# Price Action Strategy Lab

This project is a research-only tinkering lab for NSE price-action work. It is
meant to make experimentation low-friction while keeping the deployable
research project separate from exploratory notebooks and local trials.

## Objective

Build a modular workflow for testing price-action ideas on the NSE
market-collector universe. The lab should let a researcher:

- load all available NSE stocks from market-collector-backed data,
- inspect individual charts before and after a signal fires,
- express the same alpha through multiple portfolio constructions,
- compare backtest modes and cost assumptions,
- try meta selector options with explicit abstention and reason codes,
- document each run so the work can be reproduced.

## Status

The current lab has a first runnable spine:

- project metadata and research state,
- market-collector NSE panel export through `project/data`,
- decorated alpha specs and an immutable alpha registry,
- 25 encoded alpha specs covering reversal, breakout, gap, structure,
  trend-following, and candlestick-pattern signals,
- cross-sectional, stock-local, and long-only expression modes,
- turnover-cost backtests,
- selector options with abstention and lower-bound gating,
- local chart packs using the existing OHLCV chart renderer,
- JSON-shaped `configs/lab_run.yaml` for one-command CSV signal-table runs.
- YAML `configs/nse_alpha_suite.yaml` for full-universe alpha-suite runs.

No production trading workflow is defined here. No result in this project is a
deployment claim.

## Encoded Alphas

The registry currently encodes these five core reversal alphas:

- `bollinger_percent_b_mean_reversion_20`
- `stochastic_mean_reversion_14`
- `williams_r_mean_reversion_14`
- `fisher_transform_reversal_10`
- `inverse_fisher_rsi_reversal_10`

The registry also exposes a broader price-action set for custom configs and
ad hoc research:

- breakout and squeeze variants:
  - `breakout_20`
  - `keltner_breakout_20`
  - `squeeze_breakout_20`
  - `relative_volume_breakout_20`
- trend-following variants:
  - `supertrend_direction_10`
  - `parabolic_sar_trend`
  - `chandelier_trend`
  - `multi_timeframe_confirmation`
- gap and structure variants:
  - `opening_gap_regime_score`
  - `support_resistance_position_20`
  - `support_trendline_position_20`
- candlestick-pattern variants:
  - `doji_reversal_score`
  - `engulfing_reversal_score`
  - `hammer_shooting_star_score`
  - `inside_outside_bar_score`
  - `piercing_dark_cloud_score`
- existing reversal/confirmation helpers:
  - `failed_breakout_score_20`
  - `failed_reversal_score`
  - `trend_volume_composite`
  - `hybrid_confirmation`

All 25 alphas are registered through decorated immutable specs in
`alpha_specs.py` plus `price_action_pattern_specs.py`. They are signal
definitions only. Performance depends on how the signal is expressed as
positions, what holding horizon is tested, and what cost model is applied.

## Expression Modes

Cross-section is not the only way to express these alphas. It is useful because
it compares stocks against the same trading date and naturally controls market
beta, but it can hide useful single-stock behavior and it needs enough active
names each day.

Current expression modes:

- `cross_sectional_quintile`: long high-ranked names and short low-ranked names
  on the same date.
- `time_series_threshold`: evaluate each stock against its own signal threshold;
  this is the stock-local version.
- `ranked_long_only`: hold only the high-ranked side; this is useful when short
  execution is not realistic.

For each alpha, compare all available modes before making a research decision.
A weak cross-sectional result does not automatically kill an alpha if the
stock-local or long-only expression has cleaner behavior after costs.

## NSE Alpha-Suite Run Shape

Use `configs/nse_alpha_suite.yaml` as the documented target profile for running
the five core reversal alphas across the full NSE market-collector universe.
The broader registry supports the additional price-action / candlestick
strategies above for custom runs. The intended run matrix is:

- Universe: all enabled NSE stocks from market-collector-backed repository data.
- Alphas: the five encoded reversal alphas listed above.
- Modes: `cross_sectional_quintile`, `time_series_threshold`,
  `ranked_long_only`.
- Horizons: at least `1`, `5`, and `10` trading days.
- Costs: compare zero-cost and realistic turnover-cost assumptions.
- Outputs: per-alpha summaries, mode comparison, alpha-mode matrix, selector
  table, chart index, and chart packs for selected symbols.

The current `run_lab.py` is the CSV signal-table runner. Use
`run_alpha_suite.py` for the full NSE alpha-suite path: load the NSE panel
through `project.data.market_collector_panel`, convert it to the
Alpha101-style panel, compute each alpha once, cache signals, then fan out
mode/horizon/cost backtests and validation reports.

The activator pass uses the same cached alpha signals but screens family-level
market-condition masks first, then reruns the backtests with the selected
activator per alpha family. Use `run_activator_suite.py` with
`configs/nse_broad_price_action_activator_suite.yaml` for that pass.

## Workflow

1. Import market-collector OHLCV into the repository with the existing data
   loader.
