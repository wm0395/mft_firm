from __future__ import annotations

from dataclasses import astuple
from typing import Any, cast

from project.common.models import HypothesisDefinition
from project.data.db import DuckDBAccess
from project.data.models import HypothesisDefinitionRecord


class RepositoryHypothesesMixin:
    _db: DuckDBAccess

    def persist_hypothesis_definition(self, definition: HypothesisDefinition) -> None:
        _db(self).execute(
            """
            insert into hypotheses values (?, ?, ?, ?, ?, ?)
            on conflict(hypothesis_id) do nothing
            """,
            astuple(HypothesisDefinitionRecord.from_artifact(definition)),
        )

    def update_hypothesis_status(
        self,
        hypothesis_id: str,
        status: str,
    ) -> None:
        _db(self).execute(
            """
            update hypotheses
            set status = ?
            where hypothesis_id = ?
            """,
            (status, hypothesis_id),
        )

    def persist_hypothesis_signal_map(
        self,
        hypothesis_id: str,
        signal_types: tuple[str, ...],
    ) -> None:
        db = _db(self)
        db.execute("delete from hypothesis_signal_map where hypothesis_id = ?", (hypothesis_id,))
        for signal_type in tuple(dict.fromkeys(signal_types)):
            db.execute(
                """
                insert into hypothesis_signal_map values (?, ?, ?)
                on conflict(hypothesis_id, signal_type) do update set
                    role = excluded.role
                """,
                (hypothesis_id, signal_type, "required"),
            )

    def get_hypotheses(self) -> tuple[HypothesisDefinition, ...]:
        rows = _db(self).fetch_all(
            """
            select hypothesis_id, name, version, definition_json,
                   explainability_level, status
            from hypotheses
            order by hypothesis_id
            """,
        )
        return tuple(HypothesisDefinitionRecord(*row).to_artifact() for row in rows)

    def get_hypothesis(self, hypothesis_id: str) -> HypothesisDefinition | None:
        rows = _db(self).fetch_all(
            """
            select hypothesis_id, name, version, definition_json,
                   explainability_level, status
            from hypotheses
            where hypothesis_id = ?
            """,
            (hypothesis_id,),
        )
        return HypothesisDefinitionRecord(*rows[0]).to_artifact() if rows else None

    def get_hypothesis_signal_map(
        self,
        hypothesis_id: str,
    ) -> tuple[tuple[str, str | None], ...]:
        rows = _db(self).fetch_all(
            """
            select signal_type, role
            from hypothesis_signal_map
            where hypothesis_id = ?
            order by signal_type
            """,
            (hypothesis_id,),
        )
        return tuple((str(row[0]), cast(str | None, row[1])) for row in rows)


def _db(repository: Any) -> DuckDBAccess:
    return cast(DuckDBAccess, repository._db)
