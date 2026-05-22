# Alpha101 Research Brief

## Scope

This folder is the Alpha101 discovery and robustness triage lane for the MFT research stack. The work here uses cached adjusted OHLCV panels, train-only selection, and out-of-sample active-return checks against an equal-weight active-universe benchmark.

The operational data conventions are:

- `close` in formulas is adjusted close.
- `open`, `high`, and `low` are adjusted by the same close adjustment factor.
- `vwap` is a labeled proxy, not a native exchange VWAP, and is computed as typical price from adjusted OHLC.
- Universe membership is cached and current-snapshot based, so point-in-time membership risk remains a known constraint.

## Active Source-Of-Truth Files

These are the files that currently define the Alpha101 research behavior in this folder:

- [research/notebooks/alpha_001/alpha101_research_factory.ipynb](./alpha101_research_factory.ipynb)
- [research/notebooks/alpha_001/executed_alpha101_research_factory.ipynb](./executed_alpha101_research_factory.ipynb)
- [research/notebooks/alpha_001/research/alpha101_engine.py](./research/alpha101_engine.py)
- [research/notebooks/alpha_001/research/alpha101_formulas.py](./research/alpha101_formulas.py)
- [research/notebooks/alpha_001/research/alpha101_robustness.py](./research/alpha101_robustness.py)

The notebook is the narrative wrapper, while the three Python modules define the actual panel loading, Alpha101 formulas, and robustness selection logic.

## Exact-OHLCV Promoted Alpha Queue

The current promoted queue is the clean exact-OHLCV lane that survived train-only selection and was marked `promote_to_deeper_research`. All promoted items are on the `expanded` panel and use the `high_vol_top100` mask in the selected portfolio setup.

### Batch 1: Clean Exact-OHLCV Promotions

| alpha_id | median_test_active_sharpe | median_test_active_cagr | median_test_rank_ic | best_mask | best_signal_transform | best_strategy |
| --- | ---: | ---: | ---: | --- | --- | --- |
| alpha040 | 1.669713 | 0.028283 | 0.034546 | high_vol_top100 | winsor_zscore | overlay20 |
| alpha012 | 1.448578 | 0.026729 | 0.020490 | high_vol_top100 | ewm3 | ewm3_overlay20 |
| alpha024 | 1.441989 | 0.027489 | 0.039320 | high_vol_top100 | rank_centered | ewm5_overlay20 |
| alpha044 | 1.364653 | 0.022774 | 0.041260 | high_vol_top100 | ewm3 | overlay20 |
| alpha018 | 1.341600 | 0.024729 | 0.022731 | high_vol_top100 | ewm3 | ewm3_overlay20 |
| alpha023 | 1.268938 | 0.024179 | 0.029528 | high_vol_top100 | winsor_zscore | ewm5_overlay20 |
| alpha051 | 1.213014 | 0.023337 | 0.016318 | high_vol_top100 | winsor_zscore | ewm5_overlay20 |
| alpha049 | 1.205458 | 0.023193 | 0.017777 | high_vol_top100 | winsor_zscore | ewm5_overlay20 |
| alpha016 | 1.183597 | 0.021042 | 0.028471 | high_vol_top100 | ewm3 | overlay20 |
| alpha034 | 1.087923 | 0.018344 | 0.027965 | high_vol_top100 | ewm3 | ewm3_overlay20 |
| alpha022 | 1.004016 | 0.016076 | 0.020154 | high_vol_top100 | ewm3 | ewm3_overlay20 |

### Batch 2: Clean Near-Miss Exact-OHLCV Promotions

