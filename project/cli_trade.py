from __future__ import annotations

import argparse
import math
from dataclasses import replace
from pathlib import Path
from collections.abc import Callable
from typing import cast
from uuid import uuid4

from project.backtesting.engine import BacktestEngine
from project.backtesting.models import BacktestConfig
from project.cli.context import open_repository
from project.cli_support import (
    decision_action,
    decision_reason,
    emit_error,
    emit_response,
    parse_datetime,
)
from project.common.models import Direction, TradeIdea, utc_now_iso
from project.data.repository import DataRepository
from project.decision.models import Decision
from project.decision.system import decide_trade
from project.replay.engine import ReplayEngine
from project.cli_operator import doctor, next_steps, workflow_status
from project.cli_registry import (
    hypothesis_readiness,
    list_hypotheses,
    promote_hypothesis,
    run_strategy_research,
    show_hypothesis,
    validate_hypothesis,
)
from project.cli_research import (
    compare_research_runs,
    create_research_project,
    export_research_pack,
    list_research_projects,
    list_research_runs,
    promote_strategy_candidate,
    run_parameter_research,
    show_research_project,
    show_research_run,
)
from project.tracking.positions import open_position


Handler = Callable[[argparse.Namespace], int]


def review_trade_idea(
    repository: DataRepository,
    trade_id: str,
    action: str | None = None,
    reason: str | None = None,
    notes: str = "",
) -> int:
    trade_idea = next(
        (idea for idea in repository.get_trade_ideas() if idea.trade_id == trade_id),
        None,
    )
    if trade_idea is None:
        emit_error("review-trade-idea", f"Trade idea {trade_id} not found")
        return 1
    decision = _review_decision(trade_idea, action, reason, notes)
    repository.persist_decision(decision)
    warnings = _approval_position_warnings(repository, trade_idea, action, decision)
    emit_response("review-trade-idea", decision.__dict__, warnings=warnings)
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


def _governance_handlers() -> dict[str, Handler]:
    return _strategy_governance_handlers() | _operator_handlers()


def _strategy_governance_handlers() -> dict[str, Handler]:
    return {
        "run-strategy-research": _repo_handler(
            "run-strategy-research",
            False,
            lambda repo, ns: run_strategy_research(
                repo,
                ns.dataset_snapshot_id,
                ns.hypothesis_id,
                ns.asset_symbol,
                ns.start_date,
                ns.end_date,
                float(ns.slippage_bps),
                float(ns.position_size),
                ns.exit_horizon,
                bool(ns.include_testing),
                bool(ns.include_draft),
            ),
        ),
        "promote-hypothesis": _repo_handler(
            "promote-hypothesis",
            False,
            lambda repo, ns: promote_hypothesis(
                repo, ns.hypothesis_id, ns.to, bool(ns.force)
            ),
        ),
        "list-hypotheses": _repo_handler(
            "list-hypotheses", True, lambda repo, ns: list_hypotheses(repo)
        ),
        "show-hypothesis": _repo_handler(
            "show-hypothesis", True, lambda repo, ns: show_hypothesis(repo, ns.hypothesis_id)
        ),
        "validate-hypothesis": _repo_handler(
            "validate-hypothesis", True, lambda repo, ns: validate_hypothesis(repo, ns.hypothesis_id)
        ),
        "hypothesis-readiness": _repo_handler(
            "hypothesis-readiness", True, lambda repo, ns: hypothesis_readiness(repo, ns.hypothesis_id)
        ),
    }


def _operator_handlers() -> dict[str, Handler]:
    return {
        "doctor": _repo_handler("doctor", True, lambda repo, ns: doctor(repo)),
        "workflow-status": _repo_handler(
            "workflow-status", True, lambda repo, ns: workflow_status(repo)
        ),
        "next-steps": _repo_handler(
            "next-steps", True, lambda repo, ns: next_steps(repo)
        ),
    }


def _research_handlers() -> dict[str, Handler]:
    return {
        "create-research-project": _repo_handler(
            "create-research-project",
            False,
            lambda repo, ns: create_research_project(repo, ns),
        ),
        "list-research-projects": _repo_handler(
            "list-research-projects", True, lambda repo, ns: list_research_projects(repo)
        ),
        "show-research-project": _repo_handler(
            "show-research-project", True, lambda repo, ns: show_research_project(repo, ns)
        ),
        "run-parameter-research": _repo_handler(
            "run-parameter-research",
            False,
            lambda repo, ns: run_parameter_research(repo, ns),
        ),
        "list-research-runs": _repo_handler(
            "list-research-runs", True, lambda repo, ns: list_research_runs(repo, ns)
        ),
        "show-research-run": _repo_handler(
            "show-research-run", True, lambda repo, ns: show_research_run(repo, ns)
        ),
        "compare-research-runs": _repo_handler(
            "compare-research-runs",
            True,
            lambda repo, ns: compare_research_runs(repo, ns),
        ),
        "export-research-pack": _repo_handler(
            "export-research-pack",
            True,
            lambda repo, ns: export_research_pack(repo, ns),
        ),
        "promote-strategy-candidate": _repo_handler(
            "promote-strategy-candidate",
            False,
            lambda repo, ns: promote_strategy_candidate(repo, ns),
        ),
    }


def _repo_handler(
    command: str,
    read_only: bool,
    runner: Callable[[DataRepository, argparse.Namespace], int],
) -> Handler:
    def handler(args: argparse.Namespace) -> int:
        return _run_repo_command(command, args, read_only, runner)

    return handler


def _run_repo_command(
    command: str,
    args: argparse.Namespace,
    read_only: bool,
    runner: Callable[[DataRepository, argparse.Namespace], int],
) -> int:
    try:
        with open_repository(Path(args.database), read_only=read_only) as repository:
            return runner(repository, args)
    except Exception as error:
        emit_error(command, error)
        return 1


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


def _review_decision(
    trade_idea: TradeIdea,
    action: str | None,
    reason: str | None,
    notes: str = "",
) -> Decision:
    if action is None and reason is None:
        return replace(decide_trade(trade_idea), notes=notes)
    if action is None:
        msg = "manual trade review requires an action"
        raise ValueError(msg)
    normalized_action = "watchlist" if action == "watch" else action
    return Decision(
        decision_id=f"decision:{uuid4()}",
        trade_id=trade_idea.trade_id,
        action=decision_action(normalized_action),
        structured_reason=decision_reason(reason),
        notes=notes,
        created_at=utc_now_iso(),
    )


def _approval_position_warnings(
    repository: DataRepository,
    trade_idea: TradeIdea,
    action: str | None,
    decision: Decision,
) -> tuple[str, ...]:
    if action != "approve" or decision.action != "approve":
        return ()
    entry_price = _entry_price_from_snapshot(trade_idea.signals_snapshot)
    if entry_price is None:
        return (
            "Approval persisted, but no usable positive entry price was found in "
            "signals_snapshot['close'], signals_snapshot['entry_price'], or "
            "signals_snapshot['price']; no position was created.",
        )
    repository.persist_position(open_position(trade_idea.trade_id, entry_price))
    return ()


def _entry_price_from_snapshot(signals_snapshot: dict[str, float]) -> float | None:
    for field_name in ("close", "entry_price", "price"):
        value = signals_snapshot.get(field_name)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            price = float(value)
            if math.isfinite(price) and price > 0:
                return price
    return None
