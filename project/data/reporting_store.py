from __future__ import annotations

import json
from typing import Any, cast

from project.backtesting.models import BacktestResult
from project.common.models import TradeOutcome
from project.data.db import DuckDBAccess


def persist_backtest_result(db: DuckDBAccess, result: BacktestResult) -> None:
    db.execute(
        """
        insert into backtests values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        on conflict(backtest_id) do update set
            research_run_id = excluded.research_run_id,
            strategy_spec_id = excluded.strategy_spec_id,
            dataset_snapshot_id = excluded.dataset_snapshot_id,
            hypothesis_id = excluded.hypothesis_id,
            asset_id = excluded.asset_id,
            hypothesis_version = excluded.hypothesis_version,
            start_timestamp = excluded.start_timestamp,
            end_timestamp = excluded.end_timestamp,
            parameters_json = excluded.parameters_json,
            metrics_json = excluded.metrics_json
        """,
        (
            _backtest_id(result),
            result.research_run_id,
            result.strategy_spec_id,
            result.dataset_snapshot_id,
            result.hypothesis_id,
            result.asset_id,
            result.hypothesis_version,
            result.start_timestamp,
            result.end_timestamp,
            json.dumps(dict(result.parameters), sort_keys=True),
            json.dumps(result.performance_metrics(), sort_keys=True),
        ),
    )


def load_backtest_results(db: DuckDBAccess) -> tuple[BacktestResult, ...]:
    rows = db.fetch_all(
        """
        select backtest_id, research_run_id, strategy_spec_id, dataset_snapshot_id,
               hypothesis_id, asset_id, hypothesis_version, start_timestamp,
               end_timestamp, parameters_json, metrics_json
        from backtests
        """
    )
    results = tuple(_backtest_result_from_row(row) for row in rows)
    return tuple(sorted(results, key=_backtest_sort_key))


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


def _backtest_result_from_row(row: tuple[object, ...]) -> BacktestResult:
    (
        _backtest_id,
        research_run_id,
        strategy_spec_id,
        dataset_snapshot_id,
        hypothesis_id,
        asset_id,
        hypothesis_version,
        start_timestamp,
        end_timestamp,
        parameters_json,
        metrics_json,
    ) = row
    metrics = _load_json_object(metrics_json, None)
    parameters = _parameters_tuple(parameters_json, metrics.get("parameters"))
    return BacktestResult(
        hypothesis_id=_text(hypothesis_id or metrics["hypothesis_id"]),
        asset_id=_text(asset_id or metrics["asset_id"]),
        total_trades=_metric_int(metrics, "total_trades"),
        winning_trades=_metric_int(metrics, "winning_trades"),
        win_rate=_metric_float(metrics, "win_rate"),
        total_pnl=_metric_float(metrics, "total_pnl"),
        mean_pnl=_metric_float(metrics, "mean_pnl"),
        max_drawdown=_metric_float(metrics, "max_drawdown"),
        sharpe_ratio=_metric_float(metrics, "sharpe_ratio"),
        total_return_pct=_metric_float(metrics, "total_return_pct"),
        hypothesis_version=_coerce_int(
            hypothesis_version if hypothesis_version is not None else metrics.get("hypothesis_version", 1)
        ),
        strategy_spec_id=_optional_text(strategy_spec_id or metrics.get("strategy_spec_id")),
        research_run_id=_optional_text(research_run_id or metrics.get("research_run_id")),
        dataset_snapshot_id=_optional_text(
            dataset_snapshot_id or metrics.get("dataset_snapshot_id")
        ),
        start_timestamp=_optional_text(start_timestamp or metrics.get("start_timestamp")),
        end_timestamp=_optional_text(end_timestamp or metrics.get("end_timestamp")),
        parameters=parameters,
    )


def _backtest_id(result: BacktestResult) -> str:
    if result.research_run_id:
        return f"backtest:{result.research_run_id}"
    if result.start_timestamp and result.end_timestamp:
        return (
            "backtest:"
            f"{result.hypothesis_id}:{result.asset_id}:{result.start_timestamp}:{result.end_timestamp}"
        )
    return f"backtest:{result.hypothesis_id}:{result.asset_id}"


def _backtest_sort_key(result: BacktestResult) -> tuple[str, str, str, str]:
    return (
        result.hypothesis_id,
        result.asset_id,
        result.start_timestamp or "",
        result.research_run_id or "",
    )


def _parameters_tuple(parameters_json: object, fallback: object) -> tuple[tuple[str, object], ...]:
    payload = _load_parameter_payload(parameters_json, fallback)
    return tuple(sorted(payload.items()))


def _load_json_object(value: object, fallback: object) -> dict[str, object]:
    if isinstance(value, str) and value:
        parsed = json.loads(value)
    elif isinstance(value, dict):
        parsed = value
    elif isinstance(fallback, dict):
        parsed = fallback
    else:
        parsed = {}
    if not isinstance(parsed, dict):
        return {}
    return {str(key): parsed[key] for key in parsed}


def _load_parameter_payload(value: object, fallback: object) -> dict[str, object]:
    payload = _load_json_object(value, fallback)
    if payload:
        return payload
    candidate = fallback if fallback is not None else value
    if isinstance(candidate, list):
        return {
            str(item[0]): item[1]
            for item in candidate
            if isinstance(item, (list, tuple)) and len(item) == 2
        }
    return {}


def _metric_int(metrics: dict[str, object], key: str) -> int:
    return _coerce_int(metrics[key])


def _metric_float(metrics: dict[str, object], key: str) -> float:
    return float(cast(Any, metrics[key]))


def _optional_text(value: object | None) -> str | None:
    return None if value is None else str(value)


def _text(value: object) -> str:
    return str(value)


def _coerce_int(value: object) -> int:
    return int(cast(Any, value))
