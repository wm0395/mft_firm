from __future__ import annotations

from project.common.models import TradeOutcome


def analyze_hypothesis_performance(outcomes: tuple[TradeOutcome, ...]) -> dict[str, dict[str, float | int]]:
    grouped: dict[str, list[TradeOutcome]] = {}
    for outcome in outcomes:
        grouped.setdefault(outcome.hypothesis_id, []).append(outcome)
    return {
        hypothesis_id: {
            "trades": len(items),
            "total_pnl": round(sum(item.pnl for item in items), 6),
            "average_pnl": round(sum(item.pnl for item in items) / len(items), 6),
        }
        for hypothesis_id, items in sorted(grouped.items())
    }
