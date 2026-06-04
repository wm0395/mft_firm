from __future__ import annotations

import csv
from pathlib import Path
import json


def test_ipo_liquidity_pressure_project_scaffold() -> None:
    root = Path(__file__).resolve().parents[2] / "research" / "projects" / "ipo_liquidity_pressure"

    project = json.loads((root / "project.json").read_text(encoding="utf-8"))
    state = json.loads((root / "research_state.json").read_text(encoding="utf-8"))
    grid = json.loads((root / "parameter-grid.json").read_text(encoding="utf-8"))
    with (root / "data" / "ipo_events_seed.csv").open(encoding="utf-8") as fh:
        seed_rows = list(csv.DictReader(fh))
    with (root / "data" / "ipo_event_windows_seed.csv").open(encoding="utf-8") as fh:
        window_rows = list(csv.DictReader(fh))
    with (root / "data" / "ipo_pilot_event_study.csv").open(encoding="utf-8") as fh:
        pilot_rows = list(csv.DictReader(fh))
    with (root / "data" / "ipo_pilot_event_study_controls.csv").open(encoding="utf-8") as fh:
        control_rows = list(csv.DictReader(fh))

    README = (root / "README.md").read_text(encoding="utf-8")
    mechanism = (root / "reports" / "mechanism_and_hypotheses.md").read_text(encoding="utf-8")
    data_contract = (root / "reports" / "data_contract.md").read_text(encoding="utf-8")
    event_design = (root / "reports" / "event_design.md").read_text(encoding="utf-8")
    validation = (root / "reports" / "validation_framework.md").read_text(encoding="utf-8")
    source_inventory = (root / "reports" / "source_inventory.md").read_text(encoding="utf-8")
    pilot_evidence = (root / "reports" / "pilot_evidence.md").read_text(encoding="utf-8")
    pilot_study = (root / "reports" / "pilot_event_study.md").read_text(encoding="utf-8")
    loop_report = (root / "research_loop_report.md").read_text(encoding="utf-8")
    review_pack = (root / "review_packs" / "ipo_liquidity_pressure_pack.md").read_text(encoding="utf-8")
    review_readme = (root / "review_packs" / "README.md").read_text(encoding="utf-8")

    assert project["research_project_id"] == "research_project:ipo_liquidity_pressure"
    assert project["review_pack_dir"] == "review_packs"
    assert project["status"] == "draft"
    assert project["phase"] == "pilot evidence collection and seed event study"
    assert state["project_id"] == "research_project:ipo_liquidity_pressure"
    assert state["summary_artifacts"] == [
        "research/projects/ipo_liquidity_pressure/reports/mechanism_and_hypotheses.md",
        "research/projects/ipo_liquidity_pressure/reports/data_contract.md",
        "research/projects/ipo_liquidity_pressure/reports/event_design.md",
        "research/projects/ipo_liquidity_pressure/reports/validation_framework.md",
        "research/projects/ipo_liquidity_pressure/reports/source_inventory.md",
        "research/projects/ipo_liquidity_pressure/reports/pilot_evidence.md",
        "research/projects/ipo_liquidity_pressure/reports/pilot_event_study.md",
        "research/projects/ipo_liquidity_pressure/reports/pilot_regime_control_panel.md",
        "research/projects/ipo_liquidity_pressure/data/ipo_events_seed.csv",
        "research/projects/ipo_liquidity_pressure/data/ipo_event_windows_seed.csv",
        "research/projects/ipo_liquidity_pressure/data/ipo_pilot_event_study.csv",
        "research/projects/ipo_liquidity_pressure/data/ipo_pilot_event_study_controls.csv",
        "research/projects/ipo_liquidity_pressure/research_loop_report.md",
        "research/projects/ipo_liquidity_pressure/review_packs/ipo_liquidity_pressure_pack.md",
    ]
    assert state["phase"] == "pilot evidence collection and seed event study"
    assert any(task["task_id"] == "seed_pilot_ipo_evidence" and task["status"] == "completed" for task in state["initial_tasks"])
    assert any(task["task_id"] == "pilot_event_study_seed_analysis" and task["status"] == "completed" for task in state["initial_tasks"])
    assert any(task["status"] == "blocked" for task in state["initial_tasks"])
    assert "source-backed seed sample" in README
    assert "twenty-eight mainboard IPOs" in README
    assert "Canara Robeco Asset Management Company Limited" in README
    assert "Medi Assist Healthcare Services Limited" in README
    assert "Euro Pratik Sales Limited" in README
    assert "Yatra Online Limited" in README
    assert "TruAlt Bioenergy Limited" in README
    assert "OM Freight Forwarders Limited" in README
    assert "Brigade Hotel Ventures Limited" in README
    assert "Glottis Limited" in README
    assert "Fabtech Technologies Limited" in README
    assert "Lenskart Solutions Limited" in README
    assert "One 97 Communications Limited" in README
    assert "Delhivery Limited" in README
    assert "Niva Bupa Health Insurance Company Limited" in README
    assert "Sagility India Limited" in README
    assert "Ather Energy Limited" in README
    assert "Schloss Bangalore Limited" in README
    assert "HDB Financial Services Limited" in README
    assert "Travel Food Services Limited" in README
    assert "Aegis Vopak Terminals Limited" in README
    assert "Afcons Infrastructure Limited" in README
    assert "NTPC Green Energy Limited" in README
    assert "Vishal Mega Mart Limited" in README
    assert "pilot event study" in README.lower()
    assert "Pilot Evidence" in README
    assert "Reports" in README
    assert "review pack" in README.lower()
    assert "Hypotheses" in mechanism
    assert "pull" in mechanism.lower()
    assert "ipo_events" in data_contract
    assert "No lookahead" in data_contract
    assert "NII into" in data_contract
    assert "IPO open date" in event_design
    assert "Mainboard IPOs" in event_design
    assert "Mechanism gate" in validation
    assert "Case A" in validation
    assert "Urban Company" in source_inventory
    assert "Rubicon Research" in source_inventory
    assert "Canara Robeco" in source_inventory
    assert "Canara HSBC" in source_inventory
    assert "LG Electronics" in source_inventory
    assert "medi_assist_basis_allotment_notice" in source_inventory
    assert "Euro Pratik" in source_inventory
    assert "yatra_online_basis_allotment_notice" in source_inventory
    assert "TruAlt" in source_inventory
    assert "Saatvik Green Energy" in source_inventory
    assert "Sudeep Pharma" in source_inventory
    assert "Om Freight Forwarders" in source_inventory
    assert "Brigade Hotel Ventures" in source_inventory
    assert "Glottis" in source_inventory
    assert "Fabtech" in source_inventory
    assert "Lenskart Solutions" in source_inventory
    assert "niva_bupa_public_announcement" in source_inventory
    assert "niva_bupa_track_record" in source_inventory
    assert "sagility_public_announcement" in source_inventory
    assert "sagility_track_record" in source_inventory
    assert "ather_energy_basis_allotment_notice" in source_inventory
    assert "schloss_bangalore_basis_allotment_notice" in source_inventory
    assert "aegis_vopak_annual_report" in source_inventory
    assert "aegis_vopak_basis_allotment_notice" in source_inventory
    assert "afcons_infrastructure_basis_allotment_notice" in source_inventory
    assert "NTPC Green Energy" in source_inventory
    assert "ntpc_green_energy_basis_allotment_notice" in source_inventory
    assert "ntpc_green_energy_listing_notice" in source_inventory
    assert "Vishal Mega Mart" in source_inventory
    assert "vishal_mega_mart_basis_allotment_notice" in source_inventory
    assert "vishal_mega_mart_listing_notice" in source_inventory
    assert "paytm_seed_bundle" in source_inventory
    assert "paytm_track_record" in source_inventory
    assert "delhivery_seed_bundle" in source_inventory
    assert "delhivery_track_record" in source_inventory
    assert "hdb_financial_services_basis_allotment_notice" in source_inventory
    assert "travel_food_services_basis_allotment_notice" in source_inventory
    assert "Brigade Hotel Ventures Limited" in pilot_evidence
    assert "60.49x" in pilot_evidence
    assert "109.37x" in pilot_evidence
    assert "7.12x" in pilot_evidence
    assert "1.91x" in pilot_evidence
    assert "38.17x" in pilot_evidence
    assert "11.71x" in pilot_evidence
    assert "1.41x" in pilot_evidence
    assert "1.39x" in pilot_evidence
    assert "52.93x" in pilot_evidence
    assert "5.14x" in pilot_evidence
    assert "65.96x" in pilot_evidence
    assert "3.39x" in pilot_evidence
    assert "3.15x" in pilot_evidence
    assert "6.82x" in pilot_evidence
    assert "2.82x" in pilot_evidence
    assert "1.68x" in pilot_evidence
    assert "5.73x" in pilot_evidence
    assert "1.98x" in pilot_evidence
    assert "2.85x" in pilot_evidence
    assert "28.35x" in pilot_evidence
    assert "1171.58" in pilot_evidence
    assert "775.00" in pilot_evidence
    assert "84,429,103" in pilot_evidence
    assert "7596.00" in pilot_evidence
    assert "28,028,168" in pilot_evidence
    assert "54,577,465" in pilot_evidence
    assert "307.00" in pilot_evidence
    assert "7391.41" in pilot_evidence
    assert "230.30" in pilot_evidence
    assert "3.07x" in pilot_evidence
    assert "10.27x" in pilot_evidence
    assert "17.27x" in pilot_evidence
    assert "40.09x" in pilot_evidence
    assert "7.47x" in pilot_evidence
    assert "21.75x" in pilot_evidence
    assert "2.23x" in pilot_evidence
    assert "0.28x" in pilot_evidence
    assert "0.51x" in pilot_evidence
    assert "2.10x" in pilot_evidence
    assert "1.47x" in pilot_evidence
    assert "3.79x" in pilot_evidence
    assert "2.15x" in pilot_evidence
    assert "2.64x" in pilot_evidence
    assert "1.64x" in pilot_evidence
    assert "2.01x" in pilot_evidence
    assert "One 97 Communications Limited" in pilot_evidence
    assert "Delhivery Limited" in pilot_evidence
    assert "Niva Bupa Health Insurance Company Limited" in pilot_evidence
    assert "Sagility India Limited" in pilot_evidence
    assert "Ather Energy Limited" in pilot_evidence
    assert "Schloss Bangalore Limited" in pilot_evidence
    assert "HDB Financial Services Limited" in pilot_evidence
    assert "Travel Food Services Limited" in pilot_evidence
    assert "Aegis Vopak Terminals Limited" in pilot_evidence
    assert "Afcons Infrastructure Limited" in pilot_evidence
    assert "NTPC Green Energy Limited" in pilot_evidence
    assert "Vishal Mega Mart Limited" in pilot_evidence
    assert "1.66x" in pilot_evidence
    assert "2.77x" in pilot_evidence
    assert "17.62x" in pilot_evidence
    assert "3.04x" in pilot_evidence
    assert "1.95x" in pilot_evidence
    assert "1.33x" in pilot_evidence
    assert "1.90x" in pilot_evidence
    assert "3.14x" in pilot_evidence
    assert "1.50x" in pilot_evidence
    assert "3.06x" in pilot_evidence
    assert "18300.00" in pilot_evidence
    assert "5235.00" in pilot_evidence
    assert "2200.00" in pilot_evidence
    assert "2106.40" in pilot_evidence
    assert "2800.00" in pilot_evidence
    assert "5430.00" in pilot_evidence
    assert "10000.00" in pilot_evidence
    assert "8000.00" in pilot_evidence
    assert "92,867,945" in pilot_evidence
    assert "80,459,769" in pilot_evidence
    assert "119,148,936" in pilot_evidence
    assert "117,327,139" in pilot_evidence
    assert "926,824,881" in pilot_evidence
    assert "1,025,641,025" in pilot_evidence
    assert "1.86x" in pilot_evidence
    assert "0.61x" in pilot_evidence
    assert "0.74x" in pilot_evidence
    assert "1.76x" in pilot_evidence
    assert "0.83x" in pilot_evidence
    assert "0.55x" in pilot_evidence
    assert "0.69x" in pilot_evidence
    assert "3.43x" in pilot_evidence
    assert "0.94x" in pilot_evidence
    assert "1.35x" in pilot_evidence
    assert "13.35x" in pilot_evidence
    assert "3.96x" in pilot_evidence
    assert "0.83089x" in pilot_evidence
    assert "0.78578x" in pilot_evidence
    assert "1.05668x" in pilot_evidence
    assert "7.50328x" in pilot_evidence
    assert "1.94x" in pilot_evidence
    assert "20.46768x" in pilot_evidence
    assert "3.75x" in pilot_evidence
    assert "1.39x" in pilot_evidence
    assert "2.44355x" in pilot_evidence
    assert "10.44657x" in pilot_evidence
    assert "17.21215x" in pilot_evidence
    assert "85.07713x" in pilot_evidence
    assert "28-event seed sample" in pilot_study
    assert "Application recent winners 60d top50 AR averages: extreme 0.0005, high -0.0027, medium 0.0053, low -0.0003." in pilot_study
    assert "NTPC Green Energy Limited" in pilot_study
    assert "Vishal Mega Mart Limited" in pilot_study
    assert "mixed" in pilot_study.lower()
    assert "twenty-eight official mainboard IPOs" in loop_report
    regime_panel = (root / "reports" / "pilot_regime_control_panel.md").read_text(encoding="utf-8")
    assert "volatile bucket" in regime_panel.lower()
    assert "same-sector peers remain split" in regime_panel.lower()
    assert "Medi Assist Healthcare Services" in review_pack
    assert "Niva Bupa Health Insurance" in review_pack
    assert "Sagility" in review_pack
    assert "Ather Energy" in review_pack
    assert "Schloss Bangalore" in review_pack
    assert "HDB Financial Services" in review_pack
    assert "Travel Food Services" in review_pack
    assert "Aegis Vopak Terminals" in review_pack
    assert "Afcons Infrastructure" in review_pack
    assert "NTPC Green Energy" in review_pack
    assert "Vishal Mega Mart" in review_pack
    assert len(seed_rows) == 28
    seed_by_symbol = {row["symbol_after_listing"]: row for row in seed_rows}
    assert seed_by_symbol["URBANCO"]["pressure_class"] == "extreme"
    assert seed_by_symbol["RUBICON"]["subscription_total_multiple"] == "109.37"
    assert seed_by_symbol["TRUALT"]["pressure_class"] == "extreme"
    assert seed_by_symbol["TRUALT"]["subscription_total_multiple"] == "52.93"
    assert seed_by_symbol["CRAMC"]["pressure_class"] == "high"
    assert seed_by_symbol["CRAMC"]["subscription_total_multiple"] == "7.12"
    assert seed_by_symbol["SAATVIK"]["pressure_class"] == "medium"
    assert seed_by_symbol["SAATVIK"]["subscription_total_multiple"] == "5.14"
    assert seed_by_symbol["CANHLIFE"]["pressure_class"] == "low"
    assert seed_by_symbol["CANHLIFE"]["subscription_total_multiple"] == "1.91"
    assert seed_by_symbol["LGEINDIA"]["pressure_class"] == "extreme"
    assert seed_by_symbol["LGEINDIA"]["subscription_total_multiple"] == "38.17"
    assert seed_by_symbol["MEDIASSIST"]["pressure_class"] == "high"
    assert seed_by_symbol["MEDIASSIST"]["subscription_total_multiple"] == "11.71"
    assert seed_by_symbol["EUROPRATIK"]["pressure_class"] == "low"
    assert seed_by_symbol["EUROPRATIK"]["subscription_total_multiple"] == "1.41"
    assert seed_by_symbol["YATRA"]["pressure_class"] == "low"
    assert seed_by_symbol["YATRA"]["subscription_total_multiple"] == "1.39"
    assert seed_by_symbol["SUDEEPPHRM"]["pressure_class"] == "extreme"
    assert seed_by_symbol["SUDEEPPHRM"]["subscription_total_multiple"] == "65.96"
    assert seed_by_symbol["OMFREIGHT"]["pressure_class"] == "medium"
    assert seed_by_symbol["OMFREIGHT"]["subscription_total_multiple"] == "3.39"
    assert seed_by_symbol["BRIGHOTEL"]["pressure_class"] == "medium"
    assert seed_by_symbol["BRIGHOTEL"]["subscription_total_multiple"] == "3.15"
    assert seed_by_symbol["GLOTTIS"]["pressure_class"] == "low"
    assert seed_by_symbol["GLOTTIS"]["subscription_total_multiple"] == "1.98"
    assert seed_by_symbol["FABTECH"]["pressure_class"] == "medium"
    assert seed_by_symbol["FABTECH"]["subscription_total_multiple"] == "2.85"
    assert seed_by_symbol["LENSKART"]["pressure_class"] == "extreme"
    assert seed_by_symbol["LENSKART"]["subscription_total_multiple"] == "28.35"
    assert seed_by_symbol["PAYTM"]["pressure_class"] == "low"
    assert seed_by_symbol["PAYTM"]["subscription_total_multiple"] == "1.95"
    assert seed_by_symbol["DELHIVERY"]["pressure_class"] == "low"
    assert seed_by_symbol["DELHIVERY"]["subscription_total_multiple"] == "1.33"
    assert seed_by_symbol["NIVABUPA"]["pressure_class"] == "low"
    assert seed_by_symbol["NIVABUPA"]["subscription_total_multiple"] == "1.90"
    assert seed_by_symbol["SAGILITY"]["pressure_class"] == "medium"
    assert seed_by_symbol["SAGILITY"]["subscription_total_multiple"] == "3.14"
    assert seed_by_symbol["ATHERENERG"]["pressure_class"] == "low"
    assert seed_by_symbol["ATHERENERG"]["subscription_total_multiple"] == "1.50"
    assert seed_by_symbol["THELEELA"]["pressure_class"] == "medium"
    assert seed_by_symbol["THELEELA"]["subscription_total_multiple"] == "3.06"
    assert seed_by_symbol["HDBFS"]["pressure_class"] == "high"
    assert seed_by_symbol["HDBFS"]["subscription_total_multiple"] == "17.62"
    assert seed_by_symbol["TRAVELFOOD"]["pressure_class"] == "medium"
    assert seed_by_symbol["TRAVELFOOD"]["subscription_total_multiple"] == "3.04"
    assert seed_by_symbol["AEGISVOPAK"]["pressure_class"] == "low"
    assert seed_by_symbol["AEGISVOPAK"]["subscription_total_multiple"] == "1.66"
    assert seed_by_symbol["AFCONS"]["pressure_class"] == "medium"
    assert seed_by_symbol["AFCONS"]["subscription_total_multiple"] == "2.77"
    assert seed_by_symbol["NTPCGREEN"]["pressure_class"] == "low"
    assert seed_by_symbol["NTPCGREEN"]["subscription_total_multiple"] == "1.94"
    assert seed_by_symbol["VMM"]["pressure_class"] == "high"
    assert seed_by_symbol["VMM"]["subscription_total_multiple"] == "20.46768"
    assert len(window_rows) == 140
    assert len(pilot_rows) == 700
    assert len(control_rows) == 700
    assert {row["control_market_regime"] for row in control_rows} == {"volatile"}
    assert round(float(next(row["abnormal_return"] for row in pilot_rows if row["company_name"] == "Aegis Vopak Terminals Limited" and row["basket_name"] == "same_sector_peer" and row["window_name"] == "application")), 4) == 0.0009
    assert round(float(next(row["abnormal_return"] for row in pilot_rows if row["company_name"] == "Afcons Infrastructure Limited" and row["basket_name"] == "same_sector_peer" and row["window_name"] == "application")), 4) == 0.0002
    assert round(float(next(row["abnormal_return"] for row in pilot_rows if row["company_name"] == "Ather Energy Limited" and row["basket_name"] == "same_sector_peer" and row["window_name"] == "application")), 4) == 0.0067
    assert round(float(next(row["abnormal_return"] for row in pilot_rows if row["company_name"] == "Schloss Bangalore Limited" and row["basket_name"] == "same_sector_peer" and row["window_name"] == "application")), 4) == -0.0234
    assert round(float(next(row["abnormal_return"] for row in pilot_rows if row["company_name"] == "Brigade Hotel Ventures Limited" and row["basket_name"] == "recent_winners_60d_top50" and row["window_name"] == "application")), 4) == 0.0065
    assert round(float(next(row["abnormal_return"] for row in pilot_rows if row["company_name"] == "Brigade Hotel Ventures Limited" and row["basket_name"] == "cash_source_60d_top50" and row["window_name"] == "release_5")), 4) == 0.0055
    assert round(float(next(row["abnormal_return"] for row in pilot_rows if row["company_name"] == "Medi Assist Healthcare Services Limited" and row["basket_name"] == "recent_winners_60d_top50" and row["window_name"] == "application")), 4) == -0.0096
    assert round(float(next(row["abnormal_return"] for row in pilot_rows if row["company_name"] == "Yatra Online Limited" and row["basket_name"] == "recent_winners_60d_top50" and row["window_name"] == "application")), 4) == 0.0040
    assert round(float(next(row["abnormal_return"] for row in pilot_rows if row["company_name"] == "Urban Company Limited" and row["basket_name"] == "same_sector_peer" and row["window_name"] == "application")), 4) == -0.02
    assert round(float(next(row["abnormal_return"] for row in pilot_rows if row["company_name"] == "Canara Robeco Asset Management Company Limited" and row["basket_name"] == "same_sector_peer" and row["window_name"] == "application")), 4) == 0.0104
    assert round(float(next(row["abnormal_return"] for row in pilot_rows if row["company_name"] == "Canara HSBC Life Insurance Company Limited" and row["basket_name"] == "same_sector_peer" and row["window_name"] == "application")), 4) == 0.0117
    assert round(float(next(row["abnormal_return"] for row in pilot_rows if row["company_name"] == "LG Electronics India Limited" and row["basket_name"] == "same_sector_peer" and row["window_name"] == "application")), 4) == 0.0102
    assert round(float(next(row["abnormal_return"] for row in pilot_rows if row["company_name"] == "Lenskart Solutions Limited" and row["basket_name"] == "same_sector_peer" and row["window_name"] == "application")), 4) == -0.0033
    assert round(float(next(row["abnormal_return"] for row in pilot_rows if row["company_name"] == "Medi Assist Healthcare Services Limited" and row["basket_name"] == "cash_source_60d_top50" and row["window_name"] == "release_5")), 4) == -0.0036
    assert round(float(next(row["abnormal_return"] for row in pilot_rows if row["company_name"] == "Yatra Online Limited" and row["basket_name"] == "cash_source_60d_top50" and row["window_name"] == "release_5")), 4) == -0.0088
    assert round(float(next(row["abnormal_return"] for row in pilot_rows if row["company_name"] == "Euro Pratik Sales Limited" and row["basket_name"] == "recent_winners_60d_top50" and row["window_name"] == "application")), 4) == -0.0122
    assert round(float(next(row["abnormal_return"] for row in pilot_rows if row["company_name"] == "Om Freight Forwarders Limited" and row["basket_name"] == "recent_winners_60d_top50" and row["window_name"] == "application")), 4) == 0.0085
    assert round(float(next(row["abnormal_return"] for row in pilot_rows if row["company_name"] == "TruAlt Bioenergy Limited" and row["basket_name"] == "cash_source_60d_top50" and row["window_name"] == "application")), 4) == 0.0085
    assert round(float(next(row["abnormal_return"] for row in pilot_rows if row["company_name"] == "One 97 Communications Limited" and row["basket_name"] == "recent_winners_60d_top50" and row["window_name"] == "application")), 4) == 0.0003
    assert round(float(next(row["abnormal_return"] for row in pilot_rows if row["company_name"] == "Delhivery Limited" and row["basket_name"] == "same_sector_peer" and row["window_name"] == "application")), 4) == -0.0019
    assert "reviewable record" in review_readme.lower()
    assert "mixed" in review_pack.lower()
    assert grid["listing_regime"] == ["pre_t_plus_3", "post_t_plus_3"]
    assert grid["basket_type"] == [
        "broad_market",
        "retail_sensitive",
        "recent_winners",
        "liquid_cash_source",
        "same_sector",
    ]
