from __future__ import annotations
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from project.backtesting.models import BacktestConfig, BacktestResult, BacktestTrade
from project.data.repository import DataRepository
from project.data.models import HypothesisEvaluation

class BacktestEngine:
    def __init__(self, repository: DataRepository):
        self.repository = repository

    def run(
        self, 
        hypothesis_id: str, 
        asset_symbol: str, 
        start_timestamp: datetime, 
        end_timestamp: datetime, 
        config: BacktestConfig
    ) -> BacktestResult:
        # 1. Fetch data
        asset_id = f"asset:{asset_symbol.upper()}"
        market_data = self.repository.get_market_data(asset_symbol, start_timestamp, end_timestamp)
        evaluations = self.repository.get_hypothesis_evaluations(asset_id=asset_id, hypothesis_id=hypothesis_id)
        
        if not market_data:
            raise ValueError("No market data found for the specified range.")
        if not evaluations:
            return self._empty_result(hypothesis_id, asset_id)

        # Map evaluations by timestamp for fast lookup
        eval_map = {e.timestamp: e for e in evaluations}
        
        trades: list[BacktestTrade] = []
        active_trade: BacktestTrade | None = None
        
        # 2. Simulate
        # We iterate through bars. 
        # A signal at bar t is executed at the OPEN of bar t+1.
        for i in range(len(market_data) - 1):
            timestamp, open_p, high_p, low_p, close_p, vol = market_data[i]
            next_timestamp, next_open, _, _, _, _ = market_data[i+1]
            
            # Current evaluation for this bar
            eval_at_t = eval_map.get(timestamp)
            direction = eval_at_t.direction if eval_at_t else "flat"
            
            # Exit Logic
            if active_trade:
                should_exit = False
                
                # Condition 1: Opposite Signal
                if direction != "flat" and direction != active_trade.direction:
                    should_exit = True
                
                # Condition 2: Fixed Horizon
                if config.exit_horizon:
                    bars_held = i - active_trade.entry_bar_idx
                    if bars_held >= config.exit_horizon:
                        should_exit = True
                
                if should_exit:
                    # Exit at next open
                    exit_price = next_open
                    # Apply slippage
                    slippage = exit_price * (config.slippage_bps / 10000)
                    if active_trade.direction == "long":
                        exit_price -= slippage
                    else:
                        exit_price += slippage
                        
                    # Calculate PnL
                    pnl_pct = (exit_price - active_trade.entry_price) / active_trade.entry_price if active_trade.direction == "long" else \
                              (active_trade.entry_price - exit_price) / active_trade.entry_price
                    
                    pnl_usd = pnl_pct * config.position_size
                    
                    trades.append(BacktestTrade(
                        trade_id=f"trade:{hypothesis_id}:{active_trade.entry_timestamp}",
                        hypothesis_id=hypothesis_id,
                        asset_id=asset_id,
                        direction=active_trade.direction,
                        entry_timestamp=active_trade.entry_timestamp,
                        entry_price=active_trade.entry_price,
                        exit_timestamp=next_timestamp,
                        exit_price=exit_price,
                        pnl=pnl_usd,
                        duration=i - active_trade.entry_bar_idx
                    ))
                    active_trade = None

            # Entry Logic
            if not active_trade and direction != "flat":
                # Enter at next open
                entry_price = next_open
                # Apply slippage
                slippage = entry_price * (config.slippage_bps / 10000)
                if direction == "long":
                    entry_price += slippage
                else:
                    entry_price -= slippage
                
                # Create a temporary "active trade" tracking object
                # We use a helper class or just a dict, but for simplicity let's use a dummy Trade object
                # and store the index
                active_trade = BacktestTrade(
                    trade_id=f"trade:{hypothesis_id}:{next_timestamp}",
                    hypothesis_id=hypothesis_id,
                    asset_id=asset_id,
                    direction=direction,
                    entry_timestamp=next_timestamp,
                    entry_price=entry_price,
                    exit_timestamp=None,
                    exit_price=None,
                    pnl=None,
                    duration=None
                )
                # Monkey-patch the index for horizon tracking
                setattr(active_trade, 'entry_bar_idx', i + 1)

        return self._calculate_metrics(hypothesis_id, asset_id, trades)

    def _calculate_metrics(self, hypothesis_id: str, asset_id: str, trades: list[BacktestTrade]) -> BacktestResult:
        if not trades:
            return self._empty_result(hypothesis_id, asset_id)
            
        pnls = [t.pnl for t in trades if t.pnl is not None]
        if not pnls:
            return self._empty_result(hypothesis_id, asset_id)
            
        total_pnl = sum(pnls)
        winning_trades = len([p for p in pnls if p > 0])
        win_rate = winning_trades / len(pnls)
        mean_pnl = total_pnl / len(pnls)
        
        # Max Drawdown (simple equity curve)
        equity = 0.0
        peak = 0.0
        max_dd = 0.0
        for p in pnls:
            equity += p
            if equity > peak:
                peak = equity
            dd = peak - equity
            if dd > max_dd:
                max_dd = dd
                
        # Sharpe Ratio (approximate: mean / std)
        import statistics
        vol = statistics.stdev(pnls) if len(pnls) > 1 else 0.0
        sharpe = (mean_pnl / vol) if vol > 0 else 0.0
        
        return BacktestResult(
            hypothesis_id=hypothesis_id,
            asset_id=asset_id,
            total_trades=len(trades),
            winning_trades=winning_trades,
            win_rate=win_rate,
            total_pnl=total_pnl,
            mean_pnl=mean_pnl,
            max_drawdown=max_dd,
            sharpe_ratio=sharpe,
            total_return_pct=(total_pnl / 10000.0) * 100 # relative to fixed size
        )

    def _empty_result(self, hypothesis_id: str, asset_id: str) -> BacktestResult:
        return BacktestResult(
            hypothesis_id=hypothesis_id,
            asset_id=asset_id,
            total_trades=0,
            winning_trades=0,
            win_rate=0.0,
            total_pnl=0.0,
            mean_pnl=0.0,
            max_drawdown=0.0,
            sharpe_ratio=0.0,
            total_return_pct=0.0
        )
