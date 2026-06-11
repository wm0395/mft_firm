# External Stress Diagnostic Report

Status: research-only data diagnostic. No trading gate was created.

## Summary
- Available feature count: `9`
- Missing feature count: `9`
- Shortlisted diagnostic features: `7`

## Candidate Shortlist
| feature | stress_side | weak_mean | normal_mean | weak_median | normal_median | standardized_difference | abs_standardized_difference | rank_biserial | auc | oriented_auc | precision_top_decile | recall_top_decile | false_positive_folds | false_negative_weak_folds | missing_pct | status | abs_corr_to_breadth |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| advance_decline_ratio_lag1 | low | 0.4356 | 0.4729 | 0.4303 | 0.4771 | -1.5592 | 1.5592 | -0.7222 | 0.1389 | 0.8611 | 0.6667 | 0.3333 | 1 | 4 | 0.0003 | available | 0.3679 |
| nifty_return_5d_lag1 | low | -0.0046 | 0.0041 | -0.0032 | 0.0065 | -0.9397 | 0.9397 | -0.4630 | 0.2685 | 0.7315 | 0.6667 | 0.3333 | 1 | 4 | 0.0009 | available | 0.1265 |
| advance_decline_ratio_5d_lag1 | low | 0.4530 | 0.4963 | 0.4518 | 0.5107 | -0.8133 | 0.8133 | -0.4630 | 0.2685 | 0.7315 | 0.3333 | 0.1667 | 2 | 5 | 0.0001 | available | 0.2498 |
| sector_dispersion_20d_lag1 | low | 0.1270 | 0.1469 | 0.1245 | 0.1407 | -0.6724 | 0.6724 | -0.3333 | 0.3333 | 0.6667 | 0.6667 | 0.3333 | 1 | 4 | 0.0028 | available | 0.0001 |
| breadth_risk_off_lag1 | high | 0.0505 | 0.0259 | 0.0345 | 0.0125 | 0.5721 | 0.5721 | 0.0833 | 0.5417 | 0.5417 | 0.3333 | 0.1667 | 2 | 5 | 0.0001 | available | 1.0000 |
| sector_dispersion_5d_lag1 | low | 0.0626 | 0.0669 | 0.0635 | 0.0659 | -0.5672 | 0.5672 | -0.2593 | 0.3704 | 0.6296 | 0.3333 | 0.1667 | 2 | 5 | 0.0008 | available | 0.0023 |
| market_traded_value_zscore_20d_lag1 | low | -0.1636 | 0.0086 | -0.2287 | 0.0278 | -0.4870 | 0.4870 | -0.3148 | 0.3426 | 0.6574 | 0.3333 | 0.1667 | 2 | 5 | 0.0007 | available | 0.0163 |

## Coverage
| feature | source | available | missing_pct | status |
| --- | --- | --- | --- | --- |
| india_vix_level_lag1 | india_vix | False | 1.0000 | missing_source |
| india_vix_1d_change_lag1 | india_vix | False | 1.0000 | missing_source |
| india_vix_5d_change_lag1 | india_vix | False | 1.0000 | missing_source |
| fpi_equity_flow_1d_lag1 | fpi_equity_flows | False | 1.0000 | missing_source |
| fpi_equity_flow_5d_lag1 | fpi_equity_flows | False | 1.0000 | missing_source |
| fpi_equity_flow_20d_lag1 | fpi_equity_flows | False | 1.0000 | missing_source |
| usdinr_1d_change_lag1 | usdinr | False | 1.0000 | missing_source |
| usdinr_5d_change_lag1 | usdinr | False | 1.0000 | missing_source |
| crude_5d_change_lag1 | crude_proxy | False | 1.0000 | missing_source |
| nifty_return_5d_lag1 | market_collector_equal_weight_nse | True | 0.0009 | available |
| nifty_drawdown_20d_lag1 | market_collector_equal_weight_nse | True | 0.0008 | available |
| nifty_drawdown_60d_lag1 | market_collector_equal_weight_nse | True | 0.0008 | available |
| sector_dispersion_5d_lag1 | market_collector_cross_section_proxy | True | 0.0008 | available |
| sector_dispersion_20d_lag1 | market_collector_cross_section_proxy | True | 0.0028 | available |
| market_traded_value_zscore_20d_lag1 | market_collector_nse_ohlcv | True | 0.0007 | available |
| advance_decline_ratio_lag1 | market_collector_nse_ohlcv | True | 0.0003 | available |
| advance_decline_ratio_5d_lag1 | market_collector_nse_ohlcv | True | 0.0001 | available |
| breadth_risk_off_lag1 | price_action_internal_activator | True | 0.0001 | available |

## Interpretation
External macro/flow series were not present in the local market-collector database. This run therefore validates available internal market-stress proxies and records unavailable sources explicitly.