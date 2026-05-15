from __future__ import annotations

from typing import Any, cast

from project.data.db import DuckDBAccess
from project.data.row_parsers import build_filters


class RepositoryDecisionMixin:
    _db: DuckDBAccess

    def persist_decision(self, decision: Any) -> None:
        _db(self).execute(
            """
            insert into decisions values (?, ?, ?, ?, ?, ?)
            on conflict(decision_id) do nothing
            """,
            (
                decision.decision_id,
                decision.trade_id,
                decision.action,
                decision.structured_reason,
                decision.notes,
                decision.created_at,
            ),
        )

    def get_decisions(self, trade_id: str | None = None) -> tuple[tuple, ...]:
        where_clause, params = build_filters([("trade_id = ?", trade_id)])
        return tuple(
            _db(self).fetch_all(
                f"""
            select decision_id, trade_id, action, structured_reason, notes, created_at
            from decisions
            where {where_clause}
            order by created_at, decision_id
            """,
                params,
            )
        )


def _db(repository: Any) -> DuckDBAccess:
    return cast(DuckDBAccess, repository._db)
