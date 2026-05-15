from __future__ import annotations

from project.common.models import Signal
from project.data.ingestion import close_prices
from project.data.repository import DataRepository
from project.signals.compute import moving_average, rsi, volatility
from project.signals.registry import SignalRegistry


def compute_latest_price_signals(
    repository: DataRepository,
    registry: SignalRegistry,
    asset_id: str,
) -> tuple[Signal, ...]:
    raw_points = repository.read_raw_values(asset_id, "price")
    prices = close_prices(raw_points)
    if not raw_points:
        return ()
    timestamp = raw_points[-1].timestamp
    raw_reference = raw_points[-1].data_id
    definitions = {
        "rsi_14": rsi(prices, 14),
        "ma_3": moving_average(prices, 3),
        "ma_5": moving_average(prices, 5),
        "ma_20": moving_average(prices, 20),
        "volatility_5": volatility(prices, 5),
        "volatility_20": volatility(prices, 20),
    }
    signals: list[Signal] = []
    for signal_type, value in definitions.items():
        definition = registry.require(signal_type)
        signals.append(
            Signal(
                signal_type=signal_type,
                value=float(value),
                encoding_type="numeric",
                timestamp=timestamp,
                asset_id=asset_id,
                raw_reference=raw_reference,
                metadata={
                    "version": definition.version,
                    "dependencies": list(definition.dependencies),
                },
                is_persistent=definition.is_persistent,
            )
        )
    return tuple(signals)
