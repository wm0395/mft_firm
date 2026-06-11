from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import pandas as pd

from project.alpha_math.validation import embargo_time_split
from project.alpha_math.validation import purged_time_split
from project.alpha_math.validation import walk_forward_split
from research.notebooks.alpha_001.research.alpha101_engine import Alpha101Panel
from research.notebooks.alpha_001.research.alpha101_engine import forward_return
from research.projects.price_action_strategy_lab.backtest_modes import BacktestConfig
from research.projects.price_action_strategy_lab.backtest_modes import summarize_backtest
from research.projects.price_action_strategy_lab.backtest_modes import run_backtest
from research.projects.price_action_strategy_lab.costs import turnover_cost
from research.projects.price_action_strategy_lab.validation_metrics import annualized_sharpe
from research.projects.price_action_strategy_lab.validation_metrics import break_even_cost_bps
from research.projects.price_action_strategy_lab.validation_metrics import hac_t_stat
from research.projects.price_action_strategy_lab.validation_metrics import max_drawdown_bps
from research.projects.price_action_strategy_lab.validation_metrics import stationary_bootstrap_bounds


@dataclass(frozen=True)
class ValidationConfig:
    enabled: bool = False
    schemes: tuple[str, ...] = ("walk_forward", "purged", "embargo")
    outer_folds: int = 6
    train_size: int = 756
    test_size: int = 63
    step_size: int | None = None
    lookahead: int = 10
    embargo: int = 10
    bootstrap_reps: int = 1000
    bootstrap_block_length: int = 10
    target_cost_bps: float = 10.0
    min_active_days: int = 40


@dataclass(frozen=True)
class SelectorHardeningConfig:
    lower_bound_margin_bps: float = 0.0
    turnover_penalty_bps: float = 25.0
    instability_penalty_bps: float = 1.0
    minimum_fold_pass_rate: float = 0.5
    abstain_lower_bound_bps: float = 0.0
    primary_scheme: str = "embargo"


@dataclass(frozen=True)
class SignalBundle:
    alpha: str
    signal: pd.DataFrame
    rank_pct: pd.DataFrame
    backend: str


@dataclass(frozen=True)
class ValidationArtifacts:
    folds: pd.DataFrame
    summary: pd.DataFrame
    selector_results: pd.DataFrame
    audit: pd.DataFrame
    embargo_diagnostics: pd.DataFrame
    decision: pd.DataFrame

    @classmethod
    def empty(cls) -> ValidationArtifacts:
        return cls(*(pd.DataFrame() for _ in range(6)))

@dataclass(frozen=True)
class ValidationFoldSpec:
    scheme: str
    fold: int
    train_index: pd.Index
    test_index: pd.Index


def run_validation_suite(
    panel: Alpha101Panel,
    bundles: tuple[SignalBundle, ...],
    result_rows: pd.DataFrame,
    config: ValidationConfig,
    hardening: SelectorHardeningConfig,
    workers: int,
) -> ValidationArtifacts:
    if not config.enabled or result_rows.empty or not bundles:
        return ValidationArtifacts.empty()
    folds = _fold_specs(panel.close.index, config)
    if not folds:
        return ValidationArtifacts.empty()
    bundle_map = {bundle.alpha: bundle for bundle in bundles}
    jobs = _validation_jobs(
        panel,
        bundle_map,
        result_rows,
        folds,
        config,
    )
    fold_rows = _run_validation_jobs(jobs, max(1, workers))
    folds_frame = pd.DataFrame(fold_rows)
    summary = _validation_summary(folds_frame, config, hardening)
    selector_results = _selector_results(summary, config, hardening)
    return ValidationArtifacts(
        folds=folds_frame,
        summary=summary,
        selector_results=selector_results,
        audit=_audit_frame(panel, bundles, config, hardening, result_rows, folds_frame),
        embargo_diagnostics=_embargo_diagnostics(summary),
        decision=_decision_frame(selector_results, summary, config, hardening),
    )


