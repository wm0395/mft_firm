# NSE Price-Action Alpha Research Review Memo

Date: 2026-06-10

Status: research-only. No alpha or gate is approved for capital deployment.

## Abstract

This research program studied whether a broad suite of NSE price-action and candlestick alphas can be improved by regime-aware blockers or soft exposure controls. The goal was not to invent a high-complexity model, but to preserve the right tail of the baseline alpha stack while reducing fat left-tail losses. We expanded the alpha registry, ran the strategies across the NSE universe, tested expression and gating modes, introduced walk-forward validation, added tail diagnostics, built a hypothesis book, applied strict falsification gates, and attributed weak folds to market/regime/news hypotheses.

The strongest return engine remains the ungated baseline. The best portfolio-level risk-throttle candidate is `drawdown_only_throttle`, which improved Sharpe from `2.19` to `2.40` and reduced max drawdown from `-15.27%` to `-13.03%`, but it did not beat baseline return and was not statistically significant. The best alpha-level lead is `doji_reversal_score + soft_aggressive`, with `+0.405%` mean fold delta and `+2.091%` left-tail improvement, but its lower confidence bound is negative and its right-tail retention is only `91.77%`. Under strict falsification, no candidate passed.

The research conclusion is therefore conservative: the baseline is a strong research alpha engine and a shadow-trading candidate, but not deployable without a validated risk layer. Current gates are informative bad-regime detectors, not approved alpha enhancers.

## Research Objective

The stated objective was to improve price-action alphas so that the system can deal with fat left tails without losing right tails. Operationally, this became:

- Accept good trade suggestions from the baseline alpha stack.
- Block or reduce exposure to bad trade suggestions.
- Identify market, regime, and news/event conditions under which each alpha underperforms.
- Establish statistical significance before promotion.
- Avoid overfit or overly complex solutions unless they prove robust under out-of-sample validation.

The decision standard was deliberately strict: a blocker is useful only if it reduces left-tail loss while preserving most of the right-tail return and surviving leakage-aware validation.

## Data And Universe

The current NSE run used the `price_action_strategy_lab` artifacts under:

```text
research/projects/price_action_strategy_lab/reports/nse_broad_price_action_activator_suite/
```

The intended source of truth is the `market-collector` DuckDB panel for NSE securities. The research run was configured around:

- Universe: broad NSE market-collector universe.
- Mode: `ranked_long_only`.
- Horizon: `10` trading days.
- Transaction cost: `10 bps`.
- Walk-forward train window: `126` trading days.
- Test window: `21` trading days.
- Step size: `21` trading days.
- Lookahead/purge: `10` days.
- Fold selection: latest `24` folds.
- GPU setting: enabled where supported; current GPU acceleration is mainly in rank-percentile signal construction.

The 25 encoded alphas in the broad pass were:

```text
bollinger_percent_b_mean_reversion_20
breakout_20
chandelier_trend
doji_reversal_score
engulfing_reversal_score
failed_breakout_score_20
failed_reversal_score
fisher_transform_reversal_10
hammer_shooting_star_score
hybrid_confirmation
inside_outside_bar_score
inverse_fisher_rsi_reversal_10
keltner_breakout_20
multi_timeframe_confirmation
opening_gap_regime_score
parabolic_sar_trend
piercing_dark_cloud_score
relative_volume_breakout_20
squeeze_breakout_20
stochastic_mean_reversion_14
supertrend_direction_10
support_resistance_position_20
support_trendline_position_20
trend_volume_composite
williams_r_mean_reversion_14
```

## Research Sequence

### 1. Baseline Alpha Suite

We first evaluated the baseline price-action alpha stack. The baseline was treated as the control and return engine. It uses the alpha signals directly in `ranked_long_only` mode over a 10-day horizon with 10 bps cost.

The baseline performed well on aggregate but had unacceptable left-tail episodes:

- 2-year OOS return: `25.01%`
- CAGR: `11.81%`
- Annualized volatility: `5.16%`
- Sharpe: `2.19`
- Max drawdown: `-15.27%`
- Negative fold rate: `37.50%`
- Worst fold Sharpe: `-26.26`

This established the main problem: the baseline is not weak, but it fails sharply in specific market states.

### 2. Broad Strategy Registry

We expanded the alpha registry beyond the initial five reversal/mean-reversion signals to include a broader set of price-action, breakout, trend, structure, volume, and candlestick-pattern strategies.

