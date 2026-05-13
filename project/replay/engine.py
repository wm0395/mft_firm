from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Tuple

from project.common.models import Direction
from project.data.models import SignalEvaluation
from project.data.repository import DataRepository

@dataclass(frozen=True)
class ReplayConfig:
    horizons: Tuple[int, ...] = (1, 5, 20)

class ReplayEngine:
    def __init__(self, repository: DataRepository, config: ReplayConfig = ReplayConfig()):
        self._repository = repository
        self._config = config

    def evaluate_signal(
        self, 
        asset_symbol: str, 
        timestamp: datetime, 
        direction: Direction,
        hypothesis_id: str = "unknown"
    ) -> SignalEvaluation:
        """
        Evaluates the forward returns for a signal at a given timestamp.
        """
        rows = self._repository.get_market_data(asset_symbol, timestamp, None)

        if not rows:
            raise ValueError(f"No market data found for {asset_symbol} at or after {timestamp}")
        
        # Map of timestamp to close price
        # Ensure keys are datetime objects for consistent indexing
        price_map = {}
        for row in rows:
            ts = row[0]
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts)
            price_map[ts] = row[4]
            
        sorted_timestamps = sorted(price_map.keys())
        
        try:
            # Normalize both to naive UTC for comparison
            target_utc = timestamp.astimezone(UTC).replace(tzinfo=None)
            start_idx = next(i for i, ts in enumerate(sorted_timestamps) if ts.astimezone(UTC).replace(tzinfo=None) == target_utc)
        except StopIteration:
            raise ValueError(f"Exact timestamp {timestamp} not found in market data")
            
        price_now = price_map[sorted_timestamps[start_idx]]
        
        returns = []
        for h in self._config.horizons:
            future_idx = start_idx + h
            if future_idx < len(sorted_timestamps):
                future_ts = sorted_timestamps[future_idx]
                price_future = price_map[future_ts]
                # Return = (P_future - P_now) / P_now
                ret = (price_future - price_now) / price_now
                # Adjust for direction
                if direction == "short":
                    ret = -ret
                elif direction == "flat":
                    ret = 0.0
                returns.append(ret)
            else:
                # Not enough data for this horizon
                returns.append(float('nan'))
        
        # We need a signal_id. For now, we'll generate one based on asset and timestamp.
        # In a real system, this would be passed in.
        signal_id = f"sig_eval:{asset_symbol}:{timestamp.isoformat()}:{direction}"
        
        return SignalEvaluation(
            signal_id=signal_id,
            hypothesis_id=hypothesis_id,
            forward_return_1=returns[0] if len(returns) > 0 else float('nan'),
            forward_return_5=returns[1] if len(returns) > 1 else float('nan'),
            forward_return_20=returns[2] if len(returns) > 2 else float('nan'),
            evaluation_timestamp=timestamp.astimezone(UTC).replace(microsecond=0).isoformat()
        )
