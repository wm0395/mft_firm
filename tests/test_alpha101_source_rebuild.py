from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any
import sys

import numpy as np
import pandas as pd  # type: ignore[import-untyped]


MODULE_PATH = Path(__file__).resolve().parents[1] / "research/notebooks/alpha_001/research/rebuild_alpha101_sources.py"
SPEC = spec_from_file_location("alpha101_source_rebuild", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
SOURCE: Any = module_from_spec(SPEC)
sys.modules[SPEC.name] = SOURCE
SPEC.loader.exec_module(SOURCE)


def test_parse_constituent_csv_builds_uppercase_symbols_and_tickers() -> None:
    text = """Company Name,Industry,Symbol,Series,ISIN Code\nAlpha Ltd,IT,alpha,EQ,INE000A01010\nBeta Ltd,Banks,beta,BE,INE000B01010\n"""
    frame = SOURCE.parse_constituent_csv(text, "https://example.com/base.csv")
    assert frame["Symbol"].tolist() == ["ALPHA"]
    assert frame["YahooTicker"].tolist() == ["ALPHA.NS"]
    assert frame["source_url"].iat[0] == "https://example.com/base.csv"


def test_build_expanded_parent_constituents_merges_source_metadata() -> None:
    base = SOURCE.parse_constituent_csv(
        "Company Name,Industry,Symbol,Series,ISIN Code\nAlpha Ltd,IT,alpha,EQ,INE000A01010\n",
        "https://example.com/base.csv",
    )
    extra = SOURCE.parse_constituent_csv(
        "Company Name,Industry,Symbol,Series,ISIN Code\nAlpha Ltd,IT,alpha,EQ,INE000A01010\nGamma Ltd,Auto,gamma,EQ,INE000G01010\n",
        "https://example.com/extra.csv",
    )
    expanded = SOURCE.build_expanded_parent_constituents(base, {"nifty_it": ("NIFTY IT", extra)})
    alpha = expanded.set_index("Symbol").loc["ALPHA"]
    assert alpha["source_indices"] == "NIFTY 500,NIFTY IT"
    assert alpha["source_slugs"] == "nifty500,nifty_it"
    assert expanded["Symbol"].tolist() == ["ALPHA", "GAMMA"]


def test_build_dynamic_high_vol_universe_selects_highest_volatility_name() -> None:
    index = pd.bdate_range("2024-01-01", periods=140)
    high = pd.Series(100.0 + np.where(np.arange(len(index)) % 2 == 0, 8.0, -8.0), index=index, name="A")
    low = pd.Series(np.linspace(100.0, 104.0, len(index)), index=index, name="B")
    adj_close = pd.DataFrame({"A": high, "B": low}, index=index)
    raw_close = adj_close.copy()
    volume = pd.DataFrame({"A": 1_000_000.0, "B": 1_000_000.0}, index=index)

    membership, report = SOURCE.build_dynamic_high_vol_universe(adj_close, raw_close, volume, basket_size=1, buffer_size=1)

    assert bool(SOURCE.weekly_reconstitution_mask(index).iloc[0])
    assert not report.empty
    assert membership.iloc[-1]["A"]
    assert not membership.iloc[-1]["B"]
    assert report["member_count"].max() == 1
    assert report["member_count"].iloc[-1] == 1
