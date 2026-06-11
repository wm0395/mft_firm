from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPORT_DIR = Path(__file__).resolve().parent / "reports"


def max_drawdown(returns: pd.Series) -> float:
    if returns.empty:
        return float("nan")
    equity = (1.0 + returns.fillna(0.0)).cumprod()
    return float(((equity / equity.cummax()) - 1.0).min() * 100.0)


def sharpe_like(returns: pd.Series) -> float:
    values = returns.dropna()
    if len(values) < 2:
        return float("nan")
    std = float(values.std(ddof=0))
    if std == 0.0:
        return float("nan")
    return float(values.mean() / std * np.sqrt(252.0))


def cagr_pct(returns: pd.Series) -> float:
    values = returns.fillna(0.0)
    if values.empty:
        return float("nan")
    equity = float((1.0 + values).prod())
    if equity <= 0.0:
        return float("nan")
    years = len(values) / 252.0
    return float((equity ** (1.0 / years) - 1.0) * 100.0) if years > 0.0 else float("nan")


def read_frame(name: str, source: str) -> pd.DataFrame:
    frame = pd.read_csv(REPORT_DIR / name)
    frame.insert(0, "source", source)
    return frame


def write_frame(frame: pd.DataFrame, name: str) -> Path:
    path = REPORT_DIR / name
    frame.to_csv(path, index=False)
    return path


def standardize_strategy_frame(frame: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "source",
        "universe",
        "horizon",
        "family",
        "strategy",
        "description",
        "trade_days",
        "coverage_pct",
        "avg_names",
        "gross_mean_bps",
        "gross_median_bps",
        "gross_win_rate",
        "turnover",
        "gross_sharpe_like",
        "gross_max_drawdown_pct",
        "rank_ic_mean",
        "rank_ic_median",
        "rank_ic_tstat",
        "rank_ic_positive_rate",
        "net_mean_bps_0",
        "net_mean_bps_5",
        "net_mean_bps_10",
        "net_mean_bps_25",
    ]
    pack = frame.copy()
    for col in cols:
        if col not in pack.columns:
            pack[col] = np.nan
    pack["net_bps_per_turnover_10"] = pack["net_mean_bps_10"] / pack["turnover"]
    return pack[cols + ["net_bps_per_turnover_10"]]


def summarize_selected_frame(frame: pd.DataFrame, source: str, label: str) -> pd.DataFrame:
    active = frame["active"].astype(str).str.lower().eq("true")
    gross = pd.to_numeric(frame["gross_return"], errors="coerce")
    net = pd.to_numeric(frame["net_return"], errors="coerce")
    turnover = pd.to_numeric(frame["turnover"], errors="coerce")
    active_net = net[active]
    active_gross = gross[active]
    row = {
        "source": source,
        "label": label,
        "rows": int(len(frame)),
        "active_days": int(active.sum()),
        "coverage": float(active.mean()),
        "precision": float((active_net > 0.0).mean()) if len(active_net) else float("nan"),
        "active_net_mean_bps": float(active_net.mean() * 10_000.0) if len(active_net) else float("nan"),
        "portfolio_net_mean_bps": float(net.mean() * 10_000.0),
        "active_net_median_bps": float(active_net.median() * 10_000.0) if len(active_net) else float("nan"),
        "portfolio_net_median_bps": float(net.median() * 10_000.0),
        "active_gross_mean_bps": float(active_gross.mean() * 10_000.0) if len(active_gross) else float("nan"),
        "portfolio_gross_mean_bps": float(gross.mean() * 10_000.0),
        "active_gross_median_bps": float(active_gross.median() * 10_000.0) if len(active_gross) else float("nan"),
        "portfolio_gross_median_bps": float(gross.median() * 10_000.0),
        "active_turnover": float(turnover[active].mean()) if active.any() else float("nan"),
        "portfolio_turnover": float(turnover.mean()),
        "active_sharpe_like": sharpe_like(active_net),
        "portfolio_sharpe_like": sharpe_like(net),
        "portfolio_cagr_pct": cagr_pct(net),
        "portfolio_max_drawdown_pct": max_drawdown(net),
        "portfolio_net_bps_per_turnover": float(net.mean() * 10_000.0 / turnover.mean()) if turnover.mean() else float("nan"),
    }
    return pd.DataFrame([row])