def _fold_specs(index: pd.Index, config: ValidationConfig) -> tuple[ValidationFoldSpec, ...]:
    generators = {
        "walk_forward": lambda: walk_forward_split(index, config.train_size, config.test_size, config.step_size),
        "purged": lambda: purged_time_split(index, config.train_size, config.test_size, config.lookahead, config.step_size),
        "embargo": lambda: embargo_time_split(index, config.train_size, config.test_size, config.embargo, config.step_size),
    }
    specs: list[ValidationFoldSpec] = []
    for scheme in config.schemes:
        generator = generators.get(scheme)
        if generator is None:
            raise ValueError(f"unsupported validation scheme: {scheme}")
        for fold, (train_index, test_index) in enumerate(generator()):
            if fold >= config.outer_folds:
                break
            if len(train_index) and len(test_index):
                specs.append(ValidationFoldSpec(scheme, fold, train_index, test_index))
    return tuple(specs)


def _validation_jobs(
    panel: Alpha101Panel,
    bundle_map: dict[str, SignalBundle],
    result_rows: pd.DataFrame,
    folds: tuple[ValidationFoldSpec, ...],
    config: ValidationConfig,
) -> list[
    tuple[dict[str, float | int | str], SignalBundle, ValidationFoldSpec, pd.DataFrame, ValidationConfig]
]:
    forward_map = {
        horizon: forward_return(panel.close, int(horizon)) for horizon in sorted(result_rows["horizon"].unique())
    }
    jobs: list[
        tuple[dict[str, float | int | str], SignalBundle, ValidationFoldSpec, pd.DataFrame, ValidationConfig]
    ] = []
    for row in result_rows.to_dict(orient="records"):
        bundle = bundle_map[str(row["alpha"])]
        future = forward_map[int(row["horizon"])]
        for fold in folds:
            jobs.append((row, bundle, fold, future, config))
    return jobs


def _run_validation_jobs(
    jobs: list[
        tuple[dict[str, float | int | str], SignalBundle, ValidationFoldSpec, pd.DataFrame, ValidationConfig]
    ],
    workers: int,
) -> list[dict[str, float | int | str]]:
    with ThreadPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(_run_validation_job, jobs))


def _run_validation_job(
    job: tuple[dict[str, float | int | str], SignalBundle, ValidationFoldSpec, pd.DataFrame, ValidationConfig],
) -> dict[str, float | int | str]:
    row, bundle, fold, future, config = job
    test_index = fold.test_index
    signal = bundle.signal.reindex(test_index)
    rank_pct = bundle.rank_pct.reindex(test_index)
    active_mask = signal.notna()
    bt_config = BacktestConfig(
        name=f"{row['alpha']}:{row['mode']}:{int(row['horizon'])}d:{float(row['cost_bps']):g}bps:{fold.scheme}:{fold.fold}",
        mode=str(row["mode"]),
        horizon=int(row["horizon"]),
        cost_model=turnover_cost(float(row["cost_bps"])),
        top_quantile=float(row.get("top_quantile", 0.8)),
        bottom_quantile=float(row.get("bottom_quantile", 0.2)),
        threshold=float(row.get("threshold", 0.0)),
        min_names=int(row.get("min_names", 1)),
    )
    result = run_backtest(signal, future.reindex(test_index), bt_config, active_mask, rank_pct)
    summary = summarize_backtest(result)
    net_return = result.net_return.dropna()
    lower_bps, upper_bps = stationary_bootstrap_bounds(
        net_return,
        reps=config.bootstrap_reps,
        block_length=config.bootstrap_block_length,
        seed=_job_seed(row, fold),
    )
    return {
        "scheme": fold.scheme,
        "fold": fold.fold,
        "alpha": row["alpha"],
        "mode": row["mode"],
        "horizon": int(row["horizon"]),
        "cost_bps": float(row["cost_bps"]),
        "train_days": int(len(fold.train_index)),
        "test_days": int(len(fold.test_index)),
        "train_start": str(fold.train_index[0].date()) if len(fold.train_index) else "",
        "train_end": str(fold.train_index[-1].date()) if len(fold.train_index) else "",
        "test_start": str(fold.test_index[0].date()) if len(fold.test_index) else "",
        "test_end": str(fold.test_index[-1].date()) if len(fold.test_index) else "",
        "bootstrap_low_bps": lower_bps,
        "bootstrap_high_bps": upper_bps,
        "hac_t_stat": hac_t_stat(net_return, max(int(row["horizon"]), 5)),
        "net_sharpe_like": annualized_sharpe(net_return),
        "max_drawdown_bps": max_drawdown_bps(net_return),
        "break_even_cost_bps": break_even_cost_bps(
            float(summary["gross_mean_bps"]),
            float(summary["turnover"]),
        ),
        **summary,
    }


