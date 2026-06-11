# Support Trendline Volatility-Expansion Diagnostic

Candidate:

```text
support_trendline_position_20
+ volatility_expansion high
+ soft_aggressive
```

Status: research-only. This is the closest right-tail-preserving lead, but it lacks statistical significance.

## Why This Candidate Survived Further Review

Most aggressive candidates improved left-tail folds by sacrificing too much right tail. This candidate is different: it retains more than 95% of right-tail return across all tested costs.

| cost_bps | mean_delta_pct | ci_low_pct | paired_p_value | bh_p_value | left_tail_delta_pct | right_tail_retention | decision |
|---:|---:|---:|---:|---:|---:|---:|---|
| 10 | 0.1900 | -0.4383 | 0.6132 | 0.8362 | 0.9876 | 0.9510 | research_only_not_significant |
| 25 | 0.2458 | -0.3784 | 0.5127 | 0.8362 | 1.0461 | 0.9535 | research_only_not_significant |
| 50 | 0.3616 | -0.2454 | 0.3302 | 0.6191 | 1.2223 | 0.9578 | research_only_not_significant |

Interpretation:

- Right-tail preservation passes the strict 95% bar.
- Left-tail improvement is positive.
- Effect improves under higher cost stress because the throttle reduces some costly exposure.
- The lower confidence interval remains negative.
- Corrected p-values are not close to significance.

## Trade-Level Blocker Accounting

| cost_bps | net_blocker_value | loss_reduced_from_sized_down_losers | profit_reduced_from_sized_down_winners | profit_added_from_sized_up_winners | loss_added_from_sized_up_losers |
|---:|---:|---:|---:|---:|---:|
| 10 | 3.9209 | 63.5022 | 62.2386 | 20.5547 | 17.8974 |
| 25 | 4.0347 | 64.2687 | 62.6833 | 19.2821 | 16.8328 |
| 50 | 4.7772 | 64.2687 | 62.6833 | 18.7738 | 15.5820 |

The trade-level arithmetic is slightly positive:

```text
net_blocker_value =
  losses reduced
- profits reduced
+ profits added
- losses added
```

The key issue is that the edge is small. The gate reduces losers and winners in almost equal size:

- At 25 bps, losses reduced: `64.2687`
- At 25 bps, profits reduced: `62.6833`
- At 25 bps, net blocker value: only `4.0347`

This is why the candidate looks directionally useful but statistically weak.

## Event-Cluster Behavior

| cost_bps | event_label | fold_count | mean_delta_pct | mean_baseline_return_pct | mean_variant_return_pct |
|---:|---|---:|---:|---:|---:|
| 25 | early_2025_broad_correction_fpi_outflows | 3 | 0.8882 | -5.8443 | -4.9561 |
| 25 | feb_2026_it_global_tech_selloff | 2 | 1.2119 | -3.8054 | -2.5934 |
| 25 | july_2025_broad_based_selling | 1 | 3.9109 | -5.2472 | -1.3363 |
| 25 | unmatched | 18 | -0.1723 | 2.1730 | 2.0007 |

The candidate helps the known stress clusters but slightly hurts the larger unmatched bucket.

This explains the research state:

```text
protects identified stress clusters
but loses enough ordinary-fold return
to make the total effect statistically weak
```

## Worst Fold Damage

The main damage is not catastrophic failure; it is opportunity cost in positive baseline folds.

Examples at 25 bps:

| fold | window | baseline_return_pct | variant_return_pct | delta_pct |
|---:|---|---:|---:|---:|
| 345 | 2025-05-08 to 2025-06-05 | 5.2351 | 1.2862 | -3.9489 |
| 333 | 2024-05-01 to 2024-05-30 | 3.7436 | 1.8589 | -1.8847 |
| 335 | 2024-07-02 to 2024-07-31 | 3.5431 | 1.7599 | -1.7832 |
| 344 | 2025-04-03 to 2025-05-07 | 3.3135 | 1.6116 | -1.7019 |

This says the blocker is sometimes sizing down during profitable normal regimes.

## Best Fold Protection

Examples at 25 bps:

| fold | window | baseline_return_pct | variant_return_pct | delta_pct |
|---:|---|---:|---:|---:|
| 347 | 2025-07-07 to 2025-08-04 | -5.2472 | -1.3363 | 3.9109 |
| 355 | 2026-03-10 to 2026-04-12 | 10.5038 | 13.4100 | 2.9062 |
| 352 | 2025-12-08 to 2026-01-06 | 0.1284 | 2.8068 | 2.6784 |
| 346 | 2025-06-08 to 2025-07-06 | -3.1415 | -0.7938 | 2.3476 |

This is the attractive part of the candidate: it can protect bad folds and sometimes size into good states.

## Gate Stability

| cost_bps | threshold_mean | threshold_std | multiplier_down_mean | multiplier_up_mean | avg_exposure_multiplier |
|---:|---:|---:|---:|---:|---:|
| 10 | 0.1161 | 0.0400 | 0.3438 | 1.2000 | 0.7448 |
| 25 | 0.1181 | 0.0395 | 0.3438 | 1.1875 | 0.7326 |
| 50 | 0.1186 | 0.0399 | 0.3438 | 1.1812 | 0.7267 |

The threshold and multiplier choices are reasonably stable across cost levels. The problem is not wild parameter instability. The problem is weak economic separation between reduced losers and reduced winners.

## Current Diagnosis

This candidate is not failing because it destroys the right tail. It is failing because:

1. The effect size is too small.
2. It helps stress clusters but slightly hurts the large unmatched bucket.
3. It reduces almost as much winner profit as loser loss.
4. Bootstrap lower CI remains negative.
5. Corrected p-values do not support promotion.

## Research Decision

Keep as the best right-tail-preserving research lead.

Do not promote.

Next test should not broaden the search. The next focused test should ask:

```text
Can volatility_expansion high be refined into a more selective stress-state definition
using only pre-declared market variables such as breadth collapse or index trend,
without reducing right-tail retention below 95%?
```

Candidate next refinement:

```text
support_trendline_position_20
+ volatility_expansion high
+ breadth_risk_off high
+ soft_aggressive
```

This must be treated as a new pre-registered hypothesis, not an edit to the current result.