def strategy_pack() -> pd.DataFrame:
    screening = standardize_strategy_frame(read_frame("screening_results.csv", "screening"))
    extra = standardize_strategy_frame(read_frame("extra_strategy_screening.csv", "extra_screening"))
    return pd.concat([screening, extra], ignore_index=True).sort_values(
        ["net_mean_bps_10", "gross_sharpe_like"], ascending=[False, False]
    )


def selector_pack() -> pd.DataFrame:
    gate_backtest = read_frame("selector_gate_backtest.csv", "gate_backtest")
    gate_selected = summarize_selected_frame(read_frame("selector_gate_selected.csv", "gate_selected"), "gate_selected", "combined")
    walk_summary = read_frame("selector_walk_forward_summary.csv", "walk_summary")
    walk_selected = summarize_selected_frame(
        read_frame("selector_walk_forward_selected.csv", "walk_selected"), "walk_selected", "combined"
    )
    return pd.concat([gate_backtest, gate_selected, walk_summary, walk_selected], ignore_index=True, sort=False)


def regime_extremes(frame: pd.DataFrame, source: str, value_col: str) -> pd.DataFrame:
    top = frame.sort_values(value_col, ascending=False).head(20).copy()
    bottom = frame.sort_values(value_col, ascending=True).head(20).copy()
    top.insert(0, "bucket", "top")
    bottom.insert(0, "bucket", "bottom")
    top.insert(0, "source", source)
    bottom.insert(0, "source", source)
    return pd.concat([top, bottom], ignore_index=True)


def regime_pack() -> pd.DataFrame:
    strategy = regime_extremes(pd.read_csv(REPORT_DIR / "regime_strategy_summary.csv"), "strategy", "mean_net_bps")
    sector = regime_extremes(pd.read_csv(REPORT_DIR / "regime_sector_summary.csv"), "sector", "mean_net_bps")
    liquidity = regime_extremes(pd.read_csv(REPORT_DIR / "regime_liquidity_summary.csv"), "liquidity", "mean_net_bps")
    return pd.concat([strategy, sector, liquidity], ignore_index=True, sort=False)


def concentration_rows(frame: pd.DataFrame, label: str) -> pd.DataFrame:
    active = frame[frame["active"].astype(str).str.lower().eq("true")].copy()
    total = len(active)
    rows = []
    for dimension, column in {
        "strategy": "strategy",
        "family": "family",
        "universe": "universe",
        "year": active["date"].str[:4],
        "month": active["date"].str[:7],
    }.items():
        counts = column.value_counts() if isinstance(column, pd.Series) else active[column].value_counts()
        for value, count in counts.items():
            rows.append(
                {
                    "selector": label,
                    "dimension": dimension,
                    "value": value,
                    "count": int(count),
                    "share": float(count / total) if total else float("nan"),
                    "active_days": total,
                }
            )
    return pd.DataFrame(rows)


def concentration_pack() -> pd.DataFrame:
    gate = concentration_rows(pd.read_csv(REPORT_DIR / "selector_gate_selected.csv"), "gate")
    walk = concentration_rows(pd.read_csv(REPORT_DIR / "selector_walk_forward_selected.csv"), "walk")
    return pd.concat([gate, walk], ignore_index=True, sort=False)


def manifest(*frames: tuple[str, pd.DataFrame]) -> pd.DataFrame:
    return pd.DataFrame(
        [{"file": name, "rows": int(len(frame)), "columns": int(len(frame.columns))} for name, frame in frames]
    )


def main() -> int:
    strategy = strategy_pack()
    selector = selector_pack()
    regime = regime_pack()
    concentration = concentration_pack()
    outputs = [
        ("metric_pack_strategies.csv", strategy),
        ("metric_pack_selector.csv", selector),
        ("metric_pack_regimes.csv", regime),
        ("metric_pack_concentration.csv", concentration),
    ]
    manifest_frame = manifest(*outputs)
    outputs.append(("metric_pack_manifest.csv", manifest_frame))
    for name, frame in outputs:
        path = write_frame(frame, name)
        print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
