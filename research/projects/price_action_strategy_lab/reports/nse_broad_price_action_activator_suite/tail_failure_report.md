# Tail Failure Report

## Variant Diagnostics

| variant | fold_count | mean_return_pct | mean_delta_vs_baseline_pct | delta_ci_low_pct | delta_ci_high_pct | paired_t_stat | paired_p_value | left_tail_delta_pct | right_tail_retention | negative_fold_rate | worse_than_baseline_rate | sharpe_delta | max_drawdown_delta_pct | tail_decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| drawdown_only_throttle | 24 | 0.9804 | -0.0344 | -0.2123 | 0.1411 | -0.3190 | 0.7526 | 0.6102 | 0.9301 | 0.3750 | 0.4583 | 0.1351 | 0.2717 | research_only_not_significant |
| soft_aggressive | 24 | 0.9524 | -0.0625 | -0.2444 | 0.1155 | -0.5741 | 0.5714 | 0.5164 | 0.9246 | 0.3333 | 0.5000 | 0.0880 | 0.1552 | research_only_not_significant |
| baseline | 24 | 1.0148 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 1.0000 | 0.3750 | 0.0000 | 0.0000 | 0.0000 | control |
| soft_conservative | 24 | 0.7435 | -0.2714 | -0.7728 | 0.2201 | -0.9070 | 0.3738 | 1.5856 | 0.7213 | 0.3750 | 0.5417 | -0.1547 | 0.6454 | reject_loses_right_tail |
| hard_gate | 24 | 0.4900 | -0.5248 | -1.5218 | 0.4562 | -0.8791 | 0.3884 | 3.1984 | 0.4487 | 0.4583 | 0.5417 | -1.3009 | 1.2821 | reject_loses_right_tail |

## Alpha-Level Tail Candidates

_No rows._

## Gate Concentration In Baseline Tail Folds

| tail_bucket | indicator | side | selection_count | unique_alphas | unique_folds | mean_score | mean_lift_bps | mean_on_return_bps | mean_off_return_bps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| left_tail | gap_fade | low | 26 | 16 | 4 | 60.5675 | 32.6146 | 34.6168 | 2.0022 |
| left_tail | volatility_expansion | high | 24 | 15 | 5 | 78.7479 | 45.4980 | 48.4127 | 2.9147 |
| left_tail | volume_acceptance | low | 21 | 19 | 5 | 79.8155 | 49.1262 | 63.9688 | 14.8425 |
| left_tail | volatility_compression | high | 18 | 14 | 5 | 50.9384 | 24.6248 | 21.6934 | -2.9314 |
| left_tail | oscillator_extreme | high | 12 | 9 | 3 | 50.8138 | 25.4447 | 23.6864 | -1.7584 |
| left_tail | gap_continuation | high | 8 | 8 | 2 | 45.8228 | 22.3253 | 18.2976 | -4.0277 |
| left_tail | breadth_risk_off | high | 7 | 6 | 2 | 59.2056 | 27.9563 | 23.2160 | -4.7403 |
| left_tail | volatility_compression | low | 7 | 6 | 5 | 56.6469 | 32.2460 | 23.3376 | -8.9084 |
| left_tail | relative_strength_leader | high | 6 | 6 | 1 | 59.5967 | 40.3926 | 52.7830 | 12.3903 |
| left_tail | gap_continuation | low | 3 | 3 | 1 | 43.1169 | 20.5115 | 25.6072 | 5.0957 |

## Interpretation

- `left_tail_delta_pct` is variant return minus baseline return on baseline bottom-quartile folds.
- `right_tail_retention` is variant mean return divided by baseline mean return on baseline top-quartile folds.
- `delta_ci_low_pct` is a deterministic bootstrap 5% lower bound for paired fold return deltas.
- Promotion requires left-tail improvement, at least 85% right-tail retention, and positive lower CI.

## External Hypotheses To Test Next

- Volatility scaling: test NIFTY realized volatility and India VIX as soft exposure inputs.
- Liquidity stress: test Amihud-style illiquidity and traded-value collapse before drawdown folds.
- Breadth/trend stress: test broad selloff breadth, index drawdown, and NIFTY trend state.
- News/event clues: tag January 2025, July 2025, and February 2026 drawdown folds before use.
- These are hypothesis-generation inputs only; every feature needs lagged, purged OOS validation.