2. Build an NSE panel with `project.data.market_collector_panel`.
3. For direct alpha-suite research, run `PYTHONPATH=. .venv/bin/python -m research.projects.price_action_strategy_lab.run_alpha_suite research/projects/price_action_strategy_lab/configs/nse_alpha_suite.yaml`.
4. For the activator pass, run `PYTHONPATH=. .venv/bin/python -m research.projects.price_action_strategy_lab.run_activator_suite research/projects/price_action_strategy_lab/configs/nse_broad_price_action_activator_suite.yaml`.
5. For custom signal-table research, generate or provide a table with `date`, `symbol`, `ohlcv`,
   `signal`, `forward_return`, and optional `active`.
6. Choose expression modes, backtests, chart symbols, and selectors in
   `configs/lab_run.yaml`.
7. Run `PYTHONPATH=. .venv/bin/python research/projects/price_action_strategy_lab/run_lab.py --config research/projects/price_action_strategy_lab/configs/lab_run.yaml`.
8. Inspect chart packs and CSV outputs.
9. Promote only the evidence summary, not the exploratory code, into a review
   pack.

## Compute Plan

Full NSE runs should avoid recomputing the same panel and alpha frames.
The expected fast path is:

- Cache the loaded NSE OHLCV panel under a run-specific cache directory.
- Cache each alpha signal by alpha name, universe fingerprint, date range, and
  input field fingerprint.
- Compute an alpha signal once, then reuse it across all expression modes,
  horizons, costs, selectors, and chart packs.
- Parallelize independent alpha and backtest jobs with an explicit
  `max_workers` setting.
- Keep cache writes explicit and under `research/projects/price_action_strategy_lab`
  or another configured artifact directory.

GPU use is optional. The current lab stack is still pandas/numpy for signal
generation, but the runner now precomputes percentile-rank matrices once and
stores them under a backend-specific cache. If CuPy is available and
`gpu.enabled: true`, the rank-precompute step can run on GPU; otherwise it
falls back to CPU with the same outputs. The practical speedups still come
from caching, vectorized panel math, and CPU parallelism until more of the
indicator layer is ported.

The alpha-suite runner also emits validation artifacts when validation is
enabled in the suite config:

- `validation_folds.csv`
- `validation_summary.csv`
- `selector_results.csv`
- `research_audit.md`
- `embargo_failure_diagnosis.md`
- `selector_robustness.md`
- `alpha_suite_decision_report.md`

The activator-suite runner emits a lighter comparison set:

- `activator_screen.csv`
- `activator_selection.csv`
- `activator_backtests.csv`
- `run_summary.md`

## Modules Planned

### Universe

The universe layer consumes already-ingested market-collector data through
`project.data.market_collector_panel`. Research code must not access DuckDB or
repository internals directly.

Planned universe modes:

- `all_nse`
- `liquid_nse`
- `high_vol_nse`
- `custom_symbols`

### Chart Inspection

The chart workflow should make every signal visually inspectable by symbol. A
chart pack should show OHLCV, alpha events, entry and exit marks, active regime
labels, and selector reason codes where available.

### Alpha Expression Modes

Cross-sectional quintiles are only one expression of a signal. This lab should
also support time-series thresholds, event windows, long-only baskets,
short-only baskets, per-stock isolated tests, and regime-gated family tests.

### Backtest Modes

Backtests should be swappable from configuration. Planned modes include daily
rebalance, fixed holding period, threshold hysteresis, long-only basket,
long-short basket, per-stock isolated backtest, event study, and
walk-forward/purged/embargo validation.

### Meta Selectors

Selector experiments should remain explicit and observable. A selector should
return the chosen alpha, expression mode, symbols or basket, confidence,
abstain flag, lower-bound score, and reason codes.

## Constraints

- Research-only; no trade-engine or decision-layer promotion.
- No DB access outside `project/data/`.
- Immutable dataclasses only when Python implementation begins.
- No hidden state, singleton registries, runtime monkey patching, or implicit
  writes.
- No upward imports, layer skipping, or speculative abstractions.
- Config-driven runs should be reproducible from recorded artifacts.

## Current Outputs

The runner writes:

- `run_summary.md`
- `alpha_results.csv`
- `mode_comparison.csv`
- `alpha_mode_matrix.csv`
- `cache_events.csv`
- `selector_results.csv`
- `validation_folds.csv`
- `validation_summary.csv`
- `research_audit.md`
- `embargo_failure_diagnosis.md`
- `selector_robustness.md`
- `alpha_suite_decision_report.md`
- `chart_index.md`
- `activator_screen.csv`
- `activator_selection.csv`
- `activator_backtests.csv`
- per-symbol chart HTML and signal CSV files when `chart_symbols` are set

## Done Conditions For This Scaffold

- Required project files exist.
- Project metadata identifies this as `research_project:price_action_strategy_lab`.
- Configs document NSE market-collector universe expansion and tinkering modes.
- Reports and review packs have explicit placeholder documentation.
- Scaffold test passes.
