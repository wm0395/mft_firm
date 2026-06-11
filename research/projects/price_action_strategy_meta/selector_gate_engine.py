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


@dataclass(frozen=True)
class StrategyCache:
    family: str | None
    gross_return: np.ndarray
    turnover: np.ndarray
    net_return: np.ndarray


REGIME_DIMS = (
    "vol_state",
    "trend_state",
    "breadth_state",
    "gap_state",
    "liquidity_state",
    "risk_state",
    "drawdown_state",
)


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
    strategy: str,
    state_values: tuple[str, ...],
    state_keys: tuple[str, ...],
    cache: StrategyCache,
    rule_weights: dict[str, float],
    bonus: dict[str, float],
    thresholds: GateThresholds,
    net_return: float,
) -> tuple[str, str | None, float, int, float] | None:
    score = bonus.get(strategy, 0.0)
    score += family_regime_bonus(cache.family, state_values)
    matches = 0
    for key in state_keys:
        weight = rule_weights.get(key)
        if weight is not None:
            score += weight
            matches += 1
    if matches < thresholds.min_matches or score < thresholds.min_score:
        return None
    if pd.isna(net_return):
        return None
    return strategy, cache.family, score, matches, float(net_return)


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


def build_strategy_cache(frames: dict[str, pd.DataFrame]) -> dict[str, StrategyCache]:
    return {
        strategy: StrategyCache(
            family=frame.attrs.get("family") if isinstance(frame.attrs.get("family"), str) else None,
            gross_return=frame["gross_return"].to_numpy(),
            turnover=frame["turnover"].to_numpy(),
            net_return=frame["net_return"].to_numpy(),
        )
        for strategy, frame in frames.items()
    }


def regime_state_keys(state_values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        f"{dimension}:{state}" for dimension, state in zip(REGIME_DIMS, state_values)
    )


def selected_positions(frames: dict[str, pd.DataFrame], index: pd.Index) -> np.ndarray:
    positions = next(iter(frames.values())).index.get_indexer(index)
    if (positions < 0).any():
        raise ValueError("mask index is not aligned with strategy frames")
    return positions


def support_floor(state_values: tuple[str, ...], thresholds: GateThresholds) -> int:
    vol, trend, _, gap, liquidity, risk, drawdown = state_values
    hard_states = (
        vol == "high_vol",
        trend == "bear",
        gap == "up_gap_shock",
        liquidity == "low_liquidity",
        risk == "risk_off",
        drawdown == "deep_drawdown",
    )
    if any(hard_states):
        return thresholds.min_support
    return max(1, thresholds.min_support - 1)


def family_regime_bonus(family: str | None, state_values: tuple[str, ...]) -> float:
    if family is None:
        return 0.0
    vol, trend, breadth, gap, liquidity, risk, drawdown = state_values
    score = -0.5 if liquidity == "low_liquidity" else 0.0
    if family == "reversal_exhaustion":
        if vol == "high_vol":
            score += 1.5
        if trend == "bear":
            score += 1.0
        if risk == "risk_off":
            score += 1.0
        if gap in {"up_gap_shock", "down_gap_shock"}:
            score += 1.0
        if drawdown == "deep_drawdown":
            score += 1.0
        if trend == "bull" and risk == "risk_on":
            score -= 1.5
        return score
    if family == "trend_following":
        if trend == "bull" or risk == "risk_on":
            score += 1.5
        if breadth == "bullish":
            score += 0.5
        if vol == "high_vol" or trend == "bear" or risk == "risk_off" or drawdown == "deep_drawdown":
            score -= 1.5
        return score
    if family == "gap_reaction":
        return score + (1.5 if gap in {"up_gap_shock", "down_gap_shock"} else -0.5)
    if family == "volume_confirmation":
        score += 0.75 if liquidity != "low_liquidity" else -1.0
        if risk == "risk_on" or breadth == "bullish":
            score += 0.5
        if risk == "risk_off":
            score -= 0.5
        return score
    if family == "structure_levels":
        score += 0.25 if liquidity != "low_liquidity" else -0.75
        if breadth == "bullish" or trend == "bull":
            score += 0.25
        return score
    if family == "breakout_continuation":
        if trend == "bull" and risk == "risk_on":
            score += 1.0
        if vol == "high_vol" or trend == "bear" or risk == "risk_off" or drawdown == "deep_drawdown":
            score -= 1.0
        return score
    return 0.0


def select_day(
    universe: str,
    state_values: tuple[str, ...],
    state_keys: tuple[str, ...],
    strategy_cache: dict[str, StrategyCache],
    lookup: dict[str, dict[str, dict[str, float]]],
    bonus: dict[str, float],
    thresholds: GateThresholds,
    pos: int,
) -> tuple[str | None, str | None, float, int, float]:
    candidates: list[tuple[str, str | None, float, int, float]] = []
    universe_lookup = lookup.get(universe)
    if universe_lookup is None:
        return None, None, float("-inf"), 0, float("nan")
    for strategy, cache in strategy_cache.items():
        rule_weights = universe_lookup.get(strategy)
        if rule_weights is None:
            continue
        candidate = score_strategy(
            strategy,
            state_values,
            state_keys,
            cache,
            rule_weights,
            bonus,
            thresholds,
            cache.net_return[pos],
        )
        if candidate is not None:
            candidates.append(candidate)
    if len(candidates) < support_floor(state_values, thresholds):
        return None, None, float("-inf"), 0, float("nan")
    return max(candidates, key=lambda item: item[2])