The broad registry allowed us to test whether the tail problem was isolated to a few oscillator reversal strategies or common across price-action families. The later weak-fold attribution showed that the worst episodes affected many families simultaneously, suggesting common market-state failure rather than isolated alpha bugs.

### 3. Indicator And Activator Layer

We encoded and tested a set of market-state activators, including:

- Trend alignment.
- Breakout environment.
- Mean-reversion environment.
- Volatility expansion.
- Volatility compression.
- Breadth thrust.
- Breadth risk-off.
- Gap continuation.
- Gap fade.
- Volume acceptance.
- Relative-strength leaders.
- Relative-strength laggards.
- Oscillator extreme states.

The early family-level activator tests showed promising in-sample lift in some alpha groups, but the gates were too coarse. A single family-level activator assumed all alphas in a family behave similarly, which the later alpha-level results contradicted.

### 4. Hard Gate And Soft Throttle Variants

We then tested five portfolio variants:

- `baseline`: always use baseline exposure.
- `hard_gate`: binary trade/do-not-trade gate.
- `soft_conservative`: milder exposure reduction.
- `soft_aggressive`: soft sizing that can reduce or increase exposure.
- `drawdown_only_throttle`: risk-control oriented throttle.

The key conceptual change was moving away from binary gating. The evidence showed that hard gates detected bad regimes but destroyed too much right-tail return. Soft throttles were more consistent with the goal: reduce exposure in hostile states without turning off the alpha engine entirely.

### 5. Walk-Forward Validation

We implemented walk-forward validation using rolling train/test folds:

```text
train: 126 trading days
test: 21 trading days
step: 21 trading days
lookahead/purge: 10 days
folds: 24 latest folds
horizon: 10 days
cost: 10 bps
```

For each fold:

1. Indicator gates were tuned only on the training window.
2. Selected indicators, sides, thresholds, and multipliers were frozen.
3. The fold was evaluated on the next unseen month.
4. Metrics were saved at both aggregate and per-alpha levels.

We also added caching and parallel execution improvements. The original process-pool walk-forward failed due to memory/pickling pressure on large panel objects, so fold execution was switched to thread-based parallelism, which completed the 24-fold run and produced per-alpha fold diagnostics.

### 6. Tail Diagnostics

We added tail diagnostics to separate return improvement from tail-risk improvement.

Definitions:

```text
mean_delta_vs_baseline = mean(variant_fold_return - baseline_fold_return)

left_tail_delta = mean(variant_return - baseline_return)
                  on baseline bottom-quartile folds

right_tail_retention = mean(variant_return)
                       on baseline top-quartile folds
                       divided by mean(baseline_return)
                       on the same folds

delta_ci_low / delta_ci_high = deterministic bootstrap 5% / 95% bounds
                               for paired fold return deltas

paired_p_value = paired fold-level t-test p-value
```

Promotion required positive left-tail improvement, high right-tail retention, and a positive lower confidence bound.

### 7. Alpha-Level Tail Diagnostics

After aggregate gates failed to prove a significant improvement, we emitted per-alpha fold metrics. This allowed us to identify narrower alpha-level leads instead of forcing a portfolio-wide gate.

The strongest leads were:

- `doji_reversal_score + soft_aggressive`
- `doji_reversal_score + drawdown_only_throttle`
- `inside_outside_bar_score + drawdown_only_throttle`
- oscillator reversal family + `soft_aggressive`
- `support_trendline_position_20 + soft_aggressive`

However, none passed statistical promotion.

### 8. Hypothesis Book

We then created an alpha-regime hypothesis book:

```text
alpha_regime_hypothesis_book.csv
alpha_regime_hypothesis_book.md
```

The hypothesis book ranks alpha x gate candidates by:

- Mean delta versus baseline.
- Left-tail improvement.
- Right-tail retention.
- Max drawdown improvement.
- Bootstrap lower CI.
- Paired p-value.
- Gate stability.
- Selected indicator and side.

Rows were classified as:

- `candidate_validate_next`
- `research_only_needs_significance`
- `reject_right_tail_loss`

Current result:

- Total hypotheses: `48`
- Research-only leads: `32`
- Right-tail-loss rejects: `16`
- Strictly promotable candidates: `0`

### 9. Strict Falsification Report

We then added a stricter falsification layer:

```text
alpha_regime_falsification_report.csv
alpha_regime_falsification_report.md
```

The strict acceptance bars were:

- Right-tail retention must be at least `95%`.
- Left-tail improvement must be positive.
- Bootstrap lower CI must be positive.
- Paired p-value must be below `0.05`.
- Top indicator selection rate must be at least `50%`.
- Hard-gate form is not acceptable as a main engine.

No row passed.

### 10. Weak-Fold Event Attribution

Finally, we added weak-fold event attribution:

```text
weak_fold_event_attribution.csv
weak_fold_event_attribution.md
```

This report identifies bottom-20% baseline alpha-folds and tags them with:

- Fold date window.
- Affected alpha.
- Baseline return and drawdown.
- Selected indicator and side.
- Explanatory event hypothesis.
- Source URL.

These event labels are explanatory only. They are not model inputs and cannot be promoted without timestamped, lagged, purged OOS testing.

## Main Results

### Aggregate Walk-Forward Results

| variant | return_pct | cagr_pct | ann_vol_pct | ann_sharpe | max_drawdown_pct | latest_fold_sharpe | negative_fold_rate | worst_fold_sharpe | avg_exposure_multiplier | active_day_pct | turnover |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 25.0073 | 11.8066 | 5.1578 | 2.1899 | -15.2708 | 4.6212 | 0.3750 | -26.2606 | 1.0000 | 100.0000 | 0.0371 |
| hard_gate | 11.9293 | 5.7966 | 2.6352 | 2.1516 | -4.9715 | 4.9955 | 0.4583 | -21.4786 | 0.2937 | 93.4524 | 0.0103 |
| soft_conservative | 18.3301 | 8.7796 | 3.6336 | 2.3345 | -9.5077 | 4.9547 | 0.3750 | -26.0020 | 0.6469 | 100.0000 | 0.0237 |
| soft_aggressive | 23.5660 | 11.1602 | 4.8389 | 2.2111 | -12.8543 | 4.6656 | 0.3333 | -25.2624 | 0.8914 | 100.0000 | 0.0331 |
| drawdown_only_throttle | 24.4552 | 11.5595 | 4.6067 | 2.3980 | -13.0310 | 4.0221 | 0.3750 | -25.2279 | 0.8739 | 100.0000 | 0.0325 |

Interpretation:

- The baseline remains the strongest return engine.
- `drawdown_only_throttle` has the best risk-adjusted profile, with Sharpe `2.3980`, lower volatility, and improved max drawdown.
- `soft_aggressive` reduces negative-fold rate from `37.50%` to `33.33%`.
- Hard gating reduces drawdown but destroys return.

### Aggregate Tail Diagnostics

| variant | mean_delta_vs_baseline_pct | delta_ci_low_pct | delta_ci_high_pct | paired_p_value | left_tail_delta_pct | right_tail_retention | sharpe_delta | max_drawdown_delta_pct | tail_decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| drawdown_only_throttle | -0.0344 | -0.2123 | 0.1411 | 0.7526 | 0.6102 | 0.9301 | 0.1351 | 0.2717 | research_only_not_significant |
| soft_aggressive | -0.0625 | -0.2444 | 0.1155 | 0.5714 | 0.5164 | 0.9246 | 0.0880 | 0.1552 | research_only_not_significant |
| baseline | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | control |
| soft_conservative | -0.2714 | -0.7728 | 0.2201 | 0.3738 | 1.5856 | 0.7213 | -0.1547 | 0.6454 | reject_loses_right_tail |
| hard_gate | -0.5248 | -1.5218 | 0.4562 | 0.3884 | 3.1984 | 0.4487 | -1.3009 | 1.2821 | reject_loses_right_tail |

Interpretation:

- `drawdown_only_throttle` and `soft_aggressive` improve the left tail but do not improve mean return.
- Both confidence intervals cross zero.
- Both p-values are far above significance.
- `hard_gate` and `soft_conservative` are rejected because they lose too much right-tail return.

### Best Alpha-Level Leads

