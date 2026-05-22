from __future__ import annotations

from dataclasses import dataclass, replace
from uuid import uuid4

from project.cli_support import decision_action, decision_reason, load_json
from project.common.models import HypothesisDefinition
from project.common.models import TradeIdea
from project.common.models import utc_now_iso
from project.data.models import HypothesisEvaluation
from project.data.repository import DataRepository
from project.decision.models import Decision
from project.decision.system import decide_trade


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
    signals: tuple[TradeSignalView, ...]
    evaluation_validation: dict[str, object] | None
    evaluation_explanation: dict[str, object] | None
    decision_history: tuple[TradeDecisionView, ...]


@dataclass(frozen=True)
class TradeIdeasPageView:
    queue: tuple[TradeIdeaCardView, ...]
    selected_detail: TradeIdeaDetailView | None
    debug_payload: dict[str, object]


def get_trade_ideas_page_view(
    repository: DataRepository,
    selected_trade_id: str | None = None,
) -> TradeIdeasPageView:
    assets = {asset.asset_id: asset.symbol for asset in repository.list_assets()}
    hypotheses: dict[str, HypothesisDefinition] = {
        item.hypothesis_id: item for item in repository.get_hypotheses()
    }
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
    detail = _detail_view(repository, selected, assets, hypotheses) if selected is not None else None
    return TradeIdeasPageView(
        queue=queue,
        selected_detail=detail,
        debug_payload={
            "trade_ideas": [trade.__dict__ for trade in ideas],
            "decisions": [decision for decision in repository.get_decisions()],
        },
    )


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
    return decision


def _detail_view(
    repository: DataRepository,
    trade: TradeIdea,
    assets: dict[str, str],
    hypotheses: dict[str, HypothesisDefinition],
) -> TradeIdeaDetailView:
    evaluation = _matching_evaluation(repository, trade)
    hypothesis = hypotheses.get(trade.hypothesis_id)
    return TradeIdeaDetailView(
        trade_id=trade.trade_id,
        asset_symbol=assets.get(trade.asset_id, trade.asset_id),
        direction=trade.direction,
        confidence=trade.confidence,
        hypothesis_id=trade.hypothesis_id,
        hypothesis_name=hypothesis.name if hypothesis is not None else trade.hypothesis_id,
        hypothesis_status=hypothesis.status if hypothesis is not None else "unknown",
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
        decision_history=_decision_history(repository, trade.trade_id),
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


def _decision_history(repository: DataRepository, trade_id: str) -> tuple[TradeDecisionView, ...]:
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
