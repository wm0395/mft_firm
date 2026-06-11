# Review From Quant

## Hypothesis

The strongest pocket we have found is reversal exhaustion in stressed regimes:
high volatility, bear trend, weak breadth, risk-off, and gap-shock states.

The open question is not whether that pocket exists. It does.
The open question is whether a simple, observable regime classifier can
activate it reliably enough to survive leakage-controlled validation.

That remains a hypothesis. It is not yet a measured conclusion.

## Measured Evidence

- Reversal-exhaustion strategies show the best recurring pockets in the regime
  summaries, especially in bear and high-vol conditions.
- The selector itself does not clear the hard test.
  - Holdout gate: `6.109` bps portfolio mean for the chosen `loose` policy
    versus `9.803` bps for the combined always-on baseline.
  - Walk-forward, purged, and embargo splits are all below baseline.
  - Fold 5 is the only active fold in the leakage-controlled runs.
- The surviving leakage-controlled activity is narrow:
  - concentrated in 2021 for walk-forward
  - concentrated in a small set of reversal-oriented rules
  - vulnerable to cost stress
- Bootstrap intervals and cost sensitivity do not rescue the selector's
  relative edge.
- Null benchmarks narrow the explanation space:
  - the observed selector sits below the label-shuffle median
  - it still sits well above random-strategy draws
  - so the edge is not pure chance, but it is not robust either
- The current evidence supports `SUSPECT_OVERFIT`, not promotion.

## Next Test

The next test is not broader feature search. It is a minimal, falsifiable
regime classifier built from observable inputs only:

- realized volatility percentile
- breadth relative to trend
- drawdown from recent highs

Run that rule through the existing embargo harness without extra tuning.
If it passes, then the deployment wrapper may be worth further work.
If it fails, the correct outcome is to keep the selector in research and
de-scope the deployment claim. The null benchmark already says the selector
is not just random, so the remaining question is persistence, not existence.

## Current Decision

- `KEEP_RESEARCH`
- Not deployment-ready
- The failure cause is still undiagnosed: signal quality, selector design,
  sample fragility, and regime non-stationarity are all live hypotheses
