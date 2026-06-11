# IPO Liquidity Pressure Pack

## Purpose

Committed review pack for the IPO liquidity pressure project. It captures the
scope, data contract, event design, and validation gates before any result
exists.

## Canonical Inputs

- `../project.json`
- `../README.md`
- `../research_state.json`
- `../reports/mechanism_and_hypotheses.md`
- `../reports/data_contract.md`
- `../reports/event_design.md`
- `../reports/validation_framework.md`
- `../reports/market_history_expansion.md`
- `../reports/direct_market_history_sources.md`
- `../reports/direct_market_history_loader.md`
- `../reports/sector_history_expansion.md`
- `../reports/sector_conditioned_event_study.md`
- `../reports/sector_adjusted_basket_event_study.md`
- `../reports/pressure_gradient_diagnostics.md`
- `../reports/pressure_gradient_stability.md`

## State Snapshot

- Project status: `draft`
- Phase: `pilot evidence collection, seed event study, and market-history expansion`
- Scope: mainboard IPO liquidity pressure and post-allotment reinvestment
- Metrics: event-window abnormal return, pressure bucket effect, and reversal
  classification
- Research stance: no deployment claim yet
- Current evidence: source-backed seed sample exists for thirty-eight
  mainboard IPOs; the pilot event study is mixed; the regime-control panel
  leaves the sample in the volatile bucket without producing a clean
  gradient; the market-history panel is available as a proxy-based
  conditioning layer; a sector-return / sector-turnover proxy panel is now
  available for same-sector conditioning; the direct NSE market-history source inventory has identified the archive families for turnover, delivery, category flow, mode of trading, and FII/DII activity; the direct loader now normalizes the market-activity, security-wise price-volume, delivery-position, and FII/DII CSV families into a local collection manifest; and the sector-adjusted same-sector peer pass remains mixed on the 26 mapped IPOs. The broader sector-adjusted basket pass also remains mixed across the application and release windows.
  The pressure-gradient diagnostic adds one narrow sector-adjusted lead: the midcap150 basket in the release_5 window orders low to extreme with Spearman rho 1.0, but the rest of the combinations remain mixed. The stability pass shows that the lead does not generalize to adjacent windows and that the release-window basket neighborhood remains mixed outside midcap150.

## Decision

- Keep mainboard IPOs separate from SME IPOs in the first pass.
- Keep pull and release models separate.
- Require no-lookahead event features.
- Require a mechanism, pull, release, tradability, and robustness gate before
  any strategy file is written.
