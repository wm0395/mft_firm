from __future__ import annotations

from collections.abc import Sequence
from statistics import mean, pstdev
from typing import Any, Literal

from project.research.metrics import compute_metrics
from project.research.models import ParameterEvaluation, ParameterSet, WorkbenchSeries
from project.research.config import ResearchConfig


def simulate_parameter_set(
    config: ResearchConfig,
    series: WorkbenchSeries,
    parameter_set: ParameterSet,
) -> ParameterEvaluation:
    returns = _simulate_returns(config, series, parameter_set)
    equity_curve = _equity_curve(returns)
    return ParameterEvaluation(
        parameter_set=parameter_set,
        trade_returns_pct=returns,
        equity_curve_pct=equity_curve,
        metrics=compute_metrics(returns, equity_curve),
    )


def _simulate_returns(
    config: ResearchConfig,
    series: WorkbenchSeries,
    parameter_set: ParameterSet,
) -> tuple[float, ...]:
    if parameter_set.strategy_family == "momentum_continuation":
        return _simulate_momentum(series, _parameters(parameter_set), config.slippage_bps)
    if parameter_set.strategy_family == "mean_reversion":
        return _simulate_mean_reversion(series, _parameters(parameter_set), config.slippage_bps)
    raise ValueError(f"unsupported strategy family: {parameter_set.strategy_family}")


def _simulate_momentum(
    series: WorkbenchSeries,
    parameters: dict[str, Any],
    slippage_bps: float,
) -> tuple[float, ...]:
    closes = tuple(bar.close for bar in series.bars)
    lookback = int(parameters["lookback_bars"])
    entry_threshold = float(parameters["entry_threshold"])
    exit_threshold = float(parameters["exit_threshold"])
    holding_bars = int(parameters["holding_bars"])
    trades: list[float] = []
    open_trade: tuple[Literal["long", "short"], float, int] | None = None
    for index in range(lookback, len(closes)):
        signal = _momentum_signal(closes, index, lookback)
        open_trade, trades = _step_momentum_trade(
            open_trade,
            trades,
            closes[index],
            signal,
            holding_bars,
            index,
            exit_threshold,
            slippage_bps,
        )
        if open_trade is None:
            direction = _momentum_entry_direction(signal, entry_threshold)
            if direction is not None:
                open_trade = (direction, closes[index], index)
    return tuple(trades)


def _simulate_mean_reversion(
    series: WorkbenchSeries,
    parameters: dict[str, Any],
    slippage_bps: float,
) -> tuple[float, ...]:
    closes = tuple(bar.close for bar in series.bars)
    lookback = int(parameters["lookback_bars"])
    entry_zscore = float(parameters["entry_zscore"])
    exit_zscore = float(parameters["exit_zscore"])
    holding_bars = int(parameters["holding_bars"])
    trades: list[float] = []
    open_trade: tuple[Literal["long", "short"], float, int] | None = None
    for index in range(lookback, len(closes)):
        signal = _mean_reversion_signal(closes, index, lookback)
        open_trade, trades = _step_mean_reversion_trade(
            open_trade,
            trades,
            closes[index],
            signal,
            holding_bars,
            index,
            exit_zscore,
            slippage_bps,
        )
        if open_trade is None:
            direction = _mean_reversion_entry_direction(signal, entry_zscore)
            if direction is not None:
                open_trade = (direction, closes[index], index)
    return tuple(trades)


def _step_momentum_trade(
    open_trade: tuple[Literal["long", "short"], float, int] | None,
    trades: list[float],
    close_price: float,
    signal: float,
    holding_bars: int,
    bar_index: int,
    exit_threshold: float,
    slippage_bps: float,
) -> tuple[tuple[Literal["long", "short"], float, int] | None, list[float]]:
    if open_trade is None:
        return None, trades
    direction, entry_price, entry_index = open_trade
    held_bars = bar_index - entry_index
    if not _should_exit_momentum(direction, signal, held_bars, holding_bars, exit_threshold):
        return open_trade, trades
    trades.append(_trade_return_pct(direction, entry_price, close_price, slippage_bps))
    return None, trades


def _step_mean_reversion_trade(
    open_trade: tuple[Literal["long", "short"], float, int] | None,
    trades: list[float],
    close_price: float,
    signal: float,
    holding_bars: int,
    bar_index: int,
    exit_threshold: float,
    slippage_bps: float,
) -> tuple[tuple[Literal["long", "short"], float, int] | None, list[float]]:
    if open_trade is None:
        return None, trades
    direction, entry_price, entry_index = open_trade
    held_bars = bar_index - entry_index
    if not _should_exit_mean_reversion(
        direction,
        signal,
        held_bars,
        holding_bars,
        exit_threshold,
    ):
        return open_trade, trades
    trades.append(_trade_return_pct(direction, entry_price, close_price, slippage_bps))
    return None, trades


def _should_exit_momentum(
    direction: Literal["long", "short"],
    signal: float,
    held_bars: int,
    holding_bars: int,
    exit_threshold: float,
) -> bool:
    if held_bars >= holding_bars:
        return True
    if direction == "long":
        return signal <= exit_threshold
    return signal >= -exit_threshold


def _should_exit_mean_reversion(
    direction: Literal["long", "short"],
    signal: float,
    held_bars: int,
    holding_bars: int,
    exit_threshold: float,
) -> bool:
    if held_bars >= holding_bars:
        return True
    if direction == "long":
        return signal >= -exit_threshold
    return signal <= exit_threshold


def _trade_return_pct(
    direction: Literal["long", "short"],
    entry_price: float,
    exit_price: float,
    slippage_bps: float,
) -> float:
    gross_return = (exit_price - entry_price) / entry_price if direction == "long" else (entry_price - exit_price) / entry_price
    cost_pct = (2.0 * slippage_bps) / 100.0
    return round((gross_return * 100.0) - cost_pct, 6)


def _momentum_signal(closes: Sequence[float], index: int, lookback: int) -> float:
    past = closes[index - lookback]
    return (closes[index] / past) - 1.0


def _mean_reversion_signal(closes: Sequence[float], index: int, lookback: int) -> float:
    window = closes[index - lookback : index]
    center = mean(window)
    spread = pstdev(window)
    return 0.0 if spread == 0 else (closes[index] - center) / spread


def _momentum_entry_direction(signal: float, threshold: float) -> Literal["long", "short"] | None:
    if signal >= threshold:
        return "long"
    if signal <= -threshold:
        return "short"
    return None


def _mean_reversion_entry_direction(
    signal: float,
    threshold: float,
) -> Literal["long", "short"] | None:
    if signal <= -threshold:
        return "long"
    if signal >= threshold:
        return "short"
    return None


def _parameters(parameter_set: ParameterSet) -> dict[str, Any]:
    return {key: value for key, value in parameter_set.parameters}


def _equity_curve(returns: tuple[float, ...]) -> tuple[float, ...]:
    total = 0.0
    curve: list[float] = []
    for value in returns:
        total += value
        curve.append(total)
    return tuple(curve)