def _validation_summary(
    folds: pd.DataFrame,
    config: ValidationConfig,
    hardening: SelectorHardeningConfig,
) -> pd.DataFrame:
    if folds.empty:
        return folds
    keys = ["scheme", "alpha", "mode", "horizon", "cost_bps"]
    grouped = folds.groupby(keys, as_index=False)
    summary = grouped.agg(
        fold_count=("fold", "nunique"),
        train_days=("train_days", "mean"),
        test_days=("test_days", "mean"),
        obs=("obs", "sum"),
        active_days=("active_days", "sum"),
        coverage=("coverage", "mean"),
        gross_mean_bps=("gross_mean_bps", "mean"),
        net_mean_bps=("net_mean_bps", "mean"),
        gross_std_bps=("gross_std_bps", "mean"),
        net_std_bps=("net_std_bps", "mean"),
        turnover=("turnover", "mean"),
        win_rate=("win_rate", "mean"),
        hit_rate=("hit_rate", "mean"),
        net_sharpe_like=("net_sharpe_like", "mean"),
        hac_t_stat=("hac_t_stat", "mean"),
        max_drawdown_bps=("max_drawdown_bps", "min"),
        lower_bps=("bootstrap_low_bps", "mean"),
        upper_bps=("bootstrap_high_bps", "mean"),
        break_even_cost_bps=("break_even_cost_bps", "mean"),
        fold_pass_rate=("net_mean_bps", lambda series: float(series.gt(0.0).mean())),
    )
    instability = folds.groupby(keys)["net_mean_bps"].std(ddof=1).reset_index(name="instability_bps")
    summary = summary.merge(instability, on=keys, how="left")
    summary["instability_bps"] = summary["instability_bps"].fillna(0.0)
    summary["selector_score"] = (
        summary["lower_bps"]
        - hardening.turnover_penalty_bps * summary["turnover"]
        - hardening.instability_penalty_bps * summary["instability_bps"]
    )
    summary["primary_scheme"] = summary["scheme"].eq(hardening.primary_scheme)
    summary["eligible"] = summary["active_days"].ge(config.min_active_days)
    summary["target_cost"] = summary["cost_bps"].round(9).eq(float(config.target_cost_bps))
    summary["cost_gap_bps"] = summary["cost_bps"] - float(config.target_cost_bps)
    return summary.sort_values(
        ["scheme", "selector_score", "lower_bps", "net_mean_bps"],
        ascending=[True, False, False, False],
    ).reset_index(drop=True)


def _selector_results(
    summary: pd.DataFrame,
    config: ValidationConfig,
    hardening: SelectorHardeningConfig,
) -> pd.DataFrame:
    if summary.empty:
        return summary
    selected = summary.loc[
        summary["scheme"].eq(hardening.primary_scheme)
        & summary["target_cost"]
        & summary["eligible"]
    ].copy()
    if selected.empty:
        selected = summary.loc[summary["scheme"].eq(hardening.primary_scheme) & summary["eligible"]].copy()
    if selected.empty:
        selected = summary.copy()
    selected = selected.sort_values(
        ["selector_score", "lower_bps", "net_mean_bps"],
        ascending=[False, False, False],
    ).reset_index(drop=True)
    selected["rank"] = selected.index + 1
    selected["abstain"] = False
    selected["reason_code"] = "ranked_by_selector_score"
    if not selected.empty:
        top = selected.iloc[0]
        runner_up = selected.iloc[1] if len(selected) > 1 else top
        if (
            float(top["lower_bps"]) <= hardening.abstain_lower_bound_bps
            or float(top["fold_pass_rate"]) < hardening.minimum_fold_pass_rate
            or float(top["selector_score"]) - float(runner_up["selector_score"]) < hardening.lower_bound_margin_bps
        ):
            selected.loc[:, "abstain"] = True
            selected.loc[:, "reason_code"] = "selector_abstain"
            selected.loc[:, "chosen_name"] = ""
            selected.loc[:, "confidence"] = 0.0
        else:
            selected.loc[:, "chosen_name"] = selected["alpha"].astype(str)
            selected.loc[:, "confidence"] = selected["lower_bps"].clip(lower=0.0) / 100.0
    return selected


