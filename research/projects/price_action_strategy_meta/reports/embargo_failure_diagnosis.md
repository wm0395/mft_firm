# Embargo Failure Diagnosis

## Observation

- The embargo-controlled split is still negative.
- Only fold 5 activates under walk-forward, purged, and embargo splits.
- Folds 1-4 abstain completely, so the selector is not persistent across time.
- The surviving fold is concentrated in 2021 and in reversal-oriented rules.

| split_type | fold | policy | test precision | test coverage | test mean bps | baseline mean bps | lift vs baseline |
| --- | --- | --- | --- | --- | --- | --- | --- |
| walk_forward | 1 | abstain | nan | 0.000 | 0.000 | 0.000 | 0.000 |
| walk_forward | 2 | abstain | nan | 0.000 | 0.000 | 1.478 | -1.478 |
| walk_forward | 3 | abstain | nan | 0.000 | 0.000 | 3.810 | -3.810 |
| walk_forward | 4 | abstain | nan | 0.000 | 0.000 | 0.305 | -0.305 |
| walk_forward | 5 | strict | 0.714 | 0.042 | 2.060 | 7.099 | -5.039 |
| purged | 5 | strict | 0.714 | 0.042 | 2.060 | 7.099 | -5.039 |
| embargo | 5 | strict | 0.714 | 0.042 | 2.060 | 7.099 | -5.039 |

## Hypothesis

- The embargo failure is caused by a narrow fold-specific reversal pocket, not
  by a broad market or sector edge.
- If that is true, the selected rules should be sparse, repeated only in one
  fold, and vulnerable to cost stress.

## Test

- Compare fold-level walk-forward, purged, and embargo outputs.
- Count rule persistence across folds.
- Measure active-day concentration by year and month.
- Estimate bootstrap confidence intervals and cost sensitivity.
- Check a simple high-vol market proxy for contamination.

## Result

### Fold-level decomposition

- Fold 5 is the only active fold in all three split families.
- Folds 1-4 abstain, which means the candidate scan does not generalize
  across regime transitions.
- The fold 5 embargo lift is `-5.039` bps versus the combined always-on
  baseline.

### Policy drift

- The active policy name does not drift across split families: it is
  `strict` in fold 5 for walk-forward, purged, and embargo.
- The rule file contains `126` rows, all from fold 5, which means persistence
  is absent even though the same policy label recurs.
- The selected rule set spans only `6` unique strategies in fold 5:
  `bollinger_percent_b_mean_reversion_20`, `fisher_transform_reversal_10`,
  `inverse_fisher_rsi_reversal_10`, `mfi_mean_reversion_14`,
  `stochastic_mean_reversion_14`, and `williams_r_mean_reversion_14`.

### Sample fragility

- Gate active rows: `805`, with `2017` through `2026` represented but heavily
  concentrated in a few months.
- Gate bootstrap CI for active-day mean bps: `[9.296, 61.743]`.
- Gate bootstrap CI for portfolio mean bps: `[1.776, 10.767]`.
- Walk-forward active rows: `63`, all in `2021`.
- Walk-forward bootstrap CI for portfolio mean bps: `[-0.094, 0.910]`.
- The walk-forward CI is centered near zero, but the fold still loses to the
  baseline, so the point estimate is not enough.

### Temporal clustering

- Gate activity clusters in `2017`, `2018`, `2019`, `2023`, and `2024`,
  with smaller clusters in `2020`, `2021`, `2022`, `2025`, and `2026`.
- The top gate months are `2018-07`, `2017-03`, `2017-07`, `2023-07`,
  `2018-08`, `2018-06`, and `2024-02`.
- Walk-forward activity is entirely in `2021-06`, `2021-07`, `2021-09`, and
  `2021-10`.

### Market beta / sector beta contamination

- Using the high-vol universe average daily return as a simple market proxy,
  gate active-day mean net bps adjusts to `26.856` with correlation `-0.009`.
- The walk-forward active-day adjustment remains positive at `43.964` bps,
  with correlation `-0.051`, but that still does not rescue the split versus
  baseline.
- The strongest sector pockets are still localized: `Construction risk_off`,
  `Chemicals risk_off`, `Healthcare risk_off`, `Capital Goods risk_off`, and
  `Metals & Mining down_gap_shock` dominate the top of the regime table.

### Cost and turnover sensitivity

- Gate portfolio mean bps at different costs: `0 -> 7.985`, `5 -> 7.047`,
  `10 -> 6.109`, `25 -> 3.296`, `50 -> -1.393`.
- Walk-forward portfolio mean bps at different costs: `0 -> 0.467`,
  `5 -> 0.439`, `10 -> 0.412`, `25 -> 0.330`, `50 -> 0.193`.
- The gate stays positive through `25` bps and only turns negative between
  `25` and `50` bps, so break-even is around the low `40s` bps.

### Null benchmark

- The observed selector sits below the label-shuffle median, which means the
  observed gate is not the best random relabeling of the same regime summary.
- It still sits far above random-strategy draws, so the gate is not pure noise.
- That leaves a narrow but unresolved space between chance-level and
  robustness, which is still not enough to promote.

## Interpretation

- The embargo failure is a concentration problem, not a policy-label drift
  problem.
- The selector is surfacing a real reversal pocket, but only in a narrow
  cluster of dates, rules, and states.
- Simple reversal-family basket variants do not rescue the branch once
  abstentions are counted correctly; the negative embargo result is not just
  an unlucky single-strategy choice.
- The null benchmark narrows the explanation space, but it does not change the
  rejection decision.
- That cluster is too small to survive a realistic robustness audit.

## Decision

- `SUSPECT_OVERFIT`
- Reject promotion until the selector survives embargo and cost stress on a
  broader, more persistent sample.
