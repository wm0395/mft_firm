from __future__ import annotations

from pathlib import Path

from project.research.control_room import materialize_reports


def test_materialize_reports_builds_control_room_artifacts(tmp_path: Path) -> None:
    _copy_research_fixture_tree(tmp_path)

    payloads = materialize_reports(tmp_path)
    reports_dir = tmp_path / "research" / "reports"

    assert (reports_dir / "research_control_room.md").exists()
    assert (reports_dir / "alpha101_status.md").exists()
    assert (reports_dir / "data_source_status.md").exists()
    assert (reports_dir / "multi_asset_status.md").exists()
    assert (reports_dir / "weekly_review.md").exists()
    assert payloads["alpha101_status"]["promoted_total"] == 28
    assert payloads["data_source_status"]["source_count"] == 7
    assert payloads["multi_asset_status"]["project_status"] == "draft"
    assert payloads["multi_asset_status"]["project_phase"] == "alpha101 transfer lane scaffolding"
    assert any(
        item.get("research_id") == "alpha101_mcx_continuous_transfer"
        for item in payloads["multi_asset_status"]["queues"]
    )

    control_room_markdown = (reports_dir / "research_control_room.md").read_text(encoding="utf-8")
    multi_asset_markdown = (reports_dir / "multi_asset_status.md").read_text(encoding="utf-8")
    assert "# Research Control Room" in control_room_markdown
    assert "project_id=research_project:alpha101_formulaic_alphas" in control_room_markdown
    assert "alpha_id=alpha024" in control_room_markdown
    assert "vp_research.strict_liquidity_focus_review" in control_room_markdown
    assert "project_phase: alpha101 transfer lane scaffolding" in multi_asset_markdown
    assert "alpha101_mcx_continuous_transfer" in multi_asset_markdown
    weekly_review_markdown = (reports_dir / "weekly_review.md").read_text(encoding="utf-8")
    assert "multi_asset_project_phase: alpha101 transfer lane scaffolding" in weekly_review_markdown


def _copy_research_fixture_tree(root: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    for relative_path in (
        "research/firm/daily_research_state.json",
        "research/firm/research_queue.json",
        "research/data_sources/source_registry.yaml",
        "research/asset_classes/asset_class_registry.yaml",
        "research/projects/alpha101_formulaic_alphas/research_state.json",
        "research/projects/multi_asset_expansion/project.json",
        "research/projects/multi_asset_expansion/queues/indian_etfs_queue.yaml",
        "research/projects/multi_asset_expansion/queues/nse_indices_queue.yaml",
        "research/projects/multi_asset_expansion/queues/nse_equity_derivatives_queue.yaml",
        "research/projects/multi_asset_expansion/queues/mcx_queue.yaml",
        "research/projects/multi_asset_expansion/queues/macro_queue.yaml",
        "research/projects/multi_asset_expansion/queues/global_proxy_queue.yaml",
    ):
        source = repo_root / relative_path
        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