| alpha_id | median_test_active_sharpe | median_test_active_cagr | median_test_rank_ic | best_mask | best_signal_transform | best_strategy |
| --- | ---: | ---: | ---: | --- | --- | --- |
| alpha026 | 1.505659 | 0.026694 | 0.030148 | high_vol_top100 | winsor_zscore | overlay20 |
| alpha033 | 1.165859 | 0.021484 | 0.031767 | high_vol_top100 | ewm3 | ewm3_overlay20 |
| alpha013 | 1.137544 | 0.019149 | 0.022281 | high_vol_top100 | ewm3 | overlay20 |
| alpha015 | 1.086061 | 0.018113 | 0.022677 | high_vol_top100 | rank_centered | overlay20 |
| alpha003 | 0.941490 | 0.015570 | 0.011634 | high_vol_top100 | rank_centered | overlay20 |
| alpha045 | 0.904456 | 0.014872 | 0.014302 | high_vol_top100 | ewm3 | ewm3_overlay20 |
| alpha038 | 0.889312 | 0.017319 | 0.025777 | high_vol_top100 | winsor_zscore | ewm3_overlay20 |
| alpha068 | 0.881240 | 0.014694 | 0.015941 | high_vol_top100 | liquidity_scaled | overlay20 |
| alpha088 | 0.720715 | 0.013810 | 0.031329 | high_vol_top100 | rank_centered | overlay20 |
| alpha010 | 0.700723 | 0.012554 | 0.019535 | high_vol_top100 | ewm3 | ewm5_overlay20 |
| alpha037 | 0.677416 | 0.012192 | 0.015875 | high_vol_top100 | ewm3 | ewm3_overlay20 |
| alpha017 | 0.676792 | 0.012479 | 0.014812 | high_vol_top100 | winsor_zscore | ewm5_overlay20 |
| alpha004 | 0.664159 | 0.012152 | 0.022507 | high_vol_top100 | winsor_zscore | overlay20 |
| alpha006 | 0.659661 | 0.010592 | 0.013471 | high_vol_top100 | winsor_zscore | overlay20 |
| alpha007 | 0.633464 | 0.012497 | 0.018983 | high_vol_top100 | winsor_zscore | overlay20 |
| alpha055 | 0.615999 | 0.010129 | 0.020412 | high_vol_top100 | rank_centered | overlay20 |
| alpha009 | 0.542992 | 0.009590 | 0.024941 | high_vol_top100 | ewm3 | ewm3_overlay20 |

Batch totals in the executed notebook are 11 promotions for batch 1 and 17 promotions for batch 2, for 28 exact-OHLCV promoted names overall.

## Blocked Proxy And Snapshot Lanes

These lanes are explicitly not promoted:

- `proxy_vwap`: blocked until real VWAP data exists. The notebook treats proxy-VWAP signals as research-only because typical-price VWAP is not a clean substitute for production promotion.
- `snapshot_metadata_risk`: blocked until point-in-time industry metadata exists. Current industry-neutral work uses current constituent metadata and is not a PIT backtest.
- `missing_cap`: untestable with the current cache, so it is not part of the promoted queue.
- `baseline_alpha001`: retained as a reference lane, not part of the exact-OHLCV promotion queue.

## Next Research Steps

The notebook caveats point to a narrow next-step list:

1. Run a strict NaN-preserving formula pass so warmup gaps do not turn into synthetic signals.
2. Replace proxy VWAP with real VWAP before any proxy-dependent promotion.
3. Replace snapshot industry metadata with point-in-time industry snapshots before any industry-neutral promotion.
4. Audit selected-name forward returns, stale prices, warmup NaNs, and invalid returns before treating any promoted candidate as tradable.
5. Re-run the promoted exact-OHLCV queue after the liquidity-notional audit, using raw traded rupee volume for capacity checks.

## Key Conclusions

- The Alpha101 stack is currently a candidate-discovery and robustness-triage layer, not a production-ready promotion layer.
- The clean promoted queue is entirely exact-OHLCV and concentrated on the `expanded` panel.
- Proxy-VWAP and snapshot-industry lanes are intentionally blocked, not silently mixed into the promoted queue.
- The immediate correctness gate is data hygiene, not a new signal family.
