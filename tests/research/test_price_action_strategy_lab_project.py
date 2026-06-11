from __future__ import annotations

import json
from pathlib import Path


def test_price_action_strategy_lab_project_scaffold() -> None:
    root = Path(__file__).resolve().parents[2] / "research" / "projects" / "price_action_strategy_lab"

    project = json.loads((root / "project.json").read_text(encoding="utf-8"))
    state = json.loads((root / "research_state.json").read_text(encoding="utf-8"))
    readme = (root / "README.md").read_text(encoding="utf-8")
    universe = (root / "configs" / "universe.yaml").read_text(encoding="utf-8")
    lab_run = (root / "configs" / "lab_run.yaml").read_text(encoding="utf-8")
    reports = (root / "reports" / "README.md").read_text(encoding="utf-8")
    review_packs = (root / "review_packs" / "README.md").read_text(encoding="utf-8")

    assert project["research_project_id"] == "research_project:price_action_strategy_lab"
    assert project["status"] == "draft"
    assert project["phase"] == "first_runnable_lab_spine"
    assert project["review_pack_dir"] == "review_packs"
    assert state["project_id"] == "research_project:price_action_strategy_lab"
    assert state["project_status"] == "draft"
    assert state["phase"] == "first_runnable_lab_spine"
    assert state["summary_artifacts"] == [
        "research/projects/price_action_strategy_lab/README.md",
        "research/projects/price_action_strategy_lab/configs/universe.yaml",
        "research/projects/price_action_strategy_lab/configs/lab_run.yaml",
        "project/data/market_collector_panel.py",
        "research/projects/price_action_strategy_lab/universe_adapter.py",
        "research/projects/price_action_strategy_lab/alpha_registry.py",
        "research/projects/price_action_strategy_lab/alpha_specs.py",
        "research/projects/price_action_strategy_lab/expression_modes.py",
        "research/projects/price_action_strategy_lab/backtest_modes.py",
        "research/projects/price_action_strategy_lab/selectors.py",
        "research/projects/price_action_strategy_lab/selector_registry.py",
        "research/projects/price_action_strategy_lab/chart_pack.py",
        "research/projects/price_action_strategy_lab/run_lab.py",
        "research/projects/price_action_strategy_lab/reports/README.md",
        "research/projects/price_action_strategy_lab/review_packs/README.md",
    ]
    assert any(task["task_id"] == "create_lab_scaffold" for task in state["initial_tasks"])
    assert any(task["status"] == "blocked" for task in state["initial_tasks"])

    assert "research-only tinkering lab" in readme
    assert "NSE market-collector universe" in readme
    assert "Chart Inspection" in readme
    assert "Alpha Expression Modes" in readme
    assert "Backtest Modes" in readme
    assert "Meta Selectors" in readme
    assert "No DB access outside `project/data/`" in readme
    assert "market_collector_panel" in readme
    assert "run_lab.py --config" in readme

    assert "mode: all_nse" in universe
    assert "source: market_collector" in universe
    assert "exchange: NSE" in universe
    assert "liquid_nse" in universe
    assert "high_vol_nse" in universe
    assert "custom_symbols" in universe
    assert "active_mask" in universe

    assert "cross_sectional_quintile" in lab_run
    assert "time_series_threshold" in lab_run
    assert "ranked_long_only" in lab_run
    json.loads(lab_run)

    assert "run_summary.md" in reports
    assert "mode_comparison.csv" in reports
    assert "chart_index.md" in reports
    assert "research-only" in reports
    assert "chart inspection notes" in review_packs
    assert "not deployment approvals" in review_packs
