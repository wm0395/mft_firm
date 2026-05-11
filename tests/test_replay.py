import pytest
from datetime import datetime, timezone, timedelta
from project.data.db import DuckDBAccess
from project.data.repository import DataRepository
from project.replay.engine import ReplayEngine

@pytest.fixture
def db_repo(tmp_path):
    db_path = tmp_path / "test_replay.duckdb"
    db = DuckDBAccess(str(db_path))
    repo = DataRepository(db)
    repo.initialize()
    return repo, db

def test_replay_engine_returns(db_repo):
    repo, db = db_repo
    asset_symbol = "AAPL"
    
    # Create dummy OHLCV data
    # t0: 100, t1: 101, t2: 102, t3: 103, t4: 104, t5: 110, t6: 111 ... t20: 120
    base_ts = datetime(2023, 1, 1, tzinfo=timezone.utc)
    data = []
    for i in range(25):
        ts = base_ts + timedelta(hours=i)
        # Price: 100 at t0, then 101, 102... then 110 at t5, then 120 at t20
        if i == 0:
            price = 100.0
        elif i == 5:
            price = 110.0
        elif i == 20:
            price = 120.0
        else:
            price = 100.0 + i
        data.append((asset_symbol, ts, price, price+1, price-1, price, 1000.0))
        
    for row in data:
        repo.ingest_market_data(*row)
        
    engine = ReplayEngine(repo)
    
    # Evaluate "long" at t0
    eval_long = engine.evaluate_signal(asset_symbol, base_ts, "long")
    
    # t1: 101. Return = (101-100)/100 = 0.01
    assert eval_long.forward_return_1 == pytest.approx(0.01)
    # t5: 110. Return = (110-100)/100 = 0.10
    assert eval_long.forward_return_5 == pytest.approx(0.10)
    # t20: 120. Return = (120-100)/100 = 0.20
    assert eval_long.forward_return_20 == pytest.approx(0.20)
    
    # Evaluate "short" at t0
    eval_short = engine.evaluate_signal(asset_symbol, base_ts, "short")
    assert eval_short.forward_return_1 == pytest.approx(-0.01)
    assert eval_short.forward_return_5 == pytest.approx(-0.10)
    assert eval_short.forward_return_20 == pytest.approx(-0.20)

def test_replay_engine_insufficient_data(db_repo):
    repo, db = db_repo
    asset_symbol = "AAPL"
    base_ts = datetime(2023, 1, 1, tzinfo=timezone.utc)
    
    # Only 3 bars of data
    for i in range(3):
        ts = base_ts + timedelta(hours=i)
        repo.ingest_market_data(asset_symbol, ts, 100.0, 101.0, 99.0, 100.0, 1000.0)
        
    engine = ReplayEngine(repo)
    eval_res = engine.evaluate_signal(asset_symbol, base_ts, "long")
    
    # t1 should be present
    assert not __import__('math').isnan(eval_res.forward_return_1)
    # t5 and t20 should be NaN
    assert __import__('math').isnan(eval_res.forward_return_5)
    assert __import__('math').isnan(eval_res.forward_return_20)