def build_backtest_row(
    universe: str,
    date: pd.Timestamp,
    strategy: str | None,
    family: str | None,
    score: float,
    matches: int,
    gross_return: float,
    turnover: float,
    net_return: float,
    active: bool,
) -> dict[str, object]:
    return {
        "date": date,
        "universe": universe,
        "active": active,
        "strategy": strategy,
        "family": family,
        "score": score if active else float("nan"),
        "matches": matches if active else 0,
        "gross_return": gross_return,
        "turnover": turnover,
        "net_return": net_return if active else 0.0,
    }


def single_backtest_row(
    universe: str,
    date: pd.Timestamp,
    pos: int,
    state_values: tuple[str, ...],
    strategy_cache: dict[str, StrategyCache],
    lookup: dict[str, dict[str, dict[str, float]]],
    bonus: dict[str, float],
    thresholds: GateThresholds,
) -> dict[str, object]:
    state_keys = regime_state_keys(state_values)
    strategy, family, score, matches, net_return = select_day(
        universe,
        state_values,
        state_keys,
        strategy_cache,
        lookup,
        bonus,
        thresholds,
        pos,
    )
    active = strategy is not None
    selected = strategy_cache[strategy] if active and strategy is not None else None
    gross_return = float(selected.gross_return[pos]) if selected is not None else 0.0
    turnover = float(selected.turnover[pos]) if selected is not None else 0.0
    return build_backtest_row(
        universe,
        date,
        strategy,
        family,
        score,
        matches,
        gross_return,
        turnover,
        net_return,
        active,
    )


def universe_backtest_rows(
    universe: str,
    data: UniverseData,
    lookup: dict[str, dict[str, dict[str, float]]],
    bonus: dict[str, float],
    thresholds: GateThresholds,
    mask: pd.Series,
) -> list[dict[str, object]]:
    regime = data["regime"].loc[mask]
    strategy_cache = build_strategy_cache(data["frames"])
    positions = selected_positions(data["frames"], regime.index)
    rows: list[dict[str, object]] = []
    for pos, date, state_values in zip(
        positions,
        regime.index,
        regime[list(REGIME_DIMS)].itertuples(index=False, name=None),
    ):
        rows.append(
            single_backtest_row(
                universe,
                date,
                int(pos),
                state_values,
                strategy_cache,
                lookup,
                bonus,
                thresholds,
            )
        )
    return rows


def backtest_policy(
    universe_data: dict[str, UniverseData],
    policy: GatePolicy,
    mask: pd.Series,
) -> pd.DataFrame:
    lookup = rule_lookup(policy)
    bonus = bonus_lookup(policy)
    rows: list[dict[str, object]] = []
    for universe, data in universe_data.items():
        rows.extend(
            universe_backtest_rows(universe, data, lookup, bonus, policy.thresholds, mask)
        )
    return pd.DataFrame(rows)


def candidate_rows(
    universe_data: dict[str, UniverseData],
    summary: pd.DataFrame,
    priors: pd.DataFrame,
    train_mask: pd.Series,
    test_mask: pd.Series | None,
    include_test_metrics: bool,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for thresholds in candidate_thresholds():
        policy = build_policy(summary, priors, thresholds)
        train_frame = backtest_policy(universe_data, policy, train_mask)
        train_metrics = selection_metrics(train_frame)
        row = {
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
        }
        if include_test_metrics and test_mask is not None:
            test_frame = backtest_policy(universe_data, policy, test_mask)
            test_metrics = selection_metrics(test_frame)
            row.update(
                {
                    "test_precision": test_metrics["precision"],
                    "test_coverage": test_metrics["coverage"],
                    "test_active_days": test_metrics["active_days"],
                    "test_mean_net_bps": test_metrics["active_mean_net_bps"],
                    "test_portfolio_mean_net_bps": test_metrics["portfolio_mean_net_bps"],
                }
            )
        rows.append(row)
    candidates = pd.DataFrame(rows).sort_values(
        ["train_mean_net_bps", "train_precision", "train_active_days", "train_coverage"],
        ascending=[False, False, False, False],
    )
    return candidates[
        candidates["train_active_days"].ge(200) & candidates["train_coverage"].ge(0.02)
    ]


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
    candidates = candidate_rows(
        universe_data,
        summary,
        priors,
        train_mask,
        test_mask,
        include_test_metrics=True,
    )
    if candidates.empty:
        raise ValueError("No active gate candidates survived the threshold scan")
    chosen_name = candidates.iloc[0]["policy"]
    thresholds = next(item for item in candidate_thresholds() if item.name == chosen_name)
    chosen_policy = build_policy(summary, priors, thresholds)
    chosen_rules = pd.DataFrame([rule.__dict__ for rule in chosen_policy.rules])
    return candidates, chosen_policy, chosen_rules


def candidate_scan_train_only(
    universe_data: dict[str, UniverseData],
    summary: pd.DataFrame,
    priors: pd.DataFrame,
    train_mask: pd.Series,
) -> GatePolicy:
    candidates = candidate_rows(
        universe_data,
        summary,
        priors,
        train_mask,
        None,
        include_test_metrics=False,
    )
    if candidates.empty:
        raise ValueError("No active gate candidates survived the threshold scan")
    chosen_name = candidates.iloc[0]["policy"]
    thresholds = next(item for item in candidate_thresholds() if item.name == chosen_name)
    return build_policy(summary, priors, thresholds)
