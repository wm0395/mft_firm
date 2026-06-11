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
    with (root / "data" / "ipo_sector_conditioned_event_study.csv").open(encoding="utf-8") as fh:
        sector_conditioned_rows = list(csv.DictReader(fh))
    with (root / "data" / "ipo_sector_adjusted_basket_event_study.csv").open(encoding="utf-8") as fh:
        sector_adjusted_rows = list(csv.DictReader(fh))
    with (root / "data" / "ipo_pressure_gradient_diagnostics.csv").open(encoding="utf-8") as fh:
        gradient_rows = list(csv.DictReader(fh))
    with (root / "data" / "ipo_pressure_gradient_stability.csv").open(encoding="utf-8") as fh:
        stability_rows = list(csv.DictReader(fh))
    with (root / "data" / "direct_market_history_sources.csv").open(encoding="utf-8") as fh:
        direct_market_rows = list(csv.DictReader(fh))
    with (root / "data" / "direct_market_history_collection_manifest.csv").open(encoding="utf-8") as fh:
        direct_market_manifest_rows = list(csv.DictReader(fh))

    README = (root / "README.md").read_text(encoding="utf-8")
    mechanism = (root / "reports" / "mechanism_and_hypotheses.md").read_text(encoding="utf-8")
    data_contract = (root / "reports" / "data_contract.md").read_text(encoding="utf-8")
    event_design = (root / "reports" / "event_design.md").read_text(encoding="utf-8")
    validation = (root / "reports" / "validation_framework.md").read_text(encoding="utf-8")
    source_inventory = (root / "reports" / "source_inventory.md").read_text(encoding="utf-8")
    pilot_evidence = (root / "reports" / "pilot_evidence.md").read_text(encoding="utf-8")
    pilot_study = (root / "reports" / "pilot_event_study.md").read_text(encoding="utf-8")
    market_history = (root / "reports" / "market_history_expansion.md").read_text(encoding="utf-8")
    direct_market_history = (
        root / "reports" / "direct_market_history_sources.md"
    ).read_text(encoding="utf-8")
    direct_market_loader = (
        root / "reports" / "direct_market_history_loader.md"
    ).read_text(encoding="utf-8")
    sector_history = (root / "reports" / "sector_history_expansion.md").read_text(encoding="utf-8")
    sector_conditioned = (root / "reports" / "sector_conditioned_event_study.md").read_text(encoding="utf-8")
    sector_adjusted = (root / "reports" / "sector_adjusted_basket_event_study.md").read_text(encoding="utf-8")
    gradient_report = (root / "reports" / "pressure_gradient_diagnostics.md").read_text(encoding="utf-8")
    stability_report = (root / "reports" / "pressure_gradient_stability.md").read_text(encoding="utf-8")
    loop_report = (root / "research_loop_report.md").read_text(encoding="utf-8")
    next_queue = (root / "next_queue.md").read_text(encoding="utf-8")
    review_pack = (root / "review_packs" / "ipo_liquidity_pressure_pack.md").read_text(encoding="utf-8")
    review_readme = (root / "review_packs" / "README.md").read_text(encoding="utf-8")

    assert project["research_project_id"] == "research_project:ipo_liquidity_pressure"
    assert project["review_pack_dir"] == "review_packs"
    assert project["status"] == "draft"
    assert project["phase"] == "pilot evidence collection, seed event study, and market-history expansion"
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
        "research/projects/ipo_liquidity_pressure/data/index_prices.parquet",
        "research/projects/ipo_liquidity_pressure/data/market_liquidity.parquet",
        "research/projects/ipo_liquidity_pressure/data/market_history_symbol_coverage.csv",
        "research/projects/ipo_liquidity_pressure/data/sector_history.parquet",
        "research/projects/ipo_liquidity_pressure/data/sector_history_coverage.csv",
        "research/projects/ipo_liquidity_pressure/data/ipo_sector_conditioned_event_study.csv",
        "research/projects/ipo_liquidity_pressure/data/ipo_sector_adjusted_basket_event_study.csv",
        "research/projects/ipo_liquidity_pressure/data/ipo_pressure_gradient_diagnostics.csv",
        "research/projects/ipo_liquidity_pressure/data/ipo_pressure_gradient_stability.csv",
        "research/projects/ipo_liquidity_pressure/reports/market_history_expansion.md",
        "research/projects/ipo_liquidity_pressure/data/direct_market_history_sources.csv",
        "research/projects/ipo_liquidity_pressure/reports/direct_market_history_sources.md",
        "research/projects/ipo_liquidity_pressure/data/direct_market_history_collection_manifest.csv",
        "research/projects/ipo_liquidity_pressure/reports/direct_market_history_loader.md",
        "research/projects/ipo_liquidity_pressure/reports/direct_liquidity_falsification.md",
        "research/projects/ipo_liquidity_pressure/reports/sector_history_expansion.md",
        "research/projects/ipo_liquidity_pressure/reports/sector_conditioned_event_study.md",
        "research/projects/ipo_liquidity_pressure/reports/sector_adjusted_basket_event_study.md",
        "research/projects/ipo_liquidity_pressure/reports/pressure_gradient_diagnostics.md",
        "research/projects/ipo_liquidity_pressure/reports/pressure_gradient_stability.md",
        "research/projects/ipo_liquidity_pressure/research_loop_report.md",
        "research/projects/ipo_liquidity_pressure/review_packs/ipo_liquidity_pressure_pack.md",
    ]
    assert state["phase"] == "pilot evidence collection, seed event study, and market-history expansion"
    assert any(task["task_id"] == "seed_pilot_ipo_evidence" and task["status"] == "completed" for task in state["initial_tasks"])
    assert any(task["task_id"] == "pilot_event_study_seed_analysis" and task["status"] == "completed" for task in state["initial_tasks"])
    assert any(task["task_id"] == "discover_direct_market_history_sources" and task["status"] == "completed" for task in state["initial_tasks"])
    assert any(task["task_id"] == "build_direct_market_history_loader" and task["status"] == "completed" for task in state["initial_tasks"])
    assert any(task["status"] == "blocked" for task in state["initial_tasks"])
    assert "source-backed seed sample" in README
    assert "thirty-eight mainboard IPOs" in README
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
    assert "Blue Jet Healthcare Limited" in README
    assert "Honasa Consumer Limited" in README
    assert "Chemplast Sanmar Limited" in README
    assert "Fino Payments Bank Limited" in README
    assert "Fedbank Financial Services Limited" in README
    assert "BlackBuck / Zinka Logistics Solutions Limited" in README
    assert "Bajaj Housing Finance Limited" in README
    assert "Tata Technologies Limited" in README
    assert "Waaree Energies Limited" in README
    assert "KRN Heat Exchanger and Refrigeration Limited" in README
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
    assert "Market History Expansion" in README
    assert "Direct Market History Sources" in README
    assert "Direct Market Loader" in README
    assert "direct_market_history_collection_manifest.csv" in README
    assert "direct_market_history_loader.md" in README
    assert "Sector History Expansion" in README
    assert "Sector-Conditioned Event Study" in README
    assert "Sector-Adjusted Basket Event Study" in README
    assert "Pressure Gradient Diagnostics" in README
    assert "Pressure Gradient Stability" in README
    assert "Pilot Evidence" in README
    assert "Reports" in README
    assert "review pack" in README.lower()
    assert "sector-history expansion pass" in README.lower()
    assert "sector-relative conditioning layer" in README.lower()
    assert "sector-adjusted" in README.lower()
    assert "same-sector peer averages remain mixed" in README.lower()
    assert "broader sector-adjusted basket pass" in README.lower()
    assert "pressure-gradient diagnostic compares raw and sector-adjusted basket" in README.lower()
    assert "returns across the ordered pressure buckets" in README.lower()
    assert "midcap150" in README
    assert "the stability pass stress-tests that narrow lead against adjacent windows" in README.lower()
    assert "nearby basket definitions" in README.lower()
    assert "small/midcap baskets" in README.lower()
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
    assert "blue_jet_healthcare_basis_allotment_notice" in source_inventory
    assert "honasa_consumer_basis_allotment_notice" in source_inventory
    assert "chemplast_sanmar_basis_allotment_notice" in source_inventory
    assert "fino_payments_bank_basis_allotment_notice" in source_inventory
    assert "fedbank_financial_services_basis_allotment_notice" in source_inventory
    assert "blackbuck_basis_allotment_notice" in source_inventory
    assert "bajaj_housing_finance_basis_allotment_notice" in source_inventory
    assert "tata_technologies_basis_allotment_notice" in source_inventory
    assert "waaree_energies_basis_allotment_notice" in source_inventory
    assert "krn_heat_exchanger_basis_allotment_notice" in source_inventory
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
    assert "Blue Jet Healthcare Limited" in pilot_evidence
    assert "Honasa Consumer Limited" in pilot_evidence
    assert "Chemplast Sanmar Limited" in pilot_evidence
    assert "Fino Payments Bank Limited" in pilot_evidence
    assert "Fedbank Financial Services Limited" in pilot_evidence
    assert "BlackBuck / Zinka Logistics Solutions Limited" in pilot_evidence
    assert "Bajaj Housing Finance Limited" in pilot_evidence
    assert "Tata Technologies Limited" in pilot_evidence
    assert "Waaree Energies Limited" in pilot_evidence
    assert "KRN Heat Exchanger and Refrigeration Limited" in pilot_evidence
    assert "5.97x" in pilot_evidence
    assert "4.66x" in pilot_evidence
    assert "1.61x" in pilot_evidence
    assert "1.65x" in pilot_evidence
    assert "1.8961x" in pilot_evidence
    assert "1.35x" in pilot_evidence
    assert "49.97x" in pilot_evidence
    assert "51.7788x" in pilot_evidence
    assert "56.44x" in pilot_evidence
    assert "211.95x" in pilot_evidence
    assert "24,285,160" in pilot_evidence
    assert "52,516,742" in pilot_evidence
    assert "71,164,509" in pilot_evidence
    assert "20,802,305" in pilot_evidence
    assert "78,073,810" in pilot_evidence
    assert "40,834,701" in pilot_evidence
    assert "937,142,856" in pilot_evidence
    assert "60,850,278" in pilot_evidence
    assert "28,752,095" in pilot_evidence
    assert "15,543,000" in pilot_evidence
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
    assert "38-event seed sample" in pilot_study
    assert "Application recent winners 60d top50 AR averages: extreme 0.0010, high -0.0027, medium 0.0057, low 0.0011." in pilot_study
    assert "Blue Jet Healthcare Limited" in pilot_study
    assert "Honasa Consumer Limited" in pilot_study
    assert "Chemplast Sanmar Limited" in pilot_study
    assert "Fino Payments Bank Limited" in pilot_study
    assert "Fedbank Financial Services Limited" in pilot_study
    assert "BlackBuck / Zinka Logistics Solutions Limited" in pilot_study
    assert "Bajaj Housing Finance Limited" in pilot_study
    assert "Tata Technologies Limited" in pilot_study
    assert "Waaree Energies Limited" in pilot_study
    assert "KRN Heat Exchanger and Refrigeration Limited" in pilot_study
    assert "NTPC Green Energy Limited" in pilot_study
    assert "Vishal Mega Mart Limited" in pilot_study
    assert "mixed" in pilot_study.lower()
    assert "21 of the 38 seed IPO symbols" in market_history
    assert "26 of the 38 seed IPO symbols" in market_history
    assert "Market History Expansion" in market_history
    assert "market-liquidity panel" in market_history.lower()
    assert "project_mft.duckdb" in market_history
    assert "missing from all three local price stores" in market_history.lower()
    assert "Direct Market History Sources" in direct_market_history
    assert "business growth data across all segments" in direct_market_history.lower()
    assert "market activity report" in direct_market_history.lower()
    assert "segment-wise historical reports - capital market" in direct_market_history.lower()
    assert "security-wise price volume archives (equities)" in direct_market_history.lower()
    assert "security-wise delivery positions" in direct_market_history.lower()
    assert "fii/fpi and dii trading activity" in direct_market_history.lower()
    assert "historical fii/fpi & dii trading activity on nse, bse and msei" in direct_market_history.lower()
    assert len(direct_market_rows) == 10
    assert len({row["status"] for row in direct_market_rows}) == 1
    assert any(row["family"] == "Business Growth Data across all segments" for row in direct_market_rows)
    assert any(row["family"] == "Segment-wise Historical Reports - Capital Market" for row in direct_market_rows)
    assert any(row["family"] == "Security-wise Price Volume Archives (Equities)" for row in direct_market_rows)
    assert any(row["family"] == "CM - Category-wise Turnover" for row in direct_market_rows)
    assert any(
        row["family"] == "Historical FII/FPI & DII trading activity on NSE, BSE and MSEI"
        for row in direct_market_rows
    )
    assert "Direct Market Loader" in direct_market_loader
    assert "parser-ready families: 9 of 10" in direct_market_loader.lower()
    assert "market-activity parser" in direct_market_loader.lower()
    assert "security-wise price-volume parser" in direct_market_loader.lower()
    assert "delivery-position parser" in direct_market_loader.lower()
    assert "fii/dii parser" in direct_market_loader.lower()
    assert "capital-market monthly workbook parser" in direct_market_loader.lower()
    assert "category-wise turnover" in direct_market_loader.lower()
    assert "mode of trading" in direct_market_loader.lower()
    assert "manifest-only" in direct_market_loader.lower()
    assert len(direct_market_manifest_rows) == 10
    assert len({row["parser_status"] for row in direct_market_manifest_rows}) == 2
    assert any(row["family"] == "Business Growth Data across all segments" and row["parser_status"] == "parser_ready" for row in direct_market_manifest_rows)
    assert any(row["family"] == "CM - Market Activity Report" and row["parser_kind"] == "market_activity_csv" for row in direct_market_manifest_rows)
    assert any(row["family"] == "Security-wise Price Volume Archives (Equities)" and row["parser_kind"] == "security_price_volume_csv" and row["parser_status"] == "parser_ready" for row in direct_market_manifest_rows)
    assert any(row["family"] == "CM - Security-wise Delivery Positions" and row["parser_kind"] == "delivery_positions_dat" and row["parser_status"] == "parser_ready" for row in direct_market_manifest_rows)
    assert any(row["family"] == "FII/FPI and DII trading activity" and row["parser_kind"] == "fii_dii_csv" for row in direct_market_manifest_rows)
    assert any(row["family"] == "Historical FII/FPI & DII trading activity on NSE, BSE and MSEI" and row["parser_status"] == "parser_ready" for row in direct_market_manifest_rows)
    assert any(row["family"] == "CM - Category-wise Turnover" and row["parser_kind"] == "capital_market_monthly_xlsx" and row["parser_status"] == "parser_ready" for row in direct_market_manifest_rows)
    assert any(row["family"] == "CM - Mode of Trading" and row["parser_kind"] == "capital_market_monthly_xlsx" and row["parser_status"] == "parser_ready" for row in direct_market_manifest_rows)
    assert any(row["family"] == "Segment-wise Historical Reports - Capital Market" and row["parser_kind"] == "capital_market_monthly_xlsx" and row["parser_status"] == "parser_ready" for row in direct_market_manifest_rows)
    assert any(row["family"] == "Historical Reports - Capital Market" and row["parser_status"] == "manifest_only" for row in direct_market_manifest_rows)
    assert "thirty-eight official mainboard IPOs" in loop_report
    assert "sector-return and sector-turnover proxy panel" in loop_report.lower()
    assert "same-sector peer pass now covers 26 of the 38 seed ipo symbols" in loop_report.lower().replace("\n", " ")
    assert "26 of" in loop_report
    assert "38 seed IPO symbols" in loop_report
    assert "broader sector-adjusted basket pass" in loop_report.lower()
    assert "pressure-gradient diagnostic adds one narrow sector-adjusted lead" in loop_report.lower()
    assert "pressure-gradient stability pass shows that the midcap150 sector-adjusted lead does not generalize" in loop_report.lower()
    assert "direct nse market-history source inventory" in loop_report.lower().replace("\n", " ")
    assert "raw nse daily cache now spans all 38 seed ipo event windows" in loop_report.lower().replace("\n", " ")
    assert "about 1.98" in loop_report.lower()
    assert "million parsed rows" in loop_report.lower()
    assert "segment-wise monthly workbook sections into a local collection manifest" in loop_report.lower().replace("\n", " ")
    assert "only the umbrella historical reports - capital market family remains manifest-only" in loop_report.lower().replace("\n", " ")
    assert "data/direct_market_history_collection_manifest.csv" in loop_report
    assert "consolidate the 38-event raw nse cache into a direct liquidity panel" in next_queue.lower()
    assert "re-run the pilot, regime-control, sector-conditioned, sector-adjusted, gradient, and stability passes on the direct panel" in next_queue.lower().replace("\n", " ")
    assert "sample the remaining `historical reports - capital market` archive family" in next_queue.lower()
    assert "keep `define_trade_rules` blocked until pull, release, monotonicity, robustness, and direct-window coverage all pass" in next_queue.lower().replace("\n", " ")
    regime_panel = (root / "reports" / "pilot_regime_control_panel.md").read_text(encoding="utf-8")
    assert "Sector History Expansion" in sector_history
    assert "sector-return and sector-turnover proxy panel" in sector_history.lower()
    assert "expanded-parent industry map" in sector_history.lower()
    assert "Sector-Conditioned Event Study" in sector_conditioned
    assert "Sector mapping is available for 26 of the 38 seed IPO symbols" in sector_conditioned
    assert "sector-adjusted same-sector peer averages stay mixed" in sector_conditioned.lower()
    assert "0.005879" in sector_conditioned
    assert "-0.007388" in sector_conditioned
    assert "-0.007810" in sector_conditioned
    assert "0.006850" in sector_conditioned
    assert len(sector_conditioned_rows) == 950
    assert len({row["symbol_after_listing"] for row in sector_conditioned_rows}) == 38
    assert len({row["symbol_after_listing"] for row in sector_conditioned_rows if row["sector_covered"] == "True"}) == 26
    assert "Sector-Adjusted Basket Event Study" in sector_adjusted
    assert "sector-adjusted basket pass therefore covers 650 of the 950 pilot rows" in sector_adjusted.lower()
    assert "sector-adjusted basket averages remain mixed across application and release windows" in sector_adjusted.lower()
    assert "0.011310" in sector_adjusted
    assert "-0.012608" in sector_adjusted
    assert "-0.013788" in sector_adjusted
    assert "0.013891" in sector_adjusted
    assert "0.001360" in sector_adjusted
    assert "0.005264" in sector_adjusted
    assert len(sector_adjusted_rows) == 950
    assert len({row["symbol_after_listing"] for row in sector_adjusted_rows}) == 38
    assert len({row["symbol_after_listing"] for row in sector_adjusted_rows if row["sector_covered"] == "True"}) == 26
    assert "Pressure Gradient Diagnostics" in gradient_report
    assert "Rows analyzed: 20 basket-window-study combinations." in gradient_report
    assert "Non-mixed pressure directions: 1." in gradient_report
    assert "Strong gradients with |Spearman rho| >= 0.8: 1." in gradient_report
    assert "sector_adjusted" in gradient_report
    assert "midcap150" in gradient_report
    assert "rho 1.0" in gradient_report.lower()
    assert "The only non-mixed row is sector_adjusted / release_5 / midcap150" in gradient_report
    assert len(gradient_rows) == 20
    assert len({row["study_type"] for row in gradient_rows}) == 2
    assert any(
        row["study_type"] == "sector_adjusted"
        and row["window_name"] == "release_5"
        and row["basket_name"] == "midcap150"
        and row["pressure_direction"] == "nondecreasing"
        and row["pressure_spearman_rho"] == "1.0"
        for row in gradient_rows
    )
    assert "Pressure Gradient Stability" in stability_report
    assert "Rows analyzed: 15 stability combinations." in stability_report
    assert "Midcap150 rows analyzed: 10." in stability_report
    assert "Non-mixed midcap150 rows: 3." in stability_report
    assert "Non-mixed release_5 sector-adjusted baskets: 1." in stability_report
    assert "clean sector-adjusted midcap150 release_5 case does not generalize to adjacent windows" in stability_report.lower()
    assert "release_5 basket neighborhood remains mixed outside midcap150" in stability_report.lower()
    assert len(stability_rows) == 15
    assert len({row["section"] for row in stability_rows}) == 2
    assert sum(row["section"] == "midcap_path" for row in stability_rows) == 10
    assert sum(row["section"] == "basket_neighborhood" for row in stability_rows) == 5
    assert any(
        row["section"] == "midcap_path"
        and row["study_type"] == "sector_adjusted"
        and row["window_name"] == "release_5"
        and row["basket_name"] == "midcap150"
        and row["pressure_direction"] == "nondecreasing"
        and row["pressure_spearman_rho"] == "1.0"
        for row in stability_rows
    )
    assert "volatile bucket" in regime_panel.lower()
    assert "same-sector peers remain split" in regime_panel.lower()
    assert "source-backed seed sample exists for thirty-eight" in review_pack
    assert "volatile bucket" in review_pack.lower()
    assert "sector-return / sector-turnover proxy panel" in review_pack.lower()
    assert "direct nse market-history source inventory" in review_pack.lower()
    assert "direct loader now normalizes the market-activity, security-wise price-volume, delivery-position, and fii/dii csv families" in review_pack.lower()
    assert "sector-adjusted same-sector" in review_pack.lower()
    assert "peer pass remains mixed on the 26 mapped ipo" in review_pack.lower()
    assert "broader sector-adjusted basket pass also remains mixed" in review_pack.lower()
    assert "pressure-gradient diagnostic adds one narrow sector-adjusted lead" in review_pack.lower()
    assert "stability pass shows that the lead does not generalize to adjacent windows" in review_pack.lower()
    assert len(seed_rows) == 38
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
    assert len(window_rows) == 190
    assert len(pilot_rows) == 950
    assert len(control_rows) == 950
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
