# Alpha101 Transfer Pack

## Purpose

Committed review pack for the current Alpha101 transfer scope across other
asset classes.

## Canonical Inputs

- `../project.json`
- `../reports/alpha101_transfer_scope.md`
- `../queues/indian_etfs_queue.yaml`
- `../queues/nse_indices_queue.yaml`
- `../queues/nse_equity_derivatives_queue.yaml`
- `../queues/mcx_queue.yaml`
- `../queues/macro_queue.yaml`
- `../queues/global_proxy_queue.yaml`

## State Snapshot

- Project status: `draft`
- Project phase: `alpha101 transfer lane scaffolding`
- Transfer scope: explicit and low-compute
- ETF lane: active
- NSE index lane: scaffolded
- NSE derivative lane: scaffolded
- MCX continuous-contract lane: scaffolded
- Macro, FX, and global proxy lanes: research-only

## Decision

- Keep the ETF transfer lane as the first executable path.
- Keep index, derivative, and MCX lanes explicit but scaffolded.
- Keep proxy lanes research-only and non-authoritative.
- Do not promote cross-asset transfer on scope alone.
