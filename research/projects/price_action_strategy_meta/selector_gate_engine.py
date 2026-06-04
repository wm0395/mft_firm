from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from research.projects.price_action_strategy_meta.selector_types import UniverseData


@dataclass(frozen=True)
class GateThresholds:
    name: str
    min_mean_net_bps: float
    min_win_rate: float
    min_tstat: float
    min_obs: int
    min_matches: int
    min_score: float
    min_support: int


@dataclass(frozen=True)
class GateRule:
    universe: str
    strategy: str
    family: str
    dimension: str
    state: str
    mean_net_bps: float
    win_rate: float
    tstat: float
    obs: int
    weight: float


@dataclass(frozen=True)
class GatePolicy:
    thresholds: GateThresholds
    rules: tuple[GateRule, ...]
    strategy_bonus: tuple[tuple[str, float], ...]


def candidate_thresholds() -> list[GateThresholds]:
    return [
        GateThresholds("strict", 40.0, 0.55, 1.50, 250, 3, 3.00, 2),
        GateThresholds("ultra_strict_1", 45.0, 0.56, 1.75, 300, 3, 3.25, 2),
        GateThresholds("ultra_strict_2", 50.0, 0.57, 1.75, 300, 3, 3.50, 3),
        GateThresholds("ultra_strict_3", 50.0, 0.58, 2.00, 400, 4, 4.00, 3),
        GateThresholds("high_conf", 30.0, 0.54, 1.25, 100, 2, 2.50, 2),
        GateThresholds("balanced", 25.0, 0.53, 1.00, 100, 2, 2.25, 2),
        GateThresholds("loose", 20.0, 0.52, 1.00, 50, 2, 2.00, 1),
        GateThresholds("hyper_strict_1", 60.0, 0.60, 2.00, 400, 4, 4.00, 3),
        GateThresholds("hyper_strict_2", 70.0, 0.62, 2.50, 500, 4, 4.50, 4),
    ]


def score_strategy(
    universe: str,
    strategy: str,
    states: pd.Series,
    frame: pd.DataFrame,
    lookup: dict[str, dict[str, dict[str, float]]],
    bonus: dict[str, float],
    thresholds: GateThresholds,
) -> tuple[str, str | None, float, int, float] | None:
    if universe not in lookup or strategy not in lookup[universe]:
        return None
    score = bonus.get(strategy, 0.0)
    matches = 0
    for dimension in (
        "vol_state",
        "trend_state",
        "breadth_state",
        "gap_state",
        "liquidity_state",
        "risk_state",
    ):
        key = f"{dimension}:{states[dimension]}"
        weight = lookup[universe][strategy].get(key)
        if weight is not None:
            score += weight
            matches += 1
    if matches < thresholds.min_matches or score < thresholds.min_score:
        return None
    value = frame.at[states.name, "net_return"]
    if pd.isna(value):
        return None
    family = frame.attrs.get("family")
    family_name = family if isinstance(family, str) else None
    return strategy, family_name, score, matches, float(value)


def build_policy(summary: pd.DataFrame, priors: pd.DataFrame, thresholds: GateThresholds) -> GatePolicy:
    if summary.empty or priors.empty:
        return GatePolicy(thresholds=thresholds, rules=(), strategy_bonus=())
    filtered = summary[
        summary["mean_net_bps"].ge(thresholds.min_mean_net_bps)
        & summary["win_rate"].ge(thresholds.min_win_rate)
        & summary["tstat"].ge(thresholds.min_tstat)
        & summary["obs"].ge(thresholds.min_obs)
    ].copy()
    filtered = filtered.sort_values(
        ["universe", "strategy", "regime_dimension", "mean_net_bps"],
        ascending=[True, True, True, False],
    )
    filtered = filtered.groupby(
        ["universe", "strategy", "regime_dimension"],
        as_index=False,
        sort=False,
    ).head(2)
    filtered["weight"] = (
        1.0
        + filtered["mean_net_bps"].clip(lower=0.0).div(100.0)
        + filtered["tstat"].clip(lower=0.0).div(4.0)
    )
    rules = tuple(
        GateRule(
            universe=row.universe,
            strategy=row.strategy,
            family=row.family,
            dimension=row.regime_dimension,
            state=row.regime_state,
            mean_net_bps=float(row.mean_net_bps),
            win_rate=float(row.win_rate),
            tstat=float(row.tstat),
            obs=int(row.obs),
            weight=float(row.weight),
        )
        for row in filtered.itertuples(index=False)
    )
    bonus_series = priors.groupby("strategy", as_index=True)["mean_net_bps"].mean()
    strategy_bonus = tuple(
        (strategy, max(float(mean_bps), 0.0) / 50.0)
        for strategy, mean_bps in bonus_series.items()
    )
    return GatePolicy(thresholds=thresholds, rules=rules, strategy_bonus=strategy_bonus)


