from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any
import sys


NOTEBOOK_ROOT = Path(__file__).resolve().parents[1] / "research/notebooks/alpha_001"
if str(NOTEBOOK_ROOT) not in sys.path:
    sys.path.insert(0, str(NOTEBOOK_ROOT))

MODULE_PATH = NOTEBOOK_ROOT / "research/alpha101_strict_liquidity_batch_runner.py"
SPEC = spec_from_file_location("alpha101_strict_liquidity_batch_runner_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE: Any = module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_resolve_shortlist_prefers_positive_focus(tmp_path: Path, monkeypatch: Any) -> None:
    positive = tmp_path / "alpha101_strict_liquidity_positive_focus.csv"
    shortlist = tmp_path / "promoted_exact_shortlist_filled.csv"
    positive.write_text("alpha_id\nalpha024\n")
    shortlist.write_text("alpha_id\nalpha040\n")
    monkeypatch.setattr(MODULE, "POSITIVE_FOCUS_PATH", positive)
    monkeypatch.setattr(MODULE, "SHORTLIST_PATH", shortlist)

    assert MODULE.resolve_shortlist_path() == positive


def test_resolve_shortlist_falls_back_to_promoted_shortlist(tmp_path: Path, monkeypatch: Any) -> None:
    positive = tmp_path / "alpha101_strict_liquidity_positive_focus.csv"
    shortlist = tmp_path / "promoted_exact_shortlist_filled.csv"
    shortlist.write_text("alpha_id\nalpha040\n")
    monkeypatch.setattr(MODULE, "POSITIVE_FOCUS_PATH", positive)
    monkeypatch.setattr(MODULE, "SHORTLIST_PATH", shortlist)

    assert MODULE.resolve_shortlist_path() == shortlist
