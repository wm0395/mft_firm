from __future__ import annotations

import json
from pathlib import Path

import pytest

from project.cli import main
from project.common.models import TradeIdea
from project.data.db import DuckDBAccess
from project.data.repository import DataRepository
from project.decision.system import decide_trade


def test_mutating_command_emits_structured_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "mft.duckdb"
    main(["init-db", "--database", str(db_path)])
    capsys.readouterr()

    exit_code = main(
        ["review-trade-idea", "trade:missing", "approve", "--database", str(db_path)]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "error"
    assert payload["command"] == "review-trade-idea"


def test_review_trade_idea_cli_defaults_to_shared_rules(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "mft.duckdb"
    repository, idea = _seed_review_trade_repository(db_path)

    try:
        exit_code = main(
            ["review-trade-idea", idea.trade_id, "--database", str(db_path)]
        )
        payload = json.loads(capsys.readouterr().out)
    finally:
        repository.close()

    expected = decide_trade(idea)
    assert exit_code == 0
    assert payload["status"] == "ok"
    assert payload["command"] == "review-trade-idea"
    assert payload["result"]["action"] == expected.action
    assert payload["result"]["structured_reason"] == expected.structured_reason


def test_review_trade_idea_cli_preserves_manual_inputs(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = tmp_path / "mft.duckdb"
    repository, idea = _seed_review_trade_repository(db_path)

    try:
        exit_code = main(
            [
                "review-trade-idea",
                idea.trade_id,
                "watchlist",
                "--reason",
                "market_conditions",
                "--notes",
                "manual review",
                "--database",
                str(db_path),
            ]
        )
        payload = json.loads(capsys.readouterr().out)
    finally:
        repository.close()

    assert exit_code == 0
    assert payload["status"] == "ok"
    assert payload["result"]["action"] == "watch"
    assert payload["result"]["structured_reason"] == "market_conditions"
    assert payload["result"]["notes"] == "manual review"


def _seed_review_trade_repository(db_path: Path) -> tuple[DataRepository, TradeIdea]:
    repository = DataRepository(DuckDBAccess(db_path))
    repository.initialize()
    repository.add_asset("NIFTY", "NIFTY 50", "index", "NSE")
    idea = TradeIdea(
        trade_id="trade:review:1",
        asset_id="asset:NIFTY",
        hypothesis_id="hypothesis:test",
        version=1,
        direction="long",
        confidence=0.2,
        signals_snapshot={"rsi": 25.0},
        timestamp="2026-05-21T00:00:00+00:00",
    )
    repository.persist_trade_idea(idea)
    return repository, idea
