from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from project.cli import app
from project.cli.commands import control_room as control_room_commands
from project.cli.commands import data_sources as data_source_commands


def test_research_factory_cli_surfaces_source_and_report_status(tmp_path: Path, monkeypatch) -> None:
    repo_root = _copy_research_fixture_tree(tmp_path)
    monkeypatch.setattr(data_source_commands, "_repo_root", lambda: repo_root)
    monkeypatch.setattr(control_room_commands, "_repo_root", lambda: repo_root)

    list_result = CliRunner().invoke(app, ["list-data-sources", "--json"], catch_exceptions=False)
    list_payload = json.loads(list_result.output)
    assert list_result.exit_code == 0
    assert list_payload["status"] == "ok"
    assert list_payload["result"]["source_count"] == 7

    show_result = CliRunner().invoke(app, ["show-data-source", "fred_api", "--json"], catch_exceptions=False)
    show_payload = json.loads(show_result.output)
    assert show_result.exit_code == 0
    assert show_payload["result"]["source"]["source_id"] == "fred_api"
    assert show_payload["result"]["validation"]["is_valid"]

    control_room_result = CliRunner().invoke(app, ["research-control-room", "--json"], catch_exceptions=False)
    control_room_payload = json.loads(control_room_result.output)
    assert control_room_result.exit_code == 0
    assert control_room_payload["status"] == "ok"
    assert len(control_room_payload["result"]["reports_written"]) == 5
    assert (repo_root / "research" / "reports" / "research_control_room.md").exists()

    ingest_result = CliRunner().invoke(
        app,
        [
            "ingest-source-sample",
            "nse_official_reports",
            "--asset-class",
            "indian_equity_cash",
            "--json",
        ],
        catch_exceptions=False,
    )
    ingest_payload = json.loads(ingest_result.output)
    assert ingest_result.exit_code == 0
    assert ingest_payload["status"] == "ok"
    assert ingest_payload["result"]["record_count"] == 1
    assert ingest_payload["result"]["metadata_record_count"] == 4
    assert ingest_payload["result"]["sample"]["quality_report"]["status"] == "needs_review"
    assert ingest_payload["result"]["sample"]["canonical_records"][0]["vwap"] == 2912.5

    fred_quality_result = CliRunner().invoke(
        app,
        ["data-source-quality-report", "fred_api", "--json"],
        catch_exceptions=False,
    )
    fred_quality_payload = json.loads(fred_quality_result.output)
    assert fred_quality_result.exit_code == 0
    assert fred_quality_payload["result"]["sample_asset_class"] == "macro_series"
    assert fred_quality_payload["result"]["sample_report"]["quality_report"]["status"] == "needs_review"


def _copy_research_fixture_tree(root: Path) -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    for relative_path in (
        "research/firm/daily_research_state.json",
        "research/firm/research_queue.json",
        "research/data_sources/source_registry.yaml",
        "research/asset_classes/asset_class_registry.yaml",
        "research/projects/alpha101_formulaic_alphas/research_state.json",
        "research/projects/multi_asset_expansion/project.json",
        "research/projects/multi_asset_expansion/queues/indian_etfs_queue.yaml",
        "research/projects/multi_asset_expansion/queues/mcx_queue.yaml",
        "research/projects/multi_asset_expansion/queues/macro_queue.yaml",
        "research/projects/multi_asset_expansion/queues/global_proxy_queue.yaml",
    ):
        source = repo_root / relative_path
        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return root
