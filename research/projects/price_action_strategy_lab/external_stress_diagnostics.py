from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from research.notebooks.alpha_001.research.alpha101_engine import Alpha101Panel
from research.projects.price_action_strategy_lab.activator_specs import breadth_risk_off
from research.projects.price_action_strategy_lab.run_activator_suite import _load_panel
from research.projects.price_action_strategy_lab.run_activator_suite import _read_config
from research.projects.price_action_strategy_lab.universe_adapter import to_alpha101_panel


@dataclass(frozen=True)
class StressFeatureSpec:
    name: str
    source: str
    transform: str
    lag_days: int
    available: bool


@dataclass(frozen=True)
class ExternalStressConfig:
    features: tuple[StressFeatureSpec, ...]
    report_root: Path
    source_report_dir: Path
    baseline_fold_metrics_path: Path
    max_folds: int
    weak_quantile: float
    bottom_decile_quantile: float


@dataclass(frozen=True)
class ExternalStressResult:
    report_dir: Path
    panel: pd.DataFrame
    coverage: pd.DataFrame
    separation: pd.DataFrame
    lead_lag: pd.DataFrame
    event_profiles: pd.DataFrame
    correlation: pd.DataFrame
    shortlist: pd.DataFrame


def run_external_stress_diagnostic_config(config_path: str | Path) -> ExternalStressResult:
    raw = _read_config(Path(config_path))
    panel = to_alpha101_panel(_load_panel(raw))
    result = run_external_stress_diagnostic(panel, _config(raw))
    write_external_stress_reports(result, Path(config_path))
    return result


def run_external_stress_diagnostic(panel: Alpha101Panel, config: ExternalStressConfig) -> ExternalStressResult:
    raw_features = _raw_features(panel)
    feature_panel = _lagged_feature_panel(raw_features, config.features, 1)
    folds = _baseline_folds(config)
    fold_features = _fold_feature_values(feature_panel, folds)
    separation = _separation(fold_features, _available_names(config.features))
    lead_lag = _lead_lag(raw_features, config, folds)
    coverage = _coverage(feature_panel, config.features)
    correlation = feature_panel[list(_available_names(config.features))].corr().reset_index(names="feature")
    shortlist = _shortlist(separation, coverage, correlation)
    return ExternalStressResult(
        report_dir=_report_dir(config.report_root),
        panel=feature_panel,
        coverage=coverage,
        separation=separation,
        lead_lag=lead_lag,
        event_profiles=_event_profiles(fold_features, config),
        correlation=correlation,
        shortlist=shortlist,
    )


def write_external_stress_reports(result: ExternalStressResult, registry_path: Path) -> dict[str, Path]:
    result.report_dir.mkdir(parents=True, exist_ok=True)
    paths = _paths(result.report_dir)
    registry_text = registry_path.read_text(encoding="utf-8")
    paths["registry"].write_text(registry_text, encoding="utf-8")
    result.panel.to_parquet(paths["panel"], index=False)
    result.coverage.to_csv(paths["coverage"], index=False)
    result.separation.to_csv(paths["separation"], index=False)
    result.lead_lag.to_csv(paths["lead_lag"], index=False)
    result.event_profiles.to_csv(paths["event_profiles"], index=False)
    result.correlation.to_csv(paths["correlation"], index=False)
    result.shortlist.to_csv(paths["shortlist"], index=False)
    paths["report"].write_text(_markdown(result), encoding="utf-8")
    return paths


def _config(raw: dict[str, Any]) -> ExternalStressConfig:
    compute = dict(raw.get("compute", {}))
    targets = dict(raw.get("targets", {}))
    return ExternalStressConfig(
        features=tuple(_feature(item) for item in raw.get("features", ())),
        report_root=Path(str(compute["report_root"])),
        source_report_dir=Path(str(compute["source_report_dir"])),
        baseline_fold_metrics_path=Path(str(compute["baseline_fold_metrics_path"])),
        max_folds=int(compute.get("max_folds", 24)),
        weak_quantile=float(targets.get("weak_quantile", 0.25)),
        bottom_decile_quantile=float(targets.get("bottom_decile_quantile", 0.10)),
    )


def _feature(raw: dict[str, Any]) -> StressFeatureSpec:
    return StressFeatureSpec(
        name=str(raw["name"]),
        source=str(raw["source"]),
        transform=str(raw["transform"]),
        lag_days=int(raw["lag_days"]),
        available=bool(raw["available"]),
    )