def rule_lookup(policy: GatePolicy) -> dict[str, dict[str, dict[str, float]]]:
    lookup: dict[str, dict[str, dict[str, float]]] = {}
    for rule in policy.rules:
        lookup.setdefault(rule.universe, {}).setdefault(rule.strategy, {})[
            f"{rule.dimension}:{rule.state}"
        ] = rule.weight
    return lookup


def bonus_lookup(policy: GatePolicy) -> dict[str, float]:
    return {strategy: bonus for strategy, bonus in policy.strategy_bonus}


def support_floor(states: pd.Series, thresholds: GateThresholds) -> int:
    hard_states = (
        states["vol_state"] == "high_vol",
        states["trend_state"] == "bear",
        states["gap_state"] == "up_gap_shock",
        states["liquidity_state"] == "low_liquidity",
        states["risk_state"] == "risk_off",
    )
    if any(hard_states):
        return thresholds.min_support
    return max(1, thresholds.min_support - 1)


def select_day(
    universe: str,
    states: pd.Series,
    frames: dict[str, pd.DataFrame],
    lookup: dict[str, dict[str, dict[str, float]]],
    bonus: dict[str, float],
    thresholds: GateThresholds,
) -> tuple[str | None, str | None, float, int, float]:
    candidates: list[tuple[str, str | None, float, int, float]] = []
    for strategy, frame in frames.items():
        candidate = score_strategy(
            universe, strategy, states, frame, lookup, bonus, thresholds
        )
        if candidate is not None:
            candidates.append(candidate)
    if len(candidates) < support_floor(states, thresholds):
        return None, None, float("-inf"), 0, float("nan")
    return max(candidates, key=lambda item: item[2])


def backtest_policy(
    universe_data: dict[str, UniverseData],
    policy: GatePolicy,
    mask: pd.Series,
) -> pd.DataFrame:
    lookup = rule_lookup(policy)
    bonus = bonus_lookup(policy)
    rows: list[dict[str, object]] = []
    for universe, data in universe_data.items():
        regime = data["regime"].loc[mask]
        frames = data["frames"]
        for date, states in regime.iterrows():
            strategy, family, score, matches, net_return = select_day(
                universe, states, frames, lookup, bonus, policy.thresholds
            )
            active = strategy is not None
            rows.append(
                {
                    "date": date,
                    "universe": universe,
                    "active": active,
                    "strategy": strategy,
                    "family": family,
                    "score": score if active else float("nan"),
                    "matches": matches if active else 0,
                    "net_return": net_return if active else 0.0,
                }
            )
    return pd.DataFrame(rows)


def selection_metrics(frame: pd.DataFrame) -> dict[str, float]:
    active = frame[frame["active"]]
    returns = frame["net_return"].fillna(0.0)
    std = float(returns.std(ddof=0))
    cumulative = (1.0 + returns).cumprod()
    peak = cumulative.cummax()
    drawdown = cumulative.div(peak).sub(1.0).min() if not cumulative.empty else 0.0
    return {
        "active_days": float(len(active)),
        "total_days": float(len(frame)),
        "coverage": float(len(active) / len(frame)) if len(frame) else 0.0,
        "precision": float(active["net_return"].gt(0.0).mean()) if not active.empty else float("nan"),
        "active_mean_net_bps": float(active["net_return"].mean() * 10_000.0)
        if not active.empty
        else float("nan"),
        "portfolio_mean_net_bps": float(returns.mean() * 10_000.0) if not returns.empty else float("nan"),
        "portfolio_median_net_bps": float(returns.median() * 10_000.0) if not returns.empty else float("nan"),
        "portfolio_sharpe_like": float(returns.mean() / std * np.sqrt(len(returns))) if std > 0.0 else float("nan"),
        "portfolio_max_drawdown_pct": float(drawdown * 100.0),
    }


