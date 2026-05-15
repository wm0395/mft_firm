from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast

from project.common.models import Direction
from project.data.models import SignalEvaluation
from project.data.repository import DataRepository


@dataclass(frozen=True)
class ReplayConfig:
    horizons: tuple[int, ...] = (1, 5, 20)


class ReplayEngine:
    def __init__(self, repository: DataRepository, config: ReplayConfig = ReplayConfig()) -> None:
        self._repository = repository
        self._config = config

    def evaluate_signal(
        self,
        asset_symbol: str,
        timestamp: datetime,
        direction: Direction,
        hypothesis_id: str = "unknown",
    ) -> SignalEvaluation:
        normalized_timestamp = _normalize_timestamp(timestamp)
        rows = self._load_rows(asset_symbol, normalized_timestamp)
        price_map = _price_map(rows)
        sorted_timestamps = tuple(sorted(price_map))
        start_index = _start_index(sorted_timestamps, normalized_timestamp)
        returns = _forward_returns(
            sorted_timestamps,
            price_map,
            start_index,
            direction,
            self._config.horizons,
        )
        return _build_evaluation(
            asset_symbol,
            normalized_timestamp,
            direction,
            hypothesis_id,
            returns,
        )

    def _load_rows(self, asset_symbol: str, timestamp: datetime) -> tuple[tuple[object, ...], ...]:
        rows = self._repository.get_market_data(asset_symbol, timestamp, None)
        if not rows:
            raise ValueError(f"No market data found for {asset_symbol} at or after {timestamp}")
        return tuple(rows)


def _price_map(rows: tuple[tuple[object, ...], ...]) -> dict[datetime, float]:
    mapping: dict[datetime, float] = {}
    for row in rows:
        mapping[_normalize_timestamp(row[0])] = cast(float, row[4])
    return mapping


def _normalize_timestamp(value: object) -> datetime:
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if not isinstance(value, datetime):
        raise ValueError("market data timestamp must be datetime-like")
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def _start_index(timestamps: tuple[datetime, ...], target: datetime) -> int:
    normalized_target = _normalize_timestamp(target).astimezone(UTC)
    for index, item in enumerate(timestamps):
        if item.astimezone(UTC) == normalized_target:
            return index
    raise ValueError(f"Exact timestamp {target} not found in market data")


def _forward_returns(
    timestamps: tuple[datetime, ...],
    price_map: dict[datetime, float],
    start_index: int,
    direction: Direction,
    horizons: tuple[int, ...],
) -> tuple[float, ...]:
    price_now = price_map[timestamps[start_index]]
    values: list[float] = []
    for horizon in horizons:
        values.append(_forward_return(timestamps, price_map, start_index, horizon, price_now, direction))
    return tuple(values)


def _forward_return(
    timestamps: tuple[datetime, ...],
    price_map: dict[datetime, float],
    start_index: int,
    horizon: int,
    price_now: float,
    direction: Direction,
) -> float:
    future_index = start_index + horizon
    if future_index >= len(timestamps):
        return float("nan")
    price_future = price_map[timestamps[future_index]]
    value = (price_future - price_now) / price_now
    if direction == "short":
        return -value
    if direction == "flat":
        return 0.0
    return value


def _build_evaluation(
    asset_symbol: str,
    timestamp: datetime,
    direction: Direction,
    hypothesis_id: str,
    returns: tuple[float, ...],
) -> SignalEvaluation:
    return SignalEvaluation(
        signal_id=f"sig_eval:{asset_symbol}:{timestamp.isoformat()}:{direction}",
        hypothesis_id=hypothesis_id,
        forward_return_1=returns[0] if len(returns) > 0 else float("nan"),
        forward_return_5=returns[1] if len(returns) > 1 else float("nan"),
        forward_return_20=returns[2] if len(returns) > 2 else float("nan"),
        evaluation_timestamp=timestamp.astimezone(UTC).replace(microsecond=0).isoformat(),
    )