def _raw_features(panel: Alpha101Panel) -> dict[str, pd.Series]:
    close, volume = panel.close, panel.volume
    returns = close.pct_change(fill_method=None)
    equal_price = close.ffill().pct_change(fill_method=None).mean(axis=1).add(1.0).cumprod()
    traded_value = close.mul(volume).sum(axis=1, min_count=1)
    breadth = breadth_risk_off.builder(panel).mean(axis=1)
    return {
        "nifty_return_5d_lag1": equal_price.pct_change(5, fill_method=None),
        "nifty_drawdown_20d_lag1": _drawdown(equal_price, 20),
        "nifty_drawdown_60d_lag1": _drawdown(equal_price, 60),
        "sector_dispersion_5d_lag1": close.pct_change(5, fill_method=None).std(axis=1),
        "sector_dispersion_20d_lag1": close.pct_change(20, fill_method=None).std(axis=1),
        "market_traded_value_zscore_20d_lag1": _zscore(traded_value, 20),
        "advance_decline_ratio_lag1": returns.gt(0.0).sum(axis=1).div(returns.notna().sum(axis=1)),
        "advance_decline_ratio_5d_lag1": close.pct_change(5, fill_method=None).gt(0.0).sum(axis=1).div(close.notna().sum(axis=1)),
        "breadth_risk_off_lag1": breadth,
    }


def _lagged_feature_panel(raw: dict[str, pd.Series], specs: tuple[StressFeatureSpec, ...], lag: int) -> pd.DataFrame:
    index = next(iter(raw.values())).index
    data: dict[str, pd.Series] = {"date": pd.Series(index, index=index)}
    for spec in specs:
        if spec.available and spec.name in raw:
            data[spec.name] = raw[spec.name].shift(lag)
    return pd.DataFrame(data).reset_index(drop=True)


def _baseline_folds(config: ExternalStressConfig) -> pd.DataFrame:
    rows = pd.read_csv(config.baseline_fold_metrics_path)
    base = rows.loc[rows["variant"].eq("baseline")].copy()
    base = base.sort_values("fold").tail(config.max_folds)
    q25 = base["return_pct"].quantile(config.weak_quantile)
    q10 = base["return_pct"].quantile(config.bottom_decile_quantile)
    base["bottom_quartile_baseline_fold"] = base["return_pct"].le(q25)
    base["bottom_decile_baseline_fold"] = base["return_pct"].le(q10)
    return base


