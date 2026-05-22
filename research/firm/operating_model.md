# Operating Model

## Flow

1. Queue work is recorded in `research_queue.json`.
2. `daily_research_state.json` is the daily snapshot.
3. Role queue docs translate the JSON queue into bounded work.
4. Validation produces review packs before promotion.
5. Only state files, CSVs, and review packs are canonical.

## Roles

| Role | Ownership |
| --- | --- |
| VP Research / Alpha PM | Alpha queue priority, promotion gates, blocker decisions |
| VP Data & Platform | Data-source readiness, contracts, schema gates |
| Associate Data Source | Source registry, adapters, sample loads, quality reports |
| Associate Asset Class | Universes, symbol mapping, calendars, rolling rules |
| Associate Math & Alpha Tools | Deterministic transforms, neutralization, validation helpers |
| Associate Validation & Research Ops | Review packs, reports, state sync, release evidence |

## Promotion Gate

- Evidence pack exists.
- Capacity audit exists.
- Out-of-sample result exists.
- Blocker status is explicit.
- Source and contract fit the lane.

## Blocking Rule

- Proxy VWAP stays blocked until real VWAP data exists.
- Snapshot-industry lanes stay blocked until point-in-time history exists.
- Broad-universe claims stay blocked until they survive capacity and liquidity checks.
- Notebook outputs are not canonical until committed as reviewable packs.
