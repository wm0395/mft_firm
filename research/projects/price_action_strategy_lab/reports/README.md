# Reports

This directory is for generated research artifacts from the price-action
strategy lab.

Generated artifacts:

- `run_summary.md`
- `alpha_results.csv`
- `mode_comparison.csv`
- `alpha_mode_matrix.csv`
- `cache_events.csv`
- `selector_results.csv`
- `chart_index.md`

Reports are research-only. They should document the universe, alpha specs,
expression modes, backtest modes, selector options, costs, baselines, and chart
artifacts used in each run.

For full NSE alpha-suite runs, reports should also record:

- the market-collector universe fingerprint,
- the five encoded alpha names,
- every expression mode tested,
- every horizon and turnover-cost assumption,
- cache hit or miss counts by artifact type,
- `max_workers` and parallelism scope,
- whether GPU execution was disabled or enabled and why.
