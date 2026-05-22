from __future__ import annotations

from pathlib import Path

from project.data_sources.common import load_json_fixture
from project.data_sources.nse.parser import parse_sample_payload

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "sample.json"


def load_sample(asset_class: str):
    payload = load_json_fixture(FIXTURE_PATH)
    fixture_text = FIXTURE_PATH.read_text(encoding="utf-8")
    return parse_sample_payload(payload, FIXTURE_PATH, fixture_text, asset_class)
