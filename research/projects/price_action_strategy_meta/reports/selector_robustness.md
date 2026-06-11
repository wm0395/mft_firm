# Selector Robustness

## Observation

- The current selector fails the available leakage-controlled robustness
  checks.
- The evidence that remains is concentrated in one fold, one year, and a
  narrow reversal cluster.
- Several robustness checks are still unrun and should remain explicit rather
  than implied.

## Hypothesis

- If the edge is real, it should survive split-family changes, cost stress,
  simple market adjustments, and baseline comparisons.
- If the edge is not real, the selector should either abstain or collapse
  under those tests.

## Test

| robustness check | status | result |
| --- | --- | --- |
| walk-forward split | FAIL | average lift `-2.126` bps vs baseline |
| purged split | FAIL | average lift `-2.126` bps vs baseline |
| embargo split | FAIL | average lift `-1.955` bps vs baseline |
| shifted split boundaries | FAIL | all tested shifts remain below baseline; `shift_63` and `shift_126` weaken further |
| different embargo lengths | FAIL | `0`, `5`, `10`, and `20` day embargoes all remain below baseline |
| different train/test window lengths | FAIL | `1000/252` and `1500/252` windows remain below baseline |
| alternative cost assumptions | FAIL | gate stays positive through `25` bps and turns negative by `50` bps (`7.985` to `-1.393`) |
| sector-neutral return variant | WEAK | selected gate schedule falls to `4.812` bps portfolio mean; walk-forward active pocket rises to `1.323` bps, but this is a selected-portfolio sensitivity only |
| market-neutral return variant | WEAK | selected gate schedule stays flat at `6.109` bps; walk-forward active pocket stays sparse at `0.412` bps portfolio mean, again as a selected-portfolio sensitivity only |
| exclude top contributor stocks | NEEDS_MORE_DATA | not directly rerun yet |
| exclude top contributor sectors | NEEDS_MORE_DATA | not directly rerun yet |
| strategy-family ablation | NEEDS_MORE_DATA | not directly rerun yet |
| regime-dimension ablation | NEEDS_MORE_DATA | not directly rerun yet |
| high-vol subset sensitivity | PARTIAL | causal reference window fix applied; full sweep not rerun |
| random label sanity check | WEAK | observed selector sits below the label-shuffle median but does not collapse to chance |
| random strategy selection baseline | PASS | observed selector sits well above random-strategy draws |
| always-on baseline | FAIL | selector remains below the baseline on holdout and leakage-controlled splits |
| abstain-only sanity check | PASS | selector abstains on 4 of 5 folds, but that alone does not create edge |
| bootstrap confidence intervals | WEAK | holdout gate CI is positive in absolute terms, but the baseline gap remains negative |

## Result

- Holdout gate: `6.109` bps portfolio mean versus `9.803` bps combined
  always-on baseline.
- Full threshold sweep does not rescue the gate; `loose` remains the best
  policy at `6.109` bps portfolio mean, still below the combined baseline.
- Reversal-family basket tests under `2of3_dd10` and `3of3_dd10` remain
  negative once abstentions are counted correctly:
  `-12.735` / `-16.792` holdout lift and `-4.168` / `-5.319` embargo mean
  lift, respectively.
- Split-sensitivity sweeps across boundary shifts, embargo lengths, and train
  windows still do not rescue the selector; every setting stays below the
  always-on baseline.
- Null benchmark checks show the observed selector below the label-shuffle
  median (`6.109` vs `7.072` bps) but well above random-strategy draws
  (`-0.145` bps median, `0.000` probability of matching the observed lift).
- Selected-portfolio neutral sensitivity leaves the gate flat under
  market-neutral returns, but sector-neutral adjustment lowers the holdout
  gate to `4.812` bps portfolio mean and does not change the rejection
  state.
- Walk-forward / purged / embargo: all below baseline.
- Gate bootstrap CI for portfolio mean bps: `[1.776, 10.767]`.
- Walk-forward bootstrap CI for portfolio mean bps: `[-0.094, 0.910]`.
- Gate activity is concentrated in four strategies and one universe.
- Walk-forward activity is concentrated in one strategy and one fold.
- Boundary and window perturbations do not rescue the selector; they keep
  the same negative lift pattern under modest split changes.

## Interpretation

- The selector is not yet robust enough to promote.
- The failure mode is not just friction; it is sample concentration and weak
  persistence.
- The current state is still useful as research because it points to a narrow
  reversal pocket, but it is not a deployment candidate.

## Decision

- `SUSPECT_OVERFIT`
- Keep the selector in research until the missing robustness sweeps are run
  and the embargo split turns positive after realistic costs.
