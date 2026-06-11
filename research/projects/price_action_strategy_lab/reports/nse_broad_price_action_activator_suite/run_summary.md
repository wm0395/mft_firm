# Activator Suite Run

- screen rows: 123
- selection rows: 5
- activated families: 5
- backtest rows: 900
- compute backend: cpu_fallback_no_cupy

## Selected Family Activators

               family selected_activator  mean_lift_bps  mean_gated_net_bps
  reversal_exhaustion oscillator_extreme     258.605436          372.298688
  volume_confirmation     breadth_thrust     226.085876          303.042512
breakout_continuation     breadth_thrust     147.190429          273.326422
      trend_following     breadth_thrust      98.364907          174.353209
     structure_levels  volume_acceptance      75.570389          158.294423

## Indicator Inventory

- trend alignment: higher timeframe trend, supertrend, and trend filters
- breakout environment: trend alignment plus breadth, expansion, and relative strength
- mean reversion environment: choppy mean-reverting regime with weak breadth
- volatility expansion / compression: realized-volatility state
- breadth thrust / risk-off: market breadth overlays
- gap continuation / fade: opening gap regime
- volume acceptance: volume profile acceptance and value area
- relative strength leaders / laggards: multi-horizon ranking
- oscillator extreme: RSI, stochastic, and Williams %R extremes

Macro indicators to wire next: India VIX, yield curve slope, USD/INR, crude, rates, flows, CPI surprise, PMI.