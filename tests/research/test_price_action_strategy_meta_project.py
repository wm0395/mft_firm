from __future__ import annotations

import csv
import json
from pathlib import Path


def test_price_action_strategy_meta_project_scaffold() -> None:
    root = Path(__file__).resolve().parents[2] / "research" / "projects" / "price_action_strategy_meta"

    project = json.loads((root / "project.json").read_text(encoding="utf-8"))
    state = json.loads((root / "research_state.json").read_text(encoding="utf-8"))
    grid = json.loads((root / "parameter-grid.json").read_text(encoding="utf-8"))
    readme = (root / "README.md").read_text(encoding="utf-8")
    strategy_catalog = (root / "reports" / "strategy_catalog.md").read_text(encoding="utf-8")
    strategy_inventory = (root / "reports" / "strategy_inventory.md").read_text(encoding="utf-8")
    metrics_framework = (root / "reports" / "metrics_framework.md").read_text(encoding="utf-8")
    meta_selector_design = (root / "reports" / "meta_selector_design.md").read_text(encoding="utf-8")
    screening_results = (root / "reports" / "screening_results.md").read_text(encoding="utf-8")
    extra_screening = (root / "reports" / "extra_strategy_screening.md").read_text(encoding="utf-8")
    regime_analysis = (root / "reports" / "regime_analysis.md").read_text(encoding="utf-8")
    stock_regime = (root / "reports" / "stock_regime.md").read_text(encoding="utf-8")
    selector_gate = (root / "reports" / "selector_gate.md").read_text(encoding="utf-8")
    walk_forward = (root / "reports" / "selector_walk_forward.md").read_text(encoding="utf-8")
    observable_regime_gate = (root / "reports" / "observable_regime_gate.md").read_text(encoding="utf-8")
    review_pack = (root / "review_packs" / "price_action_meta_pack.md").read_text(encoding="utf-8")
    screening_csv = root / "reports" / "screening_results.csv"
    extra_screening_csv = root / "reports" / "extra_strategy_screening.csv"
    regime_strategy_csv = root / "reports" / "regime_strategy_summary.csv"
    regime_sector_csv = root / "reports" / "regime_sector_summary.csv"
    regime_liquidity_csv = root / "reports" / "regime_liquidity_summary.csv"
    regime_corr_csv = root / "reports" / "regime_correlations.csv"
    stock_summary_csv = root / "reports" / "stock_regime_summary.csv"
    stock_spread_csv = root / "reports" / "stock_regime_spreads.csv"
    gate_backtest_csv = root / "reports" / "selector_gate_backtest.csv"
    gate_rules_csv = root / "reports" / "selector_gate_rules.csv"
    walk_forward_summary_csv = root / "reports" / "selector_walk_forward_summary.csv"
    walk_forward_regime_csv = root / "reports" / "selector_walk_forward_regime.csv"
    research_audit = (root / "reports" / "research_audit.md").read_text(encoding="utf-8")
    embargo_failure = (root / "reports" / "embargo_failure_diagnosis.md").read_text(encoding="utf-8")
    selector_robustness = (root / "reports" / "selector_robustness.md").read_text(encoding="utf-8")
    selector_split_sensitivity = (root / "reports" / "selector_split_sensitivity.md").read_text(
        encoding="utf-8"
    )
    selector_null_benchmark = (root / "reports" / "selector_null_benchmark.md").read_text(
        encoding="utf-8"
    )
    selector_neutral_variant = (root / "reports" / "selector_neutral_variant.md").read_text(
        encoding="utf-8"
    )
    selector_neutral_summary_csv = root / "reports" / "selector_neutral_variant_summary.csv"
    selector_neutral_detail_csv = root / "reports" / "selector_neutral_variant_details.csv"

    assert project["research_project_id"] == "research_project:price_action_strategy_meta"
    assert project["status"] == "draft"
    assert project["phase"] == "selector gate hardening, embargo diagnosis, and robustness validation"
    assert project["review_pack_dir"] == "review_packs"
    assert state["project_id"] == "research_project:price_action_strategy_meta"
    assert state["summary_artifacts"] == [
        "research/projects/price_action_strategy_meta/reports/strategy_catalog.md",
        "research/projects/price_action_strategy_meta/reports/strategy_inventory.md",
        "research/projects/price_action_strategy_meta/reports/metrics_framework.md",
        "research/projects/price_action_strategy_meta/reports/meta_selector_design.md",
        "research/projects/price_action_strategy_meta/reports/screening_results.md",
        "research/projects/price_action_strategy_meta/reports/extra_strategy_screening.md",
        "research/projects/price_action_strategy_meta/reports/regime_analysis.md",
        "research/projects/price_action_strategy_meta/reports/stock_regime.md",
        "research/projects/price_action_strategy_meta/reports/selector_gate.md",
        "research/projects/price_action_strategy_meta/reports/selector_walk_forward.md",
        "research/projects/price_action_strategy_meta/reports/research_audit.md",
        "research/projects/price_action_strategy_meta/reports/embargo_failure_diagnosis.md",
        "research/projects/price_action_strategy_meta/reports/selector_robustness.md",
        "research/projects/price_action_strategy_meta/reports/selector_split_sensitivity.md",
        "research/projects/price_action_strategy_meta/reports/selector_null_benchmark.md",
        "research/projects/price_action_strategy_meta/reports/selector_neutral_variant.md",
        "research/projects/price_action_strategy_meta/reports/observable_regime_gate.md",
        "research/projects/price_action_strategy_meta/review_packs/price_action_meta_pack.md",
    ]
    assert state["phase"] == "selector gate hardening, embargo diagnosis, and robustness validation"
    assert any(task["status"] == "blocked" for task in state["initial_tasks"])
    assert "Walk-Forward Validation" in readme
    assert "research-only" in readme
    assert "Audit And Robustness" in readme
    assert "Supplemental Extra Screen" in readme
    assert "fisher_transform_reversal_10" in readme
    assert "inverse_fisher_rsi_reversal_10" in readme
    assert "opening_range_breakout" in strategy_catalog
    assert "support_resistance_levels" in strategy_catalog
    assert "on_balance_volume" in strategy_inventory
    assert "pyramiding_ladder" in strategy_inventory
    assert "relative_strength_index" in strategy_inventory
    assert "average_directional_index" in strategy_inventory
    assert "precision" in metrics_framework
    assert "walk-forward" in metrics_framework
    assert "abstain flag" in meta_selector_design
    assert "## expanded_high_vol_top100 / 5d" in screening_results
    assert "bollinger_percent_b_mean_reversion_20" in screening_results
    assert "Extra Strategy Screening" in extra_screening
    assert "fisher_transform_reversal_10" in extra_screening
    assert "relative_volume_breakout_20" in extra_screening
    assert "High-Confidence Gate Candidates" in regime_analysis
    assert "top 100 high-vol names" in regime_analysis
    assert "keltner_breakout_20" in regime_analysis
    assert "Metals & Mining" in regime_analysis
    assert "Stock Regime Map" in stock_regime
    assert "ADANIENT" in stock_regime
    assert "TATASTEEL" in stock_regime
    assert "Selector Gate" in selector_gate
    assert "high_conf" in selector_gate
    assert "combined always-on baseline" in selector_gate
    assert "still loses" in selector_gate
    assert "Walk-Forward Gate" in walk_forward
    assert "Family alignment bonus" in walk_forward
    assert "abstain" in walk_forward
    assert "research-only" in walk_forward
    assert "research_audit.md" in review_pack
    assert "embargo_failure_diagnosis.md" in review_pack
    assert "selector_robustness.md" in review_pack
    assert "selector_split_sensitivity.md" in review_pack
    assert "observable_regime_gate.md" in review_pack
    assert "selector_neutral_variant.md" in review_pack
    assert "screening_results.md" in review_pack
    assert "extra_strategy_screening.md" in review_pack
    assert "regime_analysis.md" in review_pack
    assert "selector_gate.md" in review_pack
    assert "selector_walk_forward.md" in review_pack
    assert "price-action strategy meta project" in review_pack
    with screening_csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    assert len(rows) > 0
    assert {
        "universe",
        "horizon",
        "family",
        "strategy",
        "gross_mean_bps",
        "rank_ic_mean",
        "net_mean_bps_10",
        "turnover",
    }.issubset(rows[0].keys())
    with extra_screening_csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        extra_rows = list(reader)
    assert len(extra_rows) == 72
    extra_cost_rows = [row for row in extra_rows if row["net_mean_bps_10"].strip()]
    assert any(
        row["strategy"] == "fisher_transform_reversal_10" and float(row["net_mean_bps_10"]) > 0.0
        for row in extra_cost_rows
    )
    assert any(
        row["strategy"] == "relative_volume_breakout_20" and float(row["net_mean_bps_10"]) < 0.0
        for row in extra_cost_rows
    )
    with regime_strategy_csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        regime_rows = list(reader)
    assert len(regime_rows) > 0
    assert {
        "universe",
        "horizon",
        "family",
        "strategy",
        "regime_dimension",
        "regime_state",
        "mean_net_bps",
    }.issubset(regime_rows[0].keys())
    for path in (regime_sector_csv, regime_liquidity_csv, regime_corr_csv):
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            assert len(list(reader)) > 0
    with stock_summary_csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        stock_rows = list(reader)
    assert len(stock_rows) > 0
    assert {
        "universe",
        "horizon",
        "regime_dimension",
        "regime_state",
        "symbol",
        "industry",
        "obs",
        "mean_net_bps",
        "delta_vs_baseline_bps",
    }.issubset(stock_rows[0].keys())
    with stock_spread_csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        spread_rows = list(reader)
    assert len(spread_rows) > 0
    assert {
        "positive_state",
        "negative_state",
        "spread_bps",
    }.issubset(spread_rows[0].keys())
    with gate_backtest_csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        gate_rows = list(reader)
    assert len(gate_rows) == 3
    high_conf = next(row for row in gate_rows if row["policy"] == "high_conf")
    assert float(high_conf["test_precision"]) >= 0.52
    assert float(high_conf["test_coverage"]) < 0.2
    assert float(high_conf["test_portfolio_mean_net_bps"]) < 9.8
    assert max(float(row["test_portfolio_mean_net_bps"]) for row in gate_rows) < 9.8
    with gate_rules_csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rules = list(reader)
    assert len(rules) > 0
    assert any(rule["strategy"] == "bollinger_percent_b_mean_reversion_20" for rule in rules)
    with walk_forward_summary_csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        walk_rows = list(reader)
    assert len(walk_rows) > 0
    assert {
        "split_type",
        "fold",
        "policy",
        "test_precision",
        "lift_vs_baseline_bps",
    }.issubset(walk_rows[0].keys())
    assert any(row["policy"] == "abstain" for row in walk_rows)
    lift_by_split: dict[str, list[float]] = {}
    for row in walk_rows:
        lift_by_split.setdefault(row["split_type"], []).append(float(row["lift_vs_baseline_bps"]))
    assert sum(lift_by_split["walk_forward"]) / len(lift_by_split["walk_forward"]) < 0.0
    assert sum(lift_by_split["purged"]) / len(lift_by_split["purged"]) < 0.0
    assert sum(lift_by_split["embargo"]) / len(lift_by_split["embargo"]) < 0.0
    with walk_forward_regime_csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        walk_regime_rows = list(reader)
    assert len(walk_regime_rows) > 0
    assert "Leakage and Timing Findings" in research_audit
    assert "KEEP_RESEARCH" in research_audit
    assert "Fold-level decomposition" in embargo_failure
    assert "Selector Split Sensitivity" in selector_split_sensitivity
    assert "SUSPECT_OVERFIT" in selector_split_sensitivity
    assert "Selector Null Benchmark" in selector_null_benchmark
    assert "random_strategy" in selector_null_benchmark
    assert "SUSPECT_OVERFIT" in embargo_failure
    assert "bootstrap confidence intervals" in selector_robustness
    assert "NEEDS_MORE_DATA" in selector_robustness
    assert "Selector Neutral Variant" in selector_neutral_variant
    assert "selected-portfolio sensitivity" in selector_neutral_variant
    assert "NEEDS_MORE_DATA" in selector_neutral_variant
    with selector_neutral_summary_csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        neutral_rows = list(reader)
    assert len(neutral_rows) == 4
    assert {
        "source",
        "mode",
        "raw_active_mean_net_bps",
        "neutral_active_mean_net_bps",
        "raw_portfolio_mean_net_bps",
        "neutral_portfolio_mean_net_bps",
    }.issubset(neutral_rows[0].keys())
    with selector_neutral_detail_csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        neutral_detail_rows = list(reader)
    assert len(neutral_detail_rows) > 0
    assert "Observable Regime Gate" in observable_regime_gate
    assert "SUSPECT_OVERFIT" in observable_regime_gate
    assert "drawdown" in observable_regime_gate
    assert grid["evaluation_protocol"]["cost_stress_bps"] == [0, 5, 10, 25]
    assert {family["family"] for family in grid["strategy_families"]} == {
        "breakout_continuation",
        "trend_following",
        "gap_reaction",
        "reversal_exhaustion",
        "structure_levels",
        "volume_confirmation",
    }