def _audit_frame(
    panel: Alpha101Panel,
    bundles: tuple[SignalBundle, ...],
    config: ValidationConfig,
    hardening: SelectorHardeningConfig,
    result_rows: pd.DataFrame,
    folds: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "panel_name": panel.name,
                "alpha_count": len(bundles),
                "result_rows": len(result_rows),
                "fold_rows": len(folds),
                "schemes": ",".join(config.schemes),
                "train_size": config.train_size,
                "test_size": config.test_size,
                "step_size": config.step_size if config.step_size is not None else config.test_size,
                "lookahead": config.lookahead,
                "embargo": config.embargo,
                "outer_folds": config.outer_folds,
                "bootstrap_reps": config.bootstrap_reps,
                "bootstrap_block_length": config.bootstrap_block_length,
                "target_cost_bps": config.target_cost_bps,
                "min_active_days": config.min_active_days,
                "primary_scheme": hardening.primary_scheme,
                "turnover_penalty_bps": hardening.turnover_penalty_bps,
                "instability_penalty_bps": hardening.instability_penalty_bps,
            }
        ]
    )


def _embargo_diagnostics(summary: pd.DataFrame) -> pd.DataFrame:
    if summary.empty:
        return summary
    pivot = summary.pivot_table(
        index=["alpha", "mode", "horizon", "cost_bps"],
        columns="scheme",
        values="net_mean_bps",
        aggfunc="mean",
    )
    frame = pivot.reset_index()
    if {"walk_forward", "embargo"}.issubset(frame.columns):
        frame["embargo_delta_bps"] = frame["embargo"] - frame["walk_forward"]
    return frame


def _decision_frame(
    selector_results: pd.DataFrame,
    summary: pd.DataFrame,
    config: ValidationConfig,
    hardening: SelectorHardeningConfig,
) -> pd.DataFrame:
    if selector_results.empty:
        return selector_results
    top = selector_results.iloc[0]
    runner_up = selector_results.iloc[1] if len(selector_results) > 1 else top
    decision = "research_only"
    if not bool(top["abstain"]):
        decision = "promote" if float(top["selector_score"]) - float(runner_up["selector_score"]) >= hardening.lower_bound_margin_bps else "research_only"
    return pd.DataFrame(
        [
            {
                "decision": decision,
                "chosen_name": top.get("chosen_name", ""),
                "chosen_alpha": top.get("alpha", ""),
                "selected_scheme": top.get("scheme", ""),
                "target_cost_bps": float(config.target_cost_bps),
                "selector_score": float(top.get("selector_score", 0.0)),
                "lower_bps": float(top.get("lower_bps", 0.0)),
                "fold_pass_rate": float(top.get("fold_pass_rate", 0.0)),
                "reason_code": "selector_abstain" if bool(top["abstain"]) else "selector_margin",
                "summary_rows": len(summary),
            }
        ]
    )


def _job_seed(row: dict[str, float | int | str], fold: ValidationFoldSpec) -> int:
    payload = "|".join(
        [
            str(row["alpha"]),
            str(row["mode"]),
            str(row["horizon"]),
            str(row["cost_bps"]),
            fold.scheme,
            str(fold.fold),
        ]
    )
    return abs(hash(payload)) % (2**32)