def baseline_metrics(universe_data: dict[str, UniverseData], mask: pd.Series) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    combined_returns: list[pd.DataFrame] = []
    for universe, data in universe_data.items():
        frames = data["frames"]
        priors = {
            strategy: float(frame.loc[mask, "net_return"].mean() * 10_000.0)
            for strategy, frame in frames.items()
        }
        best = max(priors, key=lambda strategy: priors[strategy])
        returns = frames[best].loc[mask, "net_return"].fillna(0.0)
        combined_returns.append(
            pd.DataFrame({"universe": universe, "net_return": returns.to_numpy()})
        )
        rows.append(
            {
                "universe": universe,
                "best_always_on": best,
                "best_always_on_mean_net_bps": float(priors[best]),
                "always_flat_mean_net_bps": 0.0,
                "always_flat_precision": float("nan"),
                "test_mean_net_bps": float(returns.mean() * 10_000.0),
            }
        )
    combined = pd.concat(combined_returns, ignore_index=True)
    rows.append(
        {
            "universe": "combined",
            "best_always_on": "per-universe_best",
            "best_always_on_mean_net_bps": float(combined["net_return"].mean() * 10_000.0),
            "always_flat_mean_net_bps": 0.0,
            "always_flat_precision": float("nan"),
            "test_mean_net_bps": float(combined["net_return"].mean() * 10_000.0),
        }
    )
    return pd.DataFrame(rows)


def candidate_scan(
    universe_data: dict[str, UniverseData],
    summary: pd.DataFrame,
    priors: pd.DataFrame,
    train_mask: pd.Series,
    test_mask: pd.Series,
) -> tuple[pd.DataFrame, GatePolicy, pd.DataFrame]:
    rows: list[dict[str, object]] = []
    for thresholds in candidate_thresholds():
        policy = build_policy(summary, priors, thresholds)
        train_frame = backtest_policy(universe_data, policy, train_mask)
        test_frame = backtest_policy(universe_data, policy, test_mask)
        train_metrics = selection_metrics(train_frame)
        test_metrics = selection_metrics(test_frame)
        rows.append(
            {
                "policy": thresholds.name,
                "min_mean_net_bps": thresholds.min_mean_net_bps,
                "min_win_rate": thresholds.min_win_rate,
                "min_tstat": thresholds.min_tstat,
                "min_obs": thresholds.min_obs,
                "min_matches": thresholds.min_matches,
                "min_score": thresholds.min_score,
                "min_support": thresholds.min_support,
                "train_precision": train_metrics["precision"],
                "train_coverage": train_metrics["coverage"],
                "train_active_days": train_metrics["active_days"],
                "train_mean_net_bps": train_metrics["active_mean_net_bps"],
                "test_precision": test_metrics["precision"],
                "test_coverage": test_metrics["coverage"],
                "test_active_days": test_metrics["active_days"],
                "test_mean_net_bps": test_metrics["active_mean_net_bps"],
                "test_portfolio_mean_net_bps": test_metrics["portfolio_mean_net_bps"],
            }
        )
    candidates = pd.DataFrame(rows).sort_values(
        ["train_precision", "train_active_days", "train_coverage", "train_mean_net_bps"],
        ascending=[False, False, False, False],
    )
    candidates = candidates[candidates["train_active_days"].gt(0)]
    candidates = candidates[candidates["train_coverage"].ge(0.05)]
    if candidates.empty:
        raise ValueError("No active gate candidates survived the threshold scan")
    chosen_name = candidates.iloc[0]["policy"]
    thresholds = next(item for item in candidate_thresholds() if item.name == chosen_name)
    chosen_policy = build_policy(summary, priors, thresholds)
    chosen_rules = pd.DataFrame([rule.__dict__ for rule in chosen_policy.rules])
    return candidates, chosen_policy, chosen_rules
