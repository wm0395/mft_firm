from __future__ import annotations

import math
from dataclasses import dataclass, replace
from uuid import uuid4

from project.cli_support import decision_action, decision_reason, load_json
from project.common.models import HypothesisDefinition
from project.common.models import Position
from project.common.models import TradeIdea
from project.common.models import utc_now_iso
from project.data.models import HypothesisEvaluation
from project.data.repository import DataRepository
from project.decision.models import Decision
from project.decision.system import decide_trade
from project.tracking.positions import open_position


@dataclass(frozen=True)
class TradeSignalView:
    signal_type: str
    value: str


@dataclass(frozen=True)
class TradeDecisionView:
    decision_id: str
    action: str
    structured_reason: str
    notes: str
    created_at: str


@dataclass(frozen=True)
class TradeIdeaCardView:
    trade_id: str
    asset_symbol: str
    direction: str
    confidence: float
    hypothesis_id: str
    hypothesis_name: str
    decision_status: str


@dataclass(frozen=True)
class TradeIdeaDetailView:
    trade_id: str
    asset_symbol: str
    direction: str
    confidence: float
    hypothesis_id: str
    hypothesis_name: str
    hypothesis_status: str
    recommended_action: str
    recommended_reason: str
    signals: tuple[TradeSignalView, ...]
    evaluation_validation: dict[str, object] | None
    evaluation_explanation: dict[str, object] | None
    decision_history: tuple[TradeDecisionView, ...]
    approval_outcome: "ApprovalOutcomeView"


@dataclass(frozen=True)
class ApprovalOutcomeView:
    state: str
    message: str
    open_position_status: str | None
    open_position_entry_price: float | None


@dataclass(frozen=True)
class TradeIdeasPageView:
    queue: tuple[TradeIdeaCardView, ...]
    selected_detail: TradeIdeaDetailView | None
    total_trade_ideas: int
    reviewed_trade_ideas: int
    debug_payload: dict[str, object]


def get_trade_ideas_page_view(
    repository: DataRepository,
    selected_trade_id: str | None = None,
) -> TradeIdeasPageView:
    assets = {asset.asset_id: asset.symbol for asset in repository.list_assets()}
    hypotheses: dict[str, HypothesisDefinition] = {
        item.hypothesis_id: item for item in repository.get_hypotheses()
    }
    trade_ideas = repository.get_trade_ideas()
    ideas = repository.get_open_trade_ideas()
    queue = tuple(
        TradeIdeaCardView(
            trade.trade_id,
            assets.get(trade.asset_id, trade.asset_id),
            trade.direction,
            trade.confidence,
            trade.hypothesis_id,
            _hypothesis_name(hypotheses, trade.hypothesis_id),
            _decision_status(repository, trade.trade_id),
        )
        for trade in ideas
    )
    selected = _selected_trade(ideas, selected_trade_id)
    detail = (
        _detail_view(repository, selected, assets, hypotheses)
        if selected is not None
        else None
    )
    return TradeIdeasPageView(
        queue=queue,
        selected_detail=detail,
        total_trade_ideas=len(trade_ideas),
        reviewed_trade_ideas=len(trade_ideas) - len(ideas),
        debug_payload={
            "trade_ideas": [trade.__dict__ for trade in ideas],
            "all_trade_ideas": [trade.__dict__ for trade in trade_ideas],
            "decisions": [decision for decision in repository.get_decisions()],
        },
    )


def get_trade_idea_detail_view(
    repository: DataRepository,
    trade_id: str,
) -> TradeIdeaDetailView | None:
    trade_idea = next(
        (idea for idea in repository.get_trade_ideas() if idea.trade_id == trade_id),
        None,
    )
    if trade_idea is None:
        return None
    assets = {asset.asset_id: asset.symbol for asset in repository.list_assets()}
    hypotheses: dict[str, HypothesisDefinition] = {
        item.hypothesis_id: item for item in repository.get_hypotheses()
    }
    return _detail_view(repository, trade_idea, assets, hypotheses)


def submit_trade_decision(
    repository: DataRepository,
    trade_id: str,
    action: str | None = None,
    reason: str | None = None,
    notes: str = "",
) -> Decision:
    trade_idea = next(
        (idea for idea in repository.get_trade_ideas() if idea.trade_id == trade_id),
        None,
    )
    if trade_idea is None:
        msg = f"Trade idea {trade_id} not found"
        raise ValueError(msg)
    decision = _build_decision(trade_idea, action, reason, notes)
    repository.persist_decision(decision)
    _open_approval_position(repository, trade_idea, decision.action)
    return decision


def approval_position_warning(
    repository: DataRepository,
    trade_id: str,
    action: str,
) -> str | None:
    if action != "approve":
        return None
    trade_idea = _trade_idea(repository, trade_id)
    if _entry_price_from_snapshot(trade_idea.signals_snapshot) is None:
        return (
            "Approval persisted, but no usable positive entry price was found in "
            "signals_snapshot['close'], signals_snapshot['entry_price'], or "
            "signals_snapshot['price']; no position was created."
        )
    return None


