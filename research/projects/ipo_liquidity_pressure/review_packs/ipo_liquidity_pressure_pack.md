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

## State Snapshot

- Project status: `draft`
- Phase: `pilot evidence collection and seed event study`
- Scope: mainboard IPO liquidity pressure and post-allotment reinvestment
- Metrics: event-window abnormal return, pressure bucket effect, and reversal
  classification
- Research stance: no deployment claim yet
- Current evidence: source-backed seed sample exists for Urban Company,
  Rubicon Research, Canara Robeco, Canara HSBC Life Insurance, LG
  Electronics, Medi Assist Healthcare Services, Euro Pratik Sales, Yatra
  Online, TruAlt Bioenergy, Saatvik Green Energy, Sudeep Pharma,
  Om Freight Forwarders, Brigade Hotel Ventures, Glottis, Fabtech
  Technologies, Lenskart Solutions, One 97 Communications, Delhivery,
  Niva Bupa Health Insurance, Sagility, Ather Energy, Schloss Bangalore,
  HDB Financial Services, Travel Food Services, Aegis Vopak Terminals,
  Afcons Infrastructure, NTPC Green Energy, and Vishal Mega Mart; the
  pilot event study is mixed; and the regime-control panel leaves the
  sample in the volatile bucket without producing a clean gradient.

## Decision

- Keep mainboard IPOs separate from SME IPOs in the first pass.
- Keep pull and release models separate.
- Require no-lookahead event features.
- Require a mechanism, pull, release, tradability, and robustness gate before
  any strategy file is written.