| alpha | variant | mean_delta_vs_baseline_pct | delta_ci_low_pct | paired_p_value | left_tail_delta_pct | right_tail_retention | max_drawdown_delta_pct | tail_decision |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| doji_reversal_score | soft_aggressive | 0.4052 | -0.0320 | 0.1771 | 2.0907 | 0.9177 | 0.7287 | research_only_not_significant |
| doji_reversal_score | drawdown_only_throttle | 0.3186 | -0.0528 | 0.2062 | 1.5546 | 0.9173 | 0.6274 | research_only_not_significant |
| inside_outside_bar_score | drawdown_only_throttle | 0.1638 | -0.1486 | 0.4237 | 1.2680 | 0.9185 | 0.4709 | research_only_not_significant |
| stochastic_mean_reversion_14 | soft_aggressive | 0.1543 | -0.1497 | 0.4373 | 0.9871 | 0.9781 | 0.3990 | research_only_not_significant |
| williams_r_mean_reversion_14 | soft_aggressive | 0.1543 | -0.1497 | 0.4373 | 0.9871 | 0.9781 | 0.3990 | research_only_not_significant |
| fisher_transform_reversal_10 | soft_aggressive | 0.1519 | -0.1677 | 0.4646 | 1.0257 | 0.9555 | 0.4143 | research_only_not_significant |
| bollinger_percent_b_mean_reversion_20 | soft_aggressive | 0.1398 | -0.2697 | 0.5749 | 1.3278 | 0.9339 | 0.4891 | research_only_not_significant |
| support_trendline_position_20 | soft_aggressive | 0.1360 | -0.2131 | 0.5444 | 1.0306 | 0.9608 | 0.3065 | research_only_not_significant |

Interpretation:

- `doji_reversal_score + soft_aggressive` is the best single alpha-level lead.
- Some oscillator alphas preserve the right tail better, but their significance remains weak.
- None of these rows has a positive lower confidence bound.

### Falsification Results

| falsification_status | count |
| --- | ---: |
| falsified_right_tail_loss | 35 |
| not_significant | 13 |

Interpretation:

- No hypothesis passed strict falsification.
- Most rows failed because right-tail retention was below the strict `95%` threshold.
- The remaining rows failed because they were not statistically significant.

### Gate Stability

| alpha | fold_count | unique_indicators | top_indicator | top_indicator_rate | activate_rate |
| --- | ---: | ---: | --- | ---: | ---: |
| inside_outside_bar_score | 24 | 9 | volatility_compression | 0.3333 | 0.9167 |
| doji_reversal_score | 24 | 7 | volatility_compression | 0.2917 | 0.9167 |
| bollinger_percent_b_mean_reversion_20 | 24 | 8 | gap_fade | 0.2917 | 0.9167 |
| support_trendline_position_20 | 24 | 6 | volatility_expansion | 0.2917 | 0.9167 |
| fisher_transform_reversal_10 | 24 | 8 | gap_fade | 0.2500 | 0.9167 |
| stochastic_mean_reversion_14 | 24 | 9 | gap_fade | 0.2500 | 0.9167 |
| williams_r_mean_reversion_14 | 24 | 9 | gap_fade | 0.2500 | 0.9167 |

Interpretation:

- Gate selection is unstable.
- Key alpha leads select 6 to 9 unique indicators across 24 folds.
- Top-indicator rates are only about 25% to 33%.
- This is consistent with weak fold-specific fitting rather than a stable causal regime relation.

## Weak-Fold Attribution

We attributed the bottom-20% baseline alpha-folds to event hypotheses.

| event_label | count |
| --- | ---: |
| early_2025_broad_correction_fpi_outflows | 45 |
| unmatched | 38 |
| feb_2026_it_global_tech_selloff | 26 |
| july_2025_broad_based_selling | 11 |

Worst weak folds:

| fold | alpha | test_start | test_end | return_pct | max_drawdown_pct | event_label | selected_indicator | selected_side |
| --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| 342 | support_trendline_position_20 | 2025-01-31 | 2025-03-02 | -11.8756 | -11.3547 | early_2025_broad_correction_fpi_outflows | volume_acceptance | high |
| 342 | bollinger_percent_b_mean_reversion_20 | 2025-01-31 | 2025-03-02 | -11.6802 | -11.4183 | early_2025_broad_correction_fpi_outflows | breadth_risk_off | high |
| 342 | stochastic_mean_reversion_14 | 2025-01-31 | 2025-03-02 | -11.6640 | -11.5226 | early_2025_broad_correction_fpi_outflows | breadth_risk_off | high |
| 342 | williams_r_mean_reversion_14 | 2025-01-31 | 2025-03-02 | -11.6640 | -11.5226 | early_2025_broad_correction_fpi_outflows | breadth_risk_off | high |
| 342 | doji_reversal_score | 2025-01-31 | 2025-03-02 | -11.6403 | -11.5286 | early_2025_broad_correction_fpi_outflows | gap_fade | low |
| 342 | inverse_fisher_rsi_reversal_10 | 2025-01-31 | 2025-03-02 | -11.6255 | -11.5273 | early_2025_broad_correction_fpi_outflows | volatility_expansion | high |
| 335 | engulfing_reversal_score | 2024-07-02 | 2024-07-31 | -11.5096 | -11.2823 | unmatched | volatility_compression | high |
| 342 | fisher_transform_reversal_10 | 2025-01-31 | 2025-03-02 | -11.3393 | -11.0904 | early_2025_broad_correction_fpi_outflows | breadth_risk_off | high |
| 342 | parabolic_sar_trend | 2025-01-31 | 2025-03-02 | -11.1292 | -10.5225 | early_2025_broad_correction_fpi_outflows | breadth_risk_off | high |
| 354 | inverse_fisher_rsi_reversal_10 | 2026-02-08 | 2026-03-09 | -10.7733 | -10.7823 | feb_2026_it_global_tech_selloff | relative_strength_leader | low |

