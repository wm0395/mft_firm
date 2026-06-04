# Meta Selector Design

This project is looking for a high-precision selector that decides whether a
price-action family should be active in the current regime, and if so, which
family should own the trade.

## Selector Job

- Choose one family or abstain.
- Prefer precision over coverage when the regime is weak.
- Avoid forcing a family into a regime that only looks good in-sample.
- Expose the decision path so every activation can be audited.

## Candidate Inputs

- `choppiness_index`
- `mass_index`
- `vortex_indicator`
- `ichimoku_cloud`
- `supertrend`
- `opening_gap_regime`
- `volume_profile_regime`
- `support_resistance_levels`
- `failed_breakout_signal`
- `trend_volume_composite`
- `hybrid_trend_volume_scores`
- `relative_strength_index`
- `stochastic_oscillator`
- `macd`
- `directional_movement_index`
- `average_directional_index`
- `channel_position`
- `williams_r`
- `fisher_transform`
- `detrended_price_oscillator`

## Initial Decision Logic

The first selector pass should be simple and abstaining:

- Breakout continuation only when compression, participation, and structure
  all agree.
- Trend following only when trend filters and volatility context align.
- Gap reaction only when the opening gap regime is explicit.
- Reversal exhaustion only when stretched price action and rejection appear
  together.
- Structure-level reactions only when prior support or resistance is relevant.
- Volume confirmation only as a gate, not as a stand-alone edge.

## Success Criteria

The selector is useful only if it improves out-of-sample results on the active
family choice without collapsing coverage.

Required checks:

- higher precision than an always-on family baseline
- lower calibration error than the unfiltered candidate set
- stable performance under `0`, `5`, `10`, and `25` bps stress
- acceptable coverage and abstention balance
- regime stability across walk-forward and held-out slices

## Baselines

- always-flat
- always-on best family from the training slice
- family-specific unconditional activation

## Output Contract

The selector should emit:

- chosen family
- direction
- confidence
- abstain flag
- reason codes for activation or abstention

The project should not claim deployment readiness until those outputs are
validated out of sample.