def _detail_view(
    repository: DataRepository,
    trade: TradeIdea,
    assets: dict[str, str],
    hypotheses: dict[str, HypothesisDefinition],
) -> TradeIdeaDetailView:
    evaluation = _matching_evaluation(repository, trade)
    hypothesis = hypotheses.get(trade.hypothesis_id)
    decision_history = _decision_history(repository, trade.trade_id)
    recommended = decide_trade(trade)
    return TradeIdeaDetailView(
        trade_id=trade.trade_id,
        asset_symbol=assets.get(trade.asset_id, trade.asset_id),
        direction=trade.direction,
        confidence=trade.confidence,
        hypothesis_id=trade.hypothesis_id,
        hypothesis_name=(
            hypothesis.name if hypothesis is not None else trade.hypothesis_id
        ),
        hypothesis_status=hypothesis.status if hypothesis is not None else "unknown",
        recommended_action=recommended.action,
        recommended_reason=recommended.structured_reason,
        signals=tuple(
            TradeSignalView(signal_type, str(value))
            for signal_type, value in sorted(trade.signals_snapshot.items())
        ),
        evaluation_validation=(
            _json_payload(evaluation.validation_result_json)
            if evaluation is not None
            else None
        ),
        evaluation_explanation=(
            _json_payload(evaluation.explanation_json)
            if evaluation is not None
            else None
        ),
        decision_history=decision_history,
        approval_outcome=_approval_outcome(
            repository,
            trade.trade_id,
            decision_history,
        ),
    )


def _matching_evaluation(
    repository: DataRepository,
    trade: TradeIdea,
) -> HypothesisEvaluation | None:
    evaluations = repository.get_hypothesis_evaluations(
        asset_id=trade.asset_id,
        hypothesis_id=trade.hypothesis_id,
    )
    for evaluation in reversed(evaluations):
        if evaluation.direction == trade.direction:
            return evaluation
    return evaluations[-1] if evaluations else None


def _decision_status(repository: DataRepository, trade_id: str) -> str:
    decisions = repository.get_decisions(trade_id)
    return "reviewed" if decisions else "pending review"


def _selected_trade(
    ideas: tuple[TradeIdea, ...],
    selected_trade_id: str | None,
) -> TradeIdea | None:
    if selected_trade_id is not None:
        for trade in ideas:
            if trade.trade_id == selected_trade_id:
                return trade
    return ideas[0] if ideas else None


def _hypothesis_name(
    hypotheses: dict[str, HypothesisDefinition],
    hypothesis_id: str,
) -> str:
    hypothesis = hypotheses.get(hypothesis_id)
    return hypothesis.name if hypothesis is not None else hypothesis_id


def _json_payload(payload: str | None) -> dict[str, object] | None:
    return load_json(payload) if payload else None


def _decision_history(
    repository: DataRepository,
    trade_id: str,
) -> tuple[TradeDecisionView, ...]:
    decisions = repository.get_decisions(trade_id)
    return tuple(
        TradeDecisionView(
            decision_id=row[0],
            action=row[2],
            structured_reason=row[3],
            notes=row[4],
            created_at=row[5],
        )
        for row in decisions
    )


def _approval_outcome(
    repository: DataRepository,
    trade_id: str,
    decision_history: tuple[TradeDecisionView, ...],
) -> ApprovalOutcomeView:
    if not decision_history:
        return ApprovalOutcomeView("info", "No decision recorded yet.", None, None)
    if not any(item.action == "approve" for item in decision_history):
        return ApprovalOutcomeView(
            "info",
            f"Latest decision is {decision_history[-1].action}; no approval recorded.",
            None,
            None,
        )
    open_position = _open_position_for_trade(repository, trade_id)
    if open_position is not None:
        return ApprovalOutcomeView(
            "ok",
            "Approved and an open position exists for this trade.",
            open_position.status,
            open_position.entry_price,
        )
    if _has_any_position(repository, trade_id):
        return ApprovalOutcomeView(
            "warning",
            "Approved, but the matching position is closed.",
            None,
            None,
        )
    return ApprovalOutcomeView(
        "warning",
        "Approved, but no open position exists for this trade.",
        None,
        None,
    )


def _open_position_for_trade(
    repository: DataRepository,
    trade_id: str,
) -> Position | None:
    for position in repository.get_positions():
        if position.trade_id == trade_id and position.status == "open":
            return position
    return None


def _has_any_position(repository: DataRepository, trade_id: str) -> bool:
    return any(position.trade_id == trade_id for position in repository.get_positions())


def _trade_idea(repository: DataRepository, trade_id: str) -> TradeIdea:
    trade_idea = next(
        (idea for idea in repository.get_trade_ideas() if idea.trade_id == trade_id),
        None,
    )
    if trade_idea is None:
        msg = f"Trade idea {trade_id} not found"
        raise ValueError(msg)
    return trade_idea


def _open_approval_position(
    repository: DataRepository,
    trade_idea: TradeIdea,
    action: str,
) -> None:
    if action != "approve":
        return
    entry_price = _entry_price_from_snapshot(trade_idea.signals_snapshot)
    if entry_price is None:
        return
    repository.persist_position(open_position(trade_idea.trade_id, entry_price))


def _build_decision(
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


def _entry_price_from_snapshot(signals_snapshot: dict[str, float]) -> float | None:
    for field_name in ("close", "entry_price", "price"):
        value = signals_snapshot.get(field_name)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            price = float(value)
            if math.isfinite(price) and price > 0:
                return price
    return None
