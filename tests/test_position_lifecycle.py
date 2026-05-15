from __future__ import annotations

import json
from pathlib import Path

import pytest

from project.cli import main
from project.common.models import TradeIdea
from project.data.db import DuckDBAccess
from project.data.loader import load_ohlcv_csv
from project.data.repository import DataRepository
from project.tracking.positions import close_position, open_position


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "market_data" / "NIFTY.csv"


def test_csv_fixture_position_lifecycle(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path = tmp_path / "mft.duckdb"
    repository = DataRepository(DuckDBAccess(db_path))
    repository.initialize()
    rows_loaded = load_ohlcv_csv(FIXTURE, "NIFTY", repository)
    trade = TradeIdea(
        trade_id="trade:fixture:nifty:ma_crossover",
        asset_id="asset:NIFTY",
        hypothesis_id="hypothesis:ma_crossover",
        version=1,
        direction="long",
        confidence=0.9,
        signals_snapshot={"close": 112.0, "ma_20": 108.0, "ma_5": 111.5},
    )
    repository.persist_trade_idea(trade)
    repository.close()

    assert rows_loaded == 25

    exit_code = main(
        [
            "review-trade-idea",
            trade.trade_id,
            "approve",
            "--database",
            str(db_path),
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "review-trade-idea"
    assert payload["status"] == "ok"
    assert payload["result"]["trade_id"] == trade.trade_id
    assert payload["result"]["action"] == "approve"

    repository = DataRepository(DuckDBAccess(db_path))
    assert repository.get_open_trade_ideas(
        asset_id=trade.asset_id,
        hypothesis_id=trade.hypothesis_id,
    ) == ()

    opened = open_position(trade.trade_id, entry_price=112.0)
    repository.persist_position(opened)
    assert repository.get_positions(
        asset_id=trade.asset_id,
        hypothesis_id=trade.hypothesis_id,
        status="open",
    ) == (opened,)

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
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload == [closed.__dict__]
