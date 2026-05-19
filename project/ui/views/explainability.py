from __future__ import annotations

from dataclasses import dataclass

from project.cli_support import load_json
from project.data.repository import DataRepository


@dataclass(frozen=True)
class TraceStepView:
    label: str
    summary: str
    state: str


@dataclass(frozen=True)
class ExplainabilityDetailView:
    evaluation_id: str
    asset_symbol: str
    hypothesis_id: str
    direction: str
    confidence: float
    trace_steps: tuple[TraceStepView, ...]
    signals: dict[str, object]
    explanation: dict[str, object]
    validation: dict[str, object] | None
    trade_ideas: tuple[str, ...]
    decisions: tuple[str, ...]


@dataclass(frozen=True)
class ExplainabilityPageView:
    evaluations: tuple[str, ...]
    selected_detail: ExplainabilityDetailView | None
    debug_payload: dict[str, object]


def get_explainability_page_view(
    repository: DataRepository,
    selected_evaluation_id: str | None = None,
) -> ExplainabilityPageView:
    evaluations = repository.get_hypothesis_evaluations()
    selected = _selected_evaluation(evaluations, selected_evaluation_id)
    detail = _detail_view(repository, selected) if selected is not None else None
    return ExplainabilityPageView(
        evaluations=tuple(evaluation.evaluation_id for evaluation in evaluations),
        selected_detail=detail,
        debug_payload={"evaluations": [evaluation.__dict__ for evaluation in evaluations]},
    )


def _detail_view(repository: DataRepository, evaluation) -> ExplainabilityDetailView:
    signals = load_json(evaluation.signals_snapshot_json)
    explanation = load_json(evaluation.explanation_json)
    validation = load_json(evaluation.validation_result_json) if evaluation.validation_result_json else None
    assets = {asset.asset_id: asset.symbol for asset in repository.list_assets()}
    trade_ideas = repository.get_trade_ideas(
        asset_id=evaluation.asset_id,
        hypothesis_id=evaluation.hypothesis_id,
        direction=evaluation.direction,
    )
    trade_ids = tuple(trade.trade_id for trade in trade_ideas)
    decisions = tuple(
        decision[0]
        for trade in trade_ideas
        for decision in repository.get_decisions(trade.trade_id)
    )
    return ExplainabilityDetailView(
        evaluation_id=evaluation.evaluation_id,
        asset_symbol=assets.get(evaluation.asset_id, evaluation.asset_id),
        hypothesis_id=evaluation.hypothesis_id,
        direction=evaluation.direction,
        confidence=evaluation.confidence,
        trace_steps=_trace_steps(signals, explanation, validation, trade_ids, decisions),
        signals=signals,
        explanation=explanation,
        validation=validation,
        trade_ideas=trade_ids,
        decisions=decisions,
    )


def _trace_steps(
    signals: dict[str, object],
    explanation: dict[str, object],
    validation: dict[str, object] | None,
    trade_ids: tuple[str, ...],
    decisions: tuple[str, ...],
) -> tuple[TraceStepView, ...]:
    return (
        TraceStepView("Raw Data", "Source rows and provenance", "ok"),
        TraceStepView("Signals", f"{len(signals)} signals", "ok"),
        TraceStepView(
            "Hypothesis Evaluation",
            str(explanation.get("hypothesis_id", "")),
            "ok",
        ),
        TraceStepView(
            "Validation",
            "passed" if validation and validation.get("is_valid", False) else "failed",
            "warning" if validation else "unknown",
        ),
        TraceStepView("Trade Idea", trade_ids[0] if trade_ids else "none", "ok" if trade_ids else "unknown"),
        TraceStepView("Decision", decisions[0] if decisions else "none", "ok" if decisions else "unknown"),
    )


def _selected_evaluation(evaluations, selected_evaluation_id: str | None):
    if selected_evaluation_id is not None:
        for evaluation in evaluations:
            if evaluation.evaluation_id == selected_evaluation_id:
                return evaluation
    return evaluations[-1] if evaluations else None

