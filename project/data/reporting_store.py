from __future__ import annotations

import json
from datetime import UTC, datetime

from project.backtesting.models import BacktestResult
from project.common.models import TradeOutcome
from project.data.db import DuckDBAccess


def persist_backtest_result(db: DuckDBAccess, result: BacktestResult) -> None:
    backtest_id = f"backtest:{result.hypothesis_id}:{result.asset_id}"
    metrics_json = json.dumps(
        {
            "hypothesis_id": result.hypothesis_id,
            "asset_id": result.asset_id,
            "total_trades": result.total_trades,
            "winning_trades": result.winning_trades,
            "win_rate": result.win_rate,
            "total_pnl": result.total_pnl,
            "mean_pnl": result.mean_pnl,
            "max_drawdown": result.max_drawdown,
            "sharpe_ratio": result.sharpe_ratio,
            "total_return_pct": result.total_return_pct,
            "persisted_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        },
        sort_keys=True,
    )
    db.execute(
        """
        insert into backtests values (?, ?, ?, ?, ?)
        on conflict(backtest_id) do update set
            metrics_json = excluded.metrics_json
        """,
        (backtest_id, result.hypothesis_id, result.asset_id, 1, metrics_json),
    )


def load_backtest_results(db: DuckDBAccess) -> tuple[BacktestResult, ...]:
    rows = db.fetch_all("select metrics_json from backtests order by hypothesis_id, asset_id, backtest_id")
    return tuple(_backtest_result_from_metrics(row[0]) for row in rows)


def load_trade_outcomes(db: DuckDBAccess) -> tuple[TradeOutcome, ...]:
    rows = db.fetch_all(
        """
        select p.trade_id, ti.hypothesis_id, p.pnl, ti.signals_snapshot_json
        from positions p
        join trade_ideas ti on p.trade_id = ti.trade_id
        where p.status = 'closed' and p.pnl is not null
        order by p.position_id
        """
    )
    return tuple(
        TradeOutcome(
            trade_id=row[0],
            hypothesis_id=row[1],
            pnl=row[2],
            signals_snapshot=json.loads(row[3]),
        )
        for row in rows
    )


def _backtest_result_from_metrics(metrics_json: str) -> BacktestResult:
    metrics = json.loads(metrics_json)
    return BacktestResult(
        hypothesis_id=metrics["hypothesis_id"],
        asset_id=metrics["asset_id"],
        total_trades=metrics["total_trades"],
        winning_trades=metrics["winning_trades"],
        win_rate=metrics["win_rate"],
        total_pnl=metrics["total_pnl"],
        mean_pnl=metrics["mean_pnl"],
        max_drawdown=metrics["max_drawdown"],
        sharpe_ratio=metrics["sharpe_ratio"],
        total_return_pct=metrics["total_return_pct"],
    )
