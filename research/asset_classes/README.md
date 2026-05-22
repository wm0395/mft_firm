# Asset Class Registry

This directory is the research-only definition of the initial multi-asset
expansion lanes. It is a control file set, not a production claim.

## Scope

- Indian equities
- Indian ETFs
- NSE indices
- NSE equity derivatives
- MCX commodities
- Macro series
- FX proxy lanes
- Global ETF proxy lanes

## Reading Rules

- `asset_class_registry.yaml` is the index.
- Each lane file is the detailed contract and symbol mapping definition.
- `source_priority_order` is conservative fallback order, not an endorsement.
- `canonical_symbol_format` is the internal namespace used by research code.
- `benchmark` is a comparison anchor, not a trading promise.
- `point_in_time_metadata_status` shows whether PIT metadata is required.
- `contract_model` sections define roll and continuity assumptions explicitly.

## Files

- `asset_class_registry.yaml`
- `indian_equities_liquid.yaml`
- `indian_etfs.yaml`
- `nse_indices.yaml`
- `mcx_commodities.yaml`
- `macro_series.yaml`

Notes:

- `nse_equity_derivative` is tracked in the registry and reviewed via
  `nse_indices.yaml`.
- `fx_proxy` and `global_etf_proxy` are tracked in the registry and reviewed
  via `macro_series.yaml`.

## Non-Goals

- No production readiness claims.
- No hidden source assumptions.
- No blanket source approval.
