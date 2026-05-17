from __future__ import annotations

from dataclasses import replace
from typing import cast
from uuid import uuid4

from project.backtesting.engine import BacktestEngine
from project.backtesting.models import BacktestConfig
from project.cli_support import (
    decision_action,
    decision_reason,
    emit_error,
    emit_response,
    parse_datetime,
)
from project.common.models import (
    DecisionAction,
    DecisionReason,
    Direction,
    utc_now_iso,
)
from project.data.repository import DataRepository
from project.decision.models import Decision
from project.replay.engine import ReplayEngine


def review_trade_idea(
    repository: DataRepository,
    trade_id: str,
    action: str,
    reason: str | None,
    notes: str,
) -> int:
    trade_idea = next(
        (idea for idea in repository.get_trade_ideas() if idea.trade_id == trade_id),
        None,
    )
    if trade_idea is None:
        emit_error("review-trade-idea", f"Trade idea {trade_id} not found")
        return 1
    decision = Decision(
        decision_id=f"decision:{uuid4()}",
        trade_id=trade_id,
        action=cast(DecisionAction, decision_action(action)),
        structured_reason=cast(DecisionReason, decision_reason(reason)),
        notes=notes,
        created_at=utc_now_iso(),
    )
    repository.persist_decision(decision)
    emit_response("review-trade-idea", decision.__dict__)
    return 0


def show_trade_idea(repository: DataRepository, trade_id: str) -> int:
    trade_idea = next(
        (idea for idea in repository.get_trade_ideas() if idea.trade_id == trade_id),
        None,
    )
    if trade_idea is None:
        emit_error("show-trade-idea", f"Trade idea {trade_id} not found")
        return 1
    emit_response("show-trade-idea", trade_idea.__dict__)
    return 0


def replay_evaluate(
    repository: DataRepository,
    asset_symbol: str,
    timestamp_text: str,
    direction: str,
    hypothesis_id: str,
) -> int:
    engine = ReplayEngine(repository)
    try:
        evaluation = engine.evaluate_signal(
            asset_symbol.upper(),
            parse_datetime(timestamp_text),
            cast(Direction, direction),
            hypothesis_id,
        )
    except ValueError as error:
        emit_error("replay-evaluate", error)
        return 1
    repository.persist_signal_evaluation(evaluation)
    emit_response("replay-evaluate", evaluation.__dict__)
    return 0


def show_hypothesis_evaluations(
    repository: DataRepository,
    asset_id: str | None,
    hypothesis_id: str | None,
) -> int:
    emit_response(
        "show-hypothesis-evaluations",
        [
            evaluation.__dict__
            for evaluation in repository.get_hypothesis_evaluations(
                asset_id, hypothesis_id
            )
        ],
    )
    return 0


def backtest_hypothesis(
    repository: DataRepository,
    hypothesis_id: str,
    asset_symbol: str,
    start_date: str,
    end_date: str,
) -> int:
    engine = BacktestEngine(repository)
    try:
        result = engine.run(
            hypothesis_id,
            asset_symbol.upper(),
            parse_datetime(f"{start_date}T00:00:00+00:00"),
            parse_datetime(f"{end_date}T23:59:59+00:00"),
            BacktestConfig(),
        )
    except ValueError as error:
        emit_error("backtest-hypothesis", error)
        return 1
    enriched_result = replace(
        result,
        start_timestamp=parse_datetime(f"{start_date}T00:00:00+00:00").isoformat(),
        end_timestamp=parse_datetime(f"{end_date}T23:59:59+00:00").isoformat(),
        parameters=_config_parameters(BacktestConfig()),
    )
    repository.persist_backtest_result(enriched_result)
    emit_response("backtest-hypothesis", enriched_result.__dict__)
    return 0


def _config_parameters(config: BacktestConfig) -> tuple[tuple[str, object], ...]:
    return tuple(
        sorted(
            {
                "slippage_bps": config.slippage_bps,
                "position_size": config.position_size,
                "exit_horizon": config.exit_horizon,
            }.items()
        )
    )
