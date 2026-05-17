from __future__ import annotations

from dataclasses import dataclass

from project.research.models import ParameterEvaluation, ResearchMetrics


@dataclass(frozen=True)
class PromotionRules:
    minimum_total_trades: int = 0
    minimum_win_rate: float = 0.0
    minimum_total_return_pct: float = 0.0
    maximum_drawdown_pct: float = float("inf")
    minimum_sharpe_like_score: float = 0.0


@dataclass(frozen=True)
class PromotionCandidate:
    strategy_family: str
    parameter_set_hash: str
    metrics: ResearchMetrics


@dataclass(frozen=True)
class PromotionValidation:
    candidate: PromotionCandidate | None
    eligible: bool
    reasons: tuple[str, ...]


def candidate_from_evaluation(
    strategy_family: str,
    evaluation: ParameterEvaluation,
) -> PromotionCandidate:
    return PromotionCandidate(
        strategy_family=strategy_family,
        parameter_set_hash=evaluation.parameter_set.parameter_set_hash,
        metrics=evaluation.metrics,
    )


def validate_promotion(
    candidate: PromotionCandidate | None,
    rules: PromotionRules,
) -> PromotionValidation:
    if candidate is None:
        return PromotionValidation(candidate=None, eligible=False, reasons=("missing_candidate",))
    reasons = _promotion_reasons(candidate.metrics, rules)
    return PromotionValidation(candidate=candidate, eligible=not reasons, reasons=tuple(reasons))


def _promotion_reasons(metrics: ResearchMetrics, rules: PromotionRules) -> list[str]:
    reasons: list[str] = []
    if metrics.trade_count < rules.minimum_total_trades:
        reasons.append("insufficient_trades")
    if metrics.win_rate < rules.minimum_win_rate:
        reasons.append("win_rate_below_threshold")
    if metrics.total_return_pct < rules.minimum_total_return_pct:
        reasons.append("total_return_below_threshold")
    if metrics.max_drawdown_pct > rules.maximum_drawdown_pct:
        reasons.append("drawdown_above_threshold")
    if metrics.sharpe_like_score < rules.minimum_sharpe_like_score:
        reasons.append("sharpe_below_threshold")
    return reasons
