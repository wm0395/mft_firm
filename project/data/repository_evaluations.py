from __future__ import annotations

from typing import Any, cast

from project.data.db import DuckDBAccess
from project.data.models import HypothesisEvaluation, SignalEvaluation
from project.data.row_parsers import build_filters


class RepositoryEvaluationsMixin:
    _db: DuckDBAccess

    def persist_signal_evaluation(self, evaluation: SignalEvaluation) -> None:
        _db(self).execute(
            """
            insert into signal_evaluations values (?, ?, ?, ?, ?, ?)
            on conflict(signal_id) do update set
                hypothesis_id = excluded.hypothesis_id,
                forward_return_1 = excluded.forward_return_1,
                forward_return_5 = excluded.forward_return_5,
                forward_return_20 = excluded.forward_return_20,
                evaluation_timestamp = excluded.evaluation_timestamp
            """,
            (
                evaluation.signal_id,
                evaluation.hypothesis_id,
                evaluation.forward_return_1,
                evaluation.forward_return_5,
                evaluation.forward_return_20,
                evaluation.evaluation_timestamp,
            ),
        )

    def persist_hypothesis_evaluation(self, evaluation: HypothesisEvaluation) -> None:
        _db(self).execute(
            """
            insert into hypothesis_evaluations values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            on conflict(evaluation_id) do update set
                direction = excluded.direction,
                confidence = excluded.confidence,
                signals_snapshot_json = excluded.signals_snapshot_json,
                explanation_json = excluded.explanation_json,
                generated_trade_idea = excluded.generated_trade_idea,
                validation_result_json = excluded.validation_result_json,
                created_at = excluded.created_at,
                experiment_id = excluded.experiment_id,
                research_run_id = excluded.research_run_id,
                dataset_snapshot_id = excluded.dataset_snapshot_id
            """,
            (
                evaluation.evaluation_id,
                evaluation.asset_id,
                evaluation.hypothesis_id,
                evaluation.hypothesis_version,
                evaluation.timestamp,
                evaluation.direction,
                evaluation.confidence,
                evaluation.signals_snapshot_json,
                evaluation.explanation_json,
                evaluation.generated_trade_idea,
                evaluation.validation_result_json,
                evaluation.created_at,
                evaluation.experiment_id,
                evaluation.research_run_id,
                evaluation.dataset_snapshot_id,
            ),
        )

    def get_hypothesis_evaluations(
        self,
        asset_id: str | None = None,
        hypothesis_id: str | None = None,
    ) -> tuple[HypothesisEvaluation, ...]:
        where_clause, params = build_filters(
            [("asset_id = ?", asset_id), ("hypothesis_id = ?", hypothesis_id)]
        )
        rows = _db(self).fetch_all(
            f"""
            select evaluation_id, asset_id, hypothesis_id, hypothesis_version, timestamp,
                   direction, confidence, signals_snapshot_json, explanation_json,
                   generated_trade_idea, validation_result_json, created_at,
                   experiment_id, research_run_id, dataset_snapshot_id
            from hypothesis_evaluations
            where {where_clause}
            order by timestamp, evaluation_id
            """,
            params,
        )
        return tuple(HypothesisEvaluation(*row) for row in rows)


def _db(repository: Any) -> DuckDBAccess:
    return cast(DuckDBAccess, repository._db)
