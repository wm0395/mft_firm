from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from project.cli import main
from project.common.models import TradeIdea
from project.data.db import DuckDBAccess
from project.data.repository import DataRepository
from project.tracking.positions import close_position, open_position


def test_review_trade_idea_approve_persists_decision_and_opens_position(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path = tmp_path / "mft.duckdb"
    trade = _seed_trade(
        db_path,
        trade_id="trade:approve:close",
        signals_snapshot={"close": 112.0, "entry_price": 111.0, "price": 110.0},
    )

    exit_code = main(
        [
            "review-trade-idea",
            trade.trade_id,
            "approve",
            "--database",
            str(db_path),
        ]
    )
    payload = _load_payload(capsys)

    assert exit_code == 0
    assert payload["command"] == "review-trade-idea"
    assert payload["status"] == "ok"
    assert payload["result"]["trade_id"] == trade.trade_id
    assert payload["result"]["action"] == "approve"

    repository = DataRepository(DuckDBAccess(db_path))
    try:
        assert len(repository.get_decisions(trade.trade_id)) == 1
        assert repository.get_open_trade_ideas(
            asset_id=trade.asset_id,
            hypothesis_id=trade.hypothesis_id,
        ) == ()
        assert repository.get_positions(
            asset_id=trade.asset_id,
            hypothesis_id=trade.hypothesis_id,
            status="open",
        ) == (open_position(trade.trade_id, entry_price=112.0),)
    finally:
        repository.close()


@pytest.mark.parametrize(
    ("trade_id", "signals_snapshot", "expected_entry_price"),
    [
        ("trade:approve:entry-price", {"entry_price": 111.0, "price": 110.0}, 111.0),
        ("trade:approve:price", {"price": 110.0}, 110.0),
    ],
)
def test_review_trade_idea_approve_prefers_entry_price_then_price(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    trade_id: str,
    signals_snapshot: dict[str, Any],
    expected_entry_price: float,
) -> None:
    db_path = tmp_path / "mft.duckdb"
    trade = _seed_trade(
        db_path,
        trade_id=trade_id,
        signals_snapshot=signals_snapshot,
    )

    exit_code = main(
        [
            "review-trade-idea",
            trade.trade_id,
            "approve",
            "--database",
            str(db_path),
        ]
    )
    payload = _load_payload(capsys)

    assert exit_code == 0
    assert payload["status"] == "ok"
    assert payload["result"]["action"] == "approve"

    repository = DataRepository(DuckDBAccess(db_path))
    try:
        positions = repository.get_positions(
            asset_id=trade.asset_id,
            hypothesis_id=trade.hypothesis_id,
            status="open",
        )
        assert positions == (open_position(trade.trade_id, expected_entry_price),)
    finally:
        repository.close()


@pytest.mark.parametrize(
    ("review_action", "expected_action"),
    [("reject", "reject"), ("watchlist", "watch")],
)
def test_review_trade_idea_reject_and_watch_do_not_create_positions(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    review_action: str,
    expected_action: str,
) -> None:
    db_path = tmp_path / "mft.duckdb"
    trade = _seed_trade(
        db_path,
        trade_id=f"trade:{review_action}",
        signals_snapshot={"close": 112.0},
    )

    exit_code = main(
        [
            "review-trade-idea",
            trade.trade_id,
            review_action,
            "--database",
            str(db_path),
        ]
    )
    payload = _load_payload(capsys)

    assert exit_code == 0
    assert payload["status"] == "ok"
    assert payload["result"]["action"] == expected_action

    repository = DataRepository(DuckDBAccess(db_path))
    try:
        assert len(repository.get_decisions(trade.trade_id)) == 1
        assert repository.get_positions(
            asset_id=trade.asset_id,
            hypothesis_id=trade.hypothesis_id,
            status="open",
        ) == ()
    finally:
        repository.close()


@pytest.mark.parametrize(
    ("trade_id", "signals_snapshot"),
    [
        ("trade:missing-price", {}),
        ("trade:non-positive-price", {"close": 0.0}),
        ("trade:non-numeric-price", {"close": "n/a"}),
    ],
)
def test_review_trade_idea_missing_or_invalid_price_does_not_create_position(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    trade_id: str,
    signals_snapshot: dict[str, Any],
) -> None:
    db_path = tmp_path / "mft.duckdb"
    trade = _seed_trade(
        db_path,
        trade_id=trade_id,
        signals_snapshot=signals_snapshot,
    )

    exit_code = main(
        [
            "review-trade-idea",
            trade.trade_id,
            "approve",
            "--database",
            str(db_path),
        ]
    )
    payload = _load_payload(capsys)

    assert exit_code == 0
    assert payload["status"] == "ok"
    assert payload["result"]["action"] == "approve"
    _assert_optional_price_feedback(payload)

    repository = DataRepository(DuckDBAccess(db_path))
    try:
        assert len(repository.get_decisions(trade.trade_id)) == 1
        assert repository.get_positions(
            asset_id=trade.asset_id,
            hypothesis_id=trade.hypothesis_id,
            status="open",
        ) == ()
    finally:
        repository.close()


def test_manual_position_close_lifecycle_remains_covered(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path = tmp_path / "mft.duckdb"
    trade = _seed_trade(
        db_path,
        trade_id="trade:manual-close",
        signals_snapshot={"close": 112.0},
    )

    repository = DataRepository(DuckDBAccess(db_path))
    repository.initialize()
    opened = open_position(trade.trade_id, entry_price=112.0)
    repository.persist_position(opened)
    closed = close_position(opened, exit_price=117.0)
    repository.persist_position(closed)
    assert repository.get_positions(
        asset_id=trade.asset_id,
        hypothesis_id=trade.hypothesis_id,
        status="open",
    ) == ()
    assert repository.get_positions(
        asset_id=trade.asset_id,
        hypothesis_id=trade.hypothesis_id,
        status="closed",
    ) == (closed,)
    repository.close()

    exit_code = main(
        [
            "position-management",
            "--asset-id",
            trade.asset_id,
            "--status",
            "closed",
            "--database",
            str(db_path),
        ]
    )
    payload = _load_payload(capsys)

    assert exit_code == 0
    assert payload["command"] == "position-management"
    assert payload["result"] == [closed.__dict__]


def _seed_trade(
    db_path: Path,
    *,
    trade_id: str,
    signals_snapshot: dict[str, Any],
) -> TradeIdea:
    repository = DataRepository(DuckDBAccess(db_path))
    repository.initialize()
    trade = TradeIdea(
        trade_id=trade_id,
        asset_id="asset:NIFTY",
        hypothesis_id="hypothesis:test",
        version=1,
        direction="long",
        confidence=0.9,
        signals_snapshot=cast(dict[str, float], signals_snapshot),
    )
    repository.persist_trade_idea(trade)
    repository.close()
    return trade


def _load_payload(capsys: pytest.CaptureFixture[str]) -> dict[str, Any]:
    return json.loads(capsys.readouterr().out)


def _assert_optional_price_feedback(payload: dict[str, Any]) -> None:
    warnings = payload.get("warnings", [])
    result = payload.get("result", {})
    note = ""
    if isinstance(result, dict):
        note = str(result.get("note") or result.get("notes") or "")
    feedback = " ".join(
        [
            *(warning for warning in warnings if isinstance(warning, str)),
            note,
        ]
    ).strip().lower()
    if feedback:
        assert "price" in feedback or "usable" in feedback
