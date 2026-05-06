from __future__ import annotations


def moving_average(values: tuple[float, ...], period: int) -> float:
    _validate_period(values, period)
    return sum(values[-period:]) / period


def volatility(values: tuple[float, ...], period: int) -> float:
    _validate_period(values, period + 1)
    returns = []
    window = values[-(period + 1) :]
    for previous, current in zip(window[:-1], window[1:], strict=True):
        returns.append(abs((current - previous) / previous))
    return sum(returns) / period


def rsi(values: tuple[float, ...], period: int) -> float:
    _validate_period(values, period + 1)
    gains = 0.0
    losses = 0.0
    window = values[-(period + 1) :]
    for previous, current in zip(window[:-1], window[1:], strict=True):
        delta = current - previous
        if delta >= 0:
            gains += delta
        else:
            losses += abs(delta)
    average_gain = gains / period
    average_loss = losses / period
    if average_loss == 0:
        return 100.0
    relative_strength = average_gain / average_loss
    return 100.0 - (100.0 / (1.0 + relative_strength))


def _validate_period(values: tuple[float, ...], period: int) -> None:
    if period <= 0:
        raise ValueError("period must be positive")
    if len(values) < period:
        raise ValueError("not enough values for requested period")