def _fold_feature_values(features: pd.DataFrame, folds: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    table = features.assign(date=pd.to_datetime(features["date"])).set_index("date")
    for fold in folds.to_dict("records"):
        start, end = pd.Timestamp(fold["test_start"]), pd.Timestamp(fold["test_end"])
        values = table.loc[(table.index >= start) & (table.index <= end)].mean(numeric_only=True)
        row = {key: fold[key] for key in ("fold", "test_start", "test_end", "return_pct")}
        row.update({key: bool(fold[key]) for key in ("bottom_quartile_baseline_fold", "bottom_decile_baseline_fold")})
        row.update(values.to_dict())
        rows.append(row)
    return pd.DataFrame(rows)


def _separation(folds: pd.DataFrame, names: tuple[str, ...]) -> pd.DataFrame:
    rows = [_separation_row(folds, name) for name in names if name in folds]
    return pd.DataFrame(rows).sort_values("abs_standardized_difference", ascending=False)


def _separation_row(folds: pd.DataFrame, name: str) -> dict[str, object]:
    weak = folds.loc[folds["bottom_quartile_baseline_fold"], name].dropna()
    normal = folds.loc[~folds["bottom_quartile_baseline_fold"], name].dropna()
    scores = folds[name].dropna()
    labels = folds.loc[scores.index, "bottom_quartile_baseline_fold"].astype(int)
    side = "high" if weak.mean() >= normal.mean() else "low"
    auc = _auc(labels, scores)
    return {
        "feature": name,
        "stress_side": side,
        "weak_mean": float(weak.mean()) if not weak.empty else np.nan,
        "normal_mean": float(normal.mean()) if not normal.empty else np.nan,
        "weak_median": float(weak.median()) if not weak.empty else np.nan,
        "normal_median": float(normal.median()) if not normal.empty else np.nan,
        "standardized_difference": _std_diff(weak, normal),
        "abs_standardized_difference": abs(_std_diff(weak, normal)),
        "rank_biserial": _rank_biserial(weak, normal),
        "auc": auc,
        "oriented_auc": auc if side == "high" else 1.0 - auc,
        "precision_top_decile": _precision_at_stress_decile(labels, scores, side),
        "recall_top_decile": _recall_at_stress_decile(labels, scores, side),
        "false_positive_folds": _false_positive_count(labels, scores, side),
        "false_negative_weak_folds": _false_negative_count(labels, scores, side),
    }


def _lead_lag(raw: dict[str, pd.Series], config: ExternalStressConfig, folds: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for lag in (1, 3, 5):
        panel = _lagged_feature_panel(raw, config.features, lag)
        sep = _separation(_fold_feature_values(panel, folds), _available_names(config.features))
        sep.insert(1, "lag_days", lag)
        frames.append(sep)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _coverage(panel: pd.DataFrame, specs: tuple[StressFeatureSpec, ...]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    dates = pd.to_datetime(panel["date"])
    for spec in specs:
        series = panel[spec.name] if spec.name in panel else pd.Series(dtype=float)
        if not series.empty:
            series = pd.Series(series.to_numpy(), index=dates)
        rows.append(_coverage_row(spec, series))
    return pd.DataFrame(rows)


def _coverage_row(spec: StressFeatureSpec, series: pd.Series) -> dict[str, object]:
    clean = series.dropna()
    return {
        "feature": spec.name,
        "source": spec.source,
        "available": spec.available and not clean.empty,
        "lag_days": spec.lag_days,
        "start_date": "" if clean.empty else clean.index.min(),
        "end_date": "" if clean.empty else clean.index.max(),
        "missing_pct": 1.0 if series.empty else float(series.isna().mean()),
        "stale_value_pct": _stale_pct(series),
        "alignment": "trading_calendar",
        "status": "available" if spec.available and not clean.empty else "missing_source",
    }


def _event_profiles(folds: pd.DataFrame, config: ExternalStressConfig) -> pd.DataFrame:
    labels = _event_labels(config.source_report_dir)
    frame = folds.assign(event_label=folds["fold"].map(labels).fillna("normal"))
    names = [c for c in frame.columns if c.endswith("_lag1")]
    rows: list[dict[str, object]] = []
    for label, group in frame.groupby("event_label", sort=False):
        rows.extend({"split": label, "feature": name, "mean": float(group[name].mean()), "fold_count": len(group)} for name in names)
    return pd.DataFrame(rows)


def _shortlist(separation: pd.DataFrame, coverage: pd.DataFrame, correlation: pd.DataFrame) -> pd.DataFrame:
    merged = separation.merge(coverage[["feature", "missing_pct", "status"]], on="feature", how="left")
    merged["abs_corr_to_breadth"] = merged["feature"].map(_corr_to_breadth(correlation)).fillna(0.0)
    mask = merged["status"].eq("available") & merged["missing_pct"].lt(0.40)
    mask &= merged["abs_standardized_difference"].ge(0.25) | merged["oriented_auc"].ge(0.60)
    return merged.loc[mask].sort_values(["abs_standardized_difference", "oriented_auc"], ascending=False)


def _paths(report_dir: Path) -> dict[str, Path]:
    p = "external_stress"
    return {
        "registry": report_dir / "external_stress_feature_registry.yaml",
        "panel": report_dir / "external_stress_panel.parquet",
        "coverage": report_dir / f"{p}_feature_coverage.csv",
        "separation": report_dir / f"{p}_weak_fold_separation.csv",
        "lead_lag": report_dir / f"{p}_lead_lag_diagnostics.csv",
        "event_profiles": report_dir / f"{p}_event_profiles.csv",
        "correlation": report_dir / f"{p}_feature_correlation.csv",
        "shortlist": report_dir / f"{p}_candidate_shortlist.csv",
        "report": report_dir / f"{p}_diagnostic_report.md",
    }


def _markdown(result: ExternalStressResult) -> str:
    top = result.shortlist.head(8)
    return "\n".join((
        "# External Stress Diagnostic Report",
        "",
        "Status: research-only data diagnostic. No trading gate was created.",
        "",
        "## Summary",
        f"- Available feature count: `{int(result.coverage['available'].sum())}`",
        f"- Missing feature count: `{int((~result.coverage['available']).sum())}`",
        f"- Shortlisted diagnostic features: `{len(result.shortlist)}`",
        "",
        "## Candidate Shortlist",
        _markdown_table(top) if not top.empty else "No feature passed the diagnostic shortlist filter.",
        "",
        "## Coverage",
        _markdown_table(result.coverage[["feature", "source", "available", "missing_pct", "status"]]),
        "",
        "## Interpretation",
        "External macro/flow series were not present in the local market-collector database. This run therefore validates available internal market-stress proxies and records unavailable sources explicitly.",
    ))


def _drawdown(price: pd.Series, window: int) -> pd.Series:
    return price.div(price.rolling(window, min_periods=5).max()).sub(1.0)


def _markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return ""
    cols = list(frame.columns)
    rows = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for record in frame.to_dict("records"):
        rows.append("| " + " | ".join(_cell(record[col]) for col in cols) + " |")
    return "\n".join(rows)


def _cell(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _zscore(series: pd.Series, window: int) -> pd.Series:
    return series.sub(series.rolling(window, min_periods=5).mean()).div(series.rolling(window, min_periods=5).std())


def _std_diff(left: pd.Series, right: pd.Series) -> float:
    denom = np.sqrt((left.var(ddof=0) + right.var(ddof=0)) / 2.0)
    return float((left.mean() - right.mean()) / denom) if denom and not np.isnan(denom) else 0.0


def _rank_biserial(weak: pd.Series, normal: pd.Series) -> float:
    if weak.empty or normal.empty:
        return 0.0
    wins = sum(float(w > n) + 0.5 * float(w == n) for w in weak for n in normal)
    return float((2.0 * wins / (len(weak) * len(normal))) - 1.0)


def _auc(labels: pd.Series, scores: pd.Series) -> float:
    positive, negative = scores[labels.eq(1)], scores[labels.eq(0)]
    return (_rank_biserial(positive, negative) + 1.0) / 2.0 if not positive.empty and not negative.empty else 0.5


def _precision_at_stress_decile(labels: pd.Series, scores: pd.Series, side: str) -> float:
    selected = _stress_decile_mask(scores, side)
    return float(labels[selected].mean()) if selected.any() else 0.0


def _recall_at_stress_decile(labels: pd.Series, scores: pd.Series, side: str) -> float:
    selected = _stress_decile_mask(scores, side)
    positives = labels.eq(1).sum()
    return float(labels[selected].sum() / positives) if positives else 0.0


def _false_positive_count(labels: pd.Series, scores: pd.Series, side: str) -> int:
    selected = _stress_decile_mask(scores, side)
    return int((selected & labels.eq(0)).sum())


def _false_negative_count(labels: pd.Series, scores: pd.Series, side: str) -> int:
    selected = _stress_decile_mask(scores, side)
    return int((~selected & labels.eq(1)).sum())


def _stress_decile_mask(scores: pd.Series, side: str) -> pd.Series:
    threshold = scores.quantile(0.90 if side == "high" else 0.10)
    selected = scores.ge(threshold) if side == "high" else scores.le(threshold)
    return selected.reindex(scores.index).fillna(False)


def _stale_pct(series: pd.Series) -> float:
    clean = series.dropna()
    return 1.0 if clean.empty else float(clean.eq(clean.shift(1)).mean())


def _available_names(specs: tuple[StressFeatureSpec, ...]) -> tuple[str, ...]:
    return tuple(spec.name for spec in specs if spec.available)


def _corr_to_breadth(correlation: pd.DataFrame) -> dict[str, float]:
    if "breadth_risk_off_lag1" not in correlation:
        return {}
    rows = correlation.set_index("feature")["breadth_risk_off_lag1"].abs()
    return {str(key): float(value) for key, value in rows.items()}


def _event_labels(source_dir: Path) -> pd.Series:
    path = source_dir / "weak_fold_event_attribution.csv"
    if not path.exists():
        return pd.Series(dtype=object)
    frame = pd.read_csv(path)
    return frame.groupby("fold")["event_label"].agg(lambda item: item.value_counts().index[0])


def _report_dir(root: Path) -> Path:
    return root / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
