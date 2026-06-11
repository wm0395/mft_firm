# Research Audit

## Observation

- The current gate does not beat the combined always-on baseline on the 5-day
  holdout.
- Leakage-controlled walk-forward, purged, and embargoed splits all remain
  below the combined always-on baseline.
- Activity is sparse and concentrated: the gate only activates in
  `nifty500`, while `expanded` never activates.
- The extra screen keeps one durable pocket: reversal exhaustion, especially
  `fisher_transform_reversal_10` and `inverse_fisher_rsi_reversal_10`.

| policy | train precision | test precision | test coverage | train active days | test active days | test active mean bps | test portfolio mean bps |
| --- | --- | --- | --- | --- | --- | --- | --- |
| loose | 0.591 | 0.549 | 0.176 | 269 | 805 | 34.758 | 6.109 |
| high_conf | 0.590 | 0.548 | 0.174 | 268 | 796 | 26.262 | 4.564 |
| balanced | 0.569 | 0.541 | 0.174 | 269 | 799 | 30.316 | 5.289 |

| split | folds | test mean bps | baseline mean bps | lift vs baseline |
| --- | --- | --- | --- | --- |
| walk_forward | 5 | 0.412 | 2.538 | -2.126 |
| purged | 5 | 0.412 | 2.538 | -2.126 |
| embargo | 5 | 0.412 | 2.367 | -1.955 |

## Hypothesis

- The selector only has a narrow reversal edge in a few high-vol, bear,
  risk-off, and gap-shock pockets.
- If that edge were durable, it should survive cost stress, fold shifts, and
  the embargo split.
- If it is not durable, the activity should collapse into a small number of
  rules, dates, or universes.

## Test

- Holdout gate readout from `selector_gate.md` and
  `selector_gate_backtest.csv`.
- Leakage-controlled split readout from `selector_walk_forward.md` and
  `selector_walk_forward_summary.csv`.
- Concentration readout from `selector_gate_selected.csv`,
  `selector_walk_forward_selected.csv`, and the regime summary CSVs.
- Bootstrap and cost-stress checks from the current selected-frame artifacts.

## Result

- Gate active-day bootstrap CI for mean net bps: `[9.296, 61.743]`.
- Gate precision bootstrap CI: `[0.514, 0.584]`.
- Gate portfolio mean bootstrap CI: `[1.776, 10.767]`.
- Gate cost sensitivity, portfolio mean bps: `0 -> 7.985`, `5 -> 7.047`,
  `10 -> 6.109`, `25 -> 3.296`, `50 -> -1.393`.
- Full threshold sweep across `strict`, `ultra_strict_*`, `high_conf`,
  `balanced`, `loose`, and `hyper_strict_*` found no policy above the
  combined baseline; `loose` remains the best portfolio mean at `6.109` bps.
- Null benchmark reads the observed selector below the label-shuffle median
  but far above random-strategy draws, which narrows the remaining explanation
  space without changing the rejection verdict.
- Gate activity by universe: `nifty500 = 805`, `expanded = 0`.
- Gate activity by strategy: `bollinger_percent_b_mean_reversion_20 = 440`,
  `choppiness_inverse_14 = 201`, `fisher_transform_reversal_10 = 162`,
  `trend_volume_composite = 2`.
- Gate activity by family: `reversal_exhaustion = 602`, `trend_following = 201`,
  `volume_confirmation = 2`.
- Walk-forward active rows: `63`, all in `2021`, with `fold 5` only.
- Walk-forward activity by strategy: `fisher_transform_reversal_10 = 63`.
- Walk-forward active-day bootstrap CI for mean net bps:
  `[-12.029, 107.085]`.
- Walk-forward precision bootstrap CI: `[0.603, 0.825]`.
- Walk-forward portfolio mean bootstrap CI: `[-0.094, 0.910]`.
- Walk-forward cost sensitivity, portfolio mean bps: `0 -> 0.467`, `5 -> 0.439`,
  `10 -> 0.412`, `25 -> 0.330`, `50 -> 0.193`.
- Strong sector pockets at 5d remain concentrated in `Construction`,
  `Chemicals`, `Healthcare`, `Capital Goods`, and `Metals & Mining` under
  specific risk states.

## Leakage and Timing Findings

- The high-vol panel now uses a causal reference window when selecting the top
  100 high-vol names.
- Strategy summaries are built from train-only masks and do not mix test rows
  into train statistics.
- Forward returns are aligned to the 5-day horizon used in the gate and
  walk-forward reports.
- The remaining failure is not an obvious lookahead artifact; it is a narrow,
  unstable edge that does not survive the embargo gate.

## Interpretation

- The current selector is explainable, but the edge is too concentrated to
  qualify as robust.
- The holdout gate is positive in absolute terms, but the selector still trails
  the always-on baseline and the leakage-controlled folds do not close the gap.
- The best surviving signal remains reversal exhaustion, but the selector does
  not capture it broadly enough to beat the always-on baseline.

## Decision

- `KEEP_RESEARCH`
- Reject promotion until the selector beats the combined always-on baseline on
  holdout, walk-forward, purged, and embargo splits after costs.
