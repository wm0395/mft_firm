from __future__ import annotations

import json

from project.common.models import RawDataPoint, TradeIdea


def build_filters(filters: list[tuple[str, object | None]]) -> tuple[str, list[object]]:
    clauses = [clause for clause, value in filters if value is not None]
    params = [value for _, value in filters if value is not None]
    return " and ".join(clauses) if clauses else "1=1", params


def raw_point_from_row(row: tuple) -> RawDataPoint:
    return RawDataPoint(row[0], row[1], row[2], row[3], json.loads(row[4]), row[5])


def trade_idea_from_row(row: tuple) -> TradeIdea:
    return TradeIdea(
        trade_id=row[0],
        asset_id=row[1],
        hypothesis_id=row[2],
        version=row[3],
        direction=row[4],
        confidence=row[5],
        signals_snapshot=json.loads(row[6]),
    )