Interpretation:

- The worst failures were clustered, not random isolated alpha events.
- Early 2025 broad correction/FPI outflow stress was the dominant identified weak cluster.
- February 2026 IT/global-tech stress was the second major cluster.
- A meaningful unmatched cluster remains and needs further attribution.

## Published Research And Market Context

The research direction is consistent with several established ideas:

1. Volatility-managed portfolios.

Moreira and Muir show that scaling down exposure when volatility is high can improve factor Sharpe ratios because volatility changes are not necessarily offset by proportional changes in expected returns. This supports testing realized-volatility and implied-volatility throttles, but not deploying them without OOS validation. Source: [NBER Working Paper 22208](https://www.nber.org/papers/w22208).

2. Momentum and factor crashes.

Daniel and Moskowitz show that factor crashes can be partly forecastable around panic, bear-market, high-volatility, and rebound states. While our alphas are price-action/candlestick alphas rather than classical momentum, the same warning applies: regimes can dominate signal behavior. Source: [NBER Momentum Crashes paper](https://www.nber.org/system/files/working_papers/w20439/w20439.pdf).

3. Liquidity stress.

Amihud-style illiquidity uses the ratio of absolute return to trading value as a simple liquidity proxy. This motivates testing liquidity stress and traded-value collapse as potential alpha-hostile states. Source: [Amihud illiquidity paper](https://www.cis.upenn.edu/~mkearns/finread/amihud.pdf).

4. India VIX.

India VIX is NSE's volatility index based on NIFTY option prices and represents expected near-term market volatility. This motivates adding India VIX level/change as an external stress input, but only after timestamped ingestion and lagged OOS testing. Source: [NSE India VIX white paper](https://nsearchives.nseindia.com/web/sites/default/files/inline-files/white_paper_IndiaVIX.pdf).

5. Early 2025 Indian equity stress.

NSE Market Pulse reports around early 2025 and market commentary identify FPI outflows and broad market stress as relevant explanatory context. Source: [NSE Market Pulse publications](https://www.nseindia.com/static/research/publications-reports-nse-market-pulse), [Times of India FPI outflow report](https://timesofindia.indiatimes.com/business/india-business/fpi-outflows-stands-at-rs-1-12-lakh-crore-in-2025-sell-rs-34574-crore-worth-equities-in-february/articleshow/118662025.cms).

6. February 2026 IT/global-tech stress.

Indian IT stocks sold off sharply during February 2026 amid global tech/AI disruption concerns. This aligns with one of the major weak-fold clusters. Sources: [Moneycontrol IT selloff](https://www.moneycontrol.com/news/business/markets/infosys-ltimindtree-tcs-other-it-stocks-plunge-6-amid-global-tech-selloff-here-s-why-13809833.html), [Times of India AI-fears IT drawdown](https://timesofindia.indiatimes.com/business/india-business/ai-fears-wipe-rs-6-lakh-crore-off-it-stocks-how-tcs-infosys-and-other-it-firms-are-shifting-strategy/articleshow/128411278.cms).

## Decisions Made

### Decision 1: Keep baseline as the main research control.

The baseline remains the best return engine. It is not deployment-ready, but it is the benchmark every blocker must beat.

### Decision 2: Reject hard gating as the main solution.

Hard gating improved drawdown but retained only `44.87%` of right-tail return. This violates the core objective.

### Decision 3: Treat soft throttles as research-only risk controls.

`drawdown_only_throttle` and `soft_aggressive` reduce left-tail damage, but neither produces statistically significant OOS improvement.

### Decision 4: Focus on per-alpha blocker hypotheses.

Portfolio-wide gates are too coarse. The most useful signals appear to be alpha-specific, especially around `doji_reversal_score`, oscillator reversal alphas, `inside_outside_bar_score`, and `support_trendline_position_20`.

### Decision 5: Add hypothesis-book and falsification layers.

Instead of continuing broad gate-shopping, we now track hypotheses explicitly and reject them unless they pass strict evidence requirements.

### Decision 6: Use news/event attribution only as explanation.

Event labels explain weak folds but are not allowed to become trading features without lagged, timestamped, purged OOS validation.

## Current Best Achievement

The best research achievement is not a deployable alpha. It is a validated research framework that:

- Finds a strong baseline alpha engine.
- Shows where it fails.
- Tests soft throttles.
- Quantifies left-tail improvement and right-tail loss.
- Emits per-alpha fold diagnostics.
- Produces a hypothesis book.
- Applies strict falsification.
- Attributes weak folds to market/event hypotheses.

The best numerical candidate is:

```text
Portfolio level: drawdown_only_throttle
Alpha level: doji_reversal_score + soft_aggressive
```

But both remain research-only.

## Deployment Assessment

### Baseline

The baseline is a strong research control and possible shadow-trading candidate. It is not deployable because:

- Max drawdown remains `-15.27%`.
- Negative fold rate is `37.50%`.
- Worst fold Sharpe is `-26.26`.
- Worst weak folds lose more than `-7%` at the aggregate level and more than `-11%` at the alpha level.
- We do not yet have a validated blocker for known stress regimes.

### Gates and Throttles

No gate or throttle is deployable:

- No aggregate variant has significant positive delta versus baseline.
- No alpha-level lead has positive lower confidence bound.
- Strict falsification found zero passing hypotheses.
- Gate stability is weak.
- Multiple-testing risk remains material.

## Limitations

1. The current walk-forward period is still limited to 24 latest monthly folds.

2. Current tail diagnostics are fold-level, not yet full trade/name-day blocker diagnostics.

3. Overlapping 10-day horizon returns are approximated into daily streams; a cleaner tranche-level PnL engine is still needed.

4. The current p-values are not yet adjusted by a full White Reality Check, Hansen SPA, or equivalent multiple-testing correction.

5. India VIX, USDINR, crude, FII flows, rates, CPI, PMI, and explicit sector maps are not fully wired as lagged features yet.

6. Event attribution is post-hoc and explanatory. It must not be used as a rule until timestamped and pre-registered.

7. The strict `95%` right-tail retention bar makes sense for deployment but may be too harsh for early discovery. It should remain the promotion bar.

## Recommended Next Research Step

The next experiment should be narrow and pre-registered:

```text
Candidates:
1. doji_reversal_score + gap_fade low + soft_aggressive
2. doji_reversal_score + gap_fade low + drawdown_only_throttle
3. inside_outside_bar_score + volatility_expansion high + drawdown_only_throttle
4. oscillator reversal family + gap_fade low + soft_aggressive
5. support_trendline_position_20 + volatility_expansion high + soft_aggressive

Validation:
- Horizon: 10 days
- Cost: 10 bps and 25 bps
- Train: 6 months
- Test: next 1 month
- Purge: 10-day label overlap
- Embargo sensitivity: add shifted split checks
- No new thresholds after seeing test fold
- Report trade-level accepted-winner / blocked-winner / accepted-loser / blocked-loser counts
```

Success conditions:

- Right-tail retention at least `95%`.
- Positive left-tail improvement.
- Positive lower CI or return retention near baseline with significant tail reduction.
- Corrected p-value below threshold after multiple-testing adjustment.
- Stable gate family in at least 50% to 60% of folds.
- Does not collapse at 25 bps.

## Final Conclusion

The research has found useful structure:

```text
Price-action alpha failures cluster in identifiable market states.
Indicators contain information about bad regimes.
Soft throttles are better than hard gates.
The baseline is strong but left-tail fragile.
```

However, the current blocker system is not yet validated:

```text
No gate preserves enough right tail and proves statistically significant improvement.
```

The correct current posture is:

```text
baseline = research control / shadow candidate
soft throttles = research-only risk overlays
hard gates = rejected as main engine
alpha-regime hypotheses = pre-registered candidates for next falsification run
deployment = no
```

This is a useful research outcome because it prevents premature promotion while giving a clear, evidence-backed path for the next experiment.
