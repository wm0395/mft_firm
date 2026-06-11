# Price Action Strategy Lab Research Paper

Date: 2026-06-10  
Scope: NSE `price_action_strategy_lab` research only

## Abstract

This program started as a broad search for a price-action alpha stack that could survive costs, preserve the right tail, and avoid fat left-tail losses on the NSE market-collector universe. The initial answer was negative for deployment and positive for mechanism discovery. Broad gate-shopping, volatility-only filters, and reversal-family throttles were rejected. The key surviving idea was an internal market-stress overlay, `breadth_risk_off`, which helped a subset of structure/level alphas and lifted return and Sharpe in isolated sleeves, but did not become a shadow-ready or deployable portfolio layer.

The final state is research-only. The strongest result is not a general gate and not a full-portfolio fix; it is a family-specific stress overlay for structure/level alphas, with explicit sleeve sizing still failing the drawdown bar.

## 1. Research Objective

The objective was to improve price-action alphas so the system can:

1. Accept good trade suggestions.
2. Block or reduce bad trade suggestions.
3. Identify market states where each alpha underperforms.
4. Establish statistical significance before promotion.
5. Avoid overfit or overly complex solutions unless they survive falsification.

The decision standard was strict throughout: a blocker is useful only if it reduces left-tail loss while preserving most of the right-tail return and surviving leakage-aware validation.

## 2. Data And Setup

The work used the NSE universe built from the market-collector-backed panel exposed through `project.data.market_collector_panel`. Research code stayed inside the project boundary and used cached signal frames and report artifacts rather than ad hoc notebook state.

Core run conventions:

- Universe: broad NSE market-collector universe.
- Primary horizon: `10` trading days.
- Validation: purged walk-forward, `126` trading days train, `21` trading days test, `21` day step, `10` day purge/lookahead, latest `24` folds.
- Costs: `10 bps` primary; `25 bps` and `50 bps` robustness; some early diagnostics also used `75 bps`.
- Expression modes: `cross_sectional_quintile`, `time_series_threshold`, `ranked_long_only`.
- Compute: cached alpha signals, parallel fan-out, and optional GPU assistance for rank-precompute steps.

Important note: each stage below is reported against its paired baseline inside the corresponding artifact. Some headline totals differ slightly across runs because they came from different stage-specific report slices, not from one merged backtest.

## 3. Alpha Universe

The lab ended with `25` encoded alphas: `5` core reversal signals plus `20` broader price-action and candlestick-pattern strategies.

Core reversal set:

- `bollinger_percent_b_mean_reversion_20`
- `stochastic_mean_reversion_14`
- `williams_r_mean_reversion_14`
- `fisher_transform_reversal_10`
- `inverse_fisher_rsi_reversal_10`

Broader registry:

- Breakout / continuation: `breakout_20`, `keltner_breakout_20`, `squeeze_breakout_20`, `relative_volume_breakout_20`
- Trend / confirmation: `supertrend_direction_10`, `parabolic_sar_trend`, `chandelier_trend`, `multi_timeframe_confirmation`
- Structure / gap: `opening_gap_regime_score`, `support_resistance_position_20`, `support_trendline_position_20`
- Candlestick / reversal: `doji_reversal_score`, `engulfing_reversal_score`, `hammer_shooting_star_score`, `inside_outside_bar_score`, `piercing_dark_cloud_score`
- Derived helpers: `failed_breakout_score_20`, `failed_reversal_score`, `trend_volume_composite`, `hybrid_confirmation`

## 4. Methodology

The project hardened research quality before drawing conclusions:

- Purged walk-forward validation with embargo logic.
- Train-only tuning of thresholds and multipliers.
- Stationary-bootstrap confidence intervals.
- Paired t-tests with Benjamini-Hochberg correction.
- Fold concentration checks to detect one-fold luck.
- Event-cluster reporting for known weak market states.
- Cached signal/rank layers with GPU support where available.
- Streamlit-friendly and markdown-friendly report generation.

The project direction evolved in stages:

1. Broad activator search.
2. Single-alpha survivor diagnostics.
3. Stress confirmation.
4. Breadth-only stress overlay testing.
5. Family replication.
6. Portfolio integration.
7. Explicit sleeve sizing.

## 5. Research Chronology And Findings

| Stage | Hypothesis | Headline result | Decision |
|---|---|---|---|
| Broad activator suite | A general activator/gate might improve the alpha stack | Best portfolio-level throttle was `drawdown_only_throttle`: Sharpe improved from `2.19` to `2.40`, max drawdown improved from `-15.27%` to `-13.03%`, but return did not beat baseline and significance was weak. Broad holdout also showed `54.3%` precision, `13.5%` coverage, and `6.691 bps` mean portfolio return versus `5.647 bps` for always-on. | Research-only |
| Single-alpha survivor | `support_trendline_position_20 + volatility_expansion high + soft_aggressive` might survive as a lead | At `25 bps`: mean delta `+0.2458%`, left-tail delta `+1.0461%`, right-tail retention `95.35%`, net blocker `+4.0347`. The effect helped stress folds and hurt ordinary folds. | Research lead only |
| Stress confirmation | `breadth_risk_off` might isolate stress better than `volatility_expansion` | At `25 bps`, `breadth_risk_off` beat volatility-only and the `AND` condition. It had cleaner unmatched-fold behavior and higher net blocker value. | Retain as internal stress signal |
| Breadth-only diagnostic | `support_trendline_position_20 + breadth_risk_off high + soft_aggressive` might be the best single-alpha stress lead | At `10 bps`: return `20.6556%` vs `10.4521%` baseline, Sharpe `1.2140` vs `0.7206`, right-tail retention `111.7451%`, unmatched delta `+0.2230%`, stress delta `+0.8779%`. CI lower bound remained negative. | Retained research lead |
| Family replication | `breadth_risk_off` should generalize across related alphas | It generalized to the structure/level family, not the reversal/exhaustion family. Structure family: mean delta `+0.1061%`, right-tail `111.3150%`, unmatched `+0.2230%`, net blocker `+1.8779`, alpha improve rate `60.0%`. Reversal family failed. | Retained research overlay for structure family only |
| Portfolio integration | The structure overlay should improve the full 25-alpha stack | Full-stack effect was weak. The core structure overlay slightly improved return and Sharpe, but drawdown did not improve enough; the negative control stayed rejected. | Research-only |
| Sleeve allocation | A separately sized structure sleeve may harvest the effect better | A `20%` core overlay sleeve was the best weighted variant, but max drawdown still worsened versus baseline. Return and Sharpe improved; drawdown did not. | Research-only |

## 6. Detailed Results

### 6.1 Broad Activator Suite

The earliest broad search showed that some gates could identify hostile regimes, but they were too coarse for deployment.

Best broad conclusions:

- `drawdown_only_throttle` was the best portfolio-level risk throttle.
- `doji_reversal_score + soft_aggressive` was the best single alpha-level lead.
- Broad gates were informative but not approved alpha enhancers.

Key alpha-level lead:

| alpha | variant | mean delta vs baseline | delta CI low | paired p-value | left-tail delta | right-tail retention | tail decision |
|---|---|---:|---:|---:|---:|---:|---|
| `doji_reversal_score` | `soft_aggressive` | `+0.4052%` | `-0.0320%` | `0.1771` | `+2.0907%` | `91.77%` | research_only_not_significant |
| `doji_reversal_score` | `drawdown_only_throttle` | `+0.3186%` | `-0.0528%` | `0.2062` | `+1.5546%` | `91.73%` | research_only_not_significant |
| `support_trendline_position_20` | `soft_aggressive` | `+0.1360%` | `-0.2131%` | `0.5444` | `+1.0306%` | `96.08%` | research_only_not_significant |

### 6.2 Single-Alpha Survivor Diagnostic

The single-alpha survivor was:

`support_trendline_position_20 + volatility_expansion high + soft_aggressive`

At `25 bps`:

- Mean delta vs baseline: `+0.2458%`
- Left-tail delta: `+1.0461%`
- Right-tail retention: `95.35%`
- Net blocker value: `+4.0347`
- Helped folds: `12`
- Hurt folds: `11`

Interpretation: this was a real stress protector, not a general alpha enhancer.

### 6.3 Stress Confirmation

The next experiment asked whether `breadth_risk_off` was cleaner than `volatility_expansion`.

At `25 bps`:

| Variant | Mean delta | Left tail | Right tail | Unmatched delta | Stress delta | Net blocker |
|---|---:|---:|---:|---:|---:|---:|
| Volatility only | `+0.2458%` | `+1.0461%` | `95.35%` | `-0.1723%` | `+1.5000%` | `+4.03` |
| Breadth risk-off only | `+0.2835%` | `+0.6850%` | `108.44%` | `+0.0856%` | `+0.8770%` | `+6.32` |
| Volatility AND breadth | `+0.2650%` | `+0.6110%` | `108.44%` | `+0.0856%` | `+0.8030%` | `+5.87` |

Interpretation:

- `breadth_risk_off` fixed the ordinary/unmatched fold failure mode.
- The `AND` condition was unnecessary.
- `breadth_risk_off` became the preferred internal stress signal.

### 6.4 Breadth-Only Diagnostic

The clearest single-alpha result came at `10 bps`.

| Metric | Baseline | Breadth risk-off |
|---|---:|---:|
| Return | `10.4521%` | `20.6556%` |
| Sharpe | `0.7206` | `1.2140` |
| Mean delta | `0.0000%` | `+0.3867%` |
| Left-tail delta | `0.0000%` | `+0.6815%` |
| Right-tail retention | `100.00%` | `111.7451%` |
| Unmatched delta | `0.0000%` | `+0.2230%` |
| Stress delta | `0.0000%` | `+0.8779%` |

This still failed significance: the confidence interval lower bound stayed negative and fold concentration remained a concern. It was the strongest internal stress-overlay lead, but not deployable.

### 6.5 Family Replication

`breadth_risk_off` was then tested across two families.

| Group | Mean delta | Left tail | Right tail | Unmatched | Stress | Net blocker | Improve rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| Structure / level | `+0.1061%` | `-0.3950%` | `111.3150%` | `+0.2230%` | `+0.8779%` | `+1.8779` | `60.0%` |
| Reversal / exhaustion | `-0.1806%` | negative | `109.6590%` | `-0.4634%` | `+1.3050%` | `-4.8876` | `14.3%` |

The structure family had partial generalization; the reversal family failed cleanly. The best structure names were `support_trendline_position_20`, `support_resistance_position_20`, and `failed_reversal_score`. The weak names included `failed_breakout_score_20` and `inside_outside_bar_score`.

### 6.6 Portfolio Integration

The family effect did not translate cleanly into the full 25-alpha stack.

At `10 bps`:

| Variant | Return | Sharpe | Max DD |
|---|---:|---:|---:|
| `full_baseline` | `24.3564%` | `1.8915` | `-7.4978%` |
| `full_stack_structure_overlay` | `24.7869%` | `1.8659` | `-7.9010%` |
| `full_stack_core_structure_overlay` | `25.1952%` | `1.9191` | `-7.7425%` |
| `structure_family_only_overlay` | `34.5809%` | `2.4618` | `-10.3316%` |
| `reversal_family_only_overlay_negative_control` | `12.7864%` | `-0.1803` | `-10.6063%` |

Interpretation:

- The full-stack structure overlay barely improved return and worsened drawdown.
- The core overlay was the best portfolio candidate, but still not shadow-ready.
- The reversal-family negative control stayed rejected.

### 6.7 Sleeve Allocation

The last step tested explicit sleeve sizing instead of naive full-stack overlaying.

Best weighted core sleeve:

| Variant | Return | Sharpe | Max DD | Delta vs baseline |
|---|---:|---:|---:|---:|
| `full_baseline` | `25.0073%` | `2.1899` | `-15.2708%` | `0.0000%` |
| `+5% core overlay sleeve` | `25.4004%` | `2.2053` | `-15.3359%` | `+0.3932%` |
| `+10% core overlay sleeve` | `25.7945%` | `2.2197` | `-15.4009%` | `+0.7873%` |
| `+15% core overlay sleeve` | `26.1896%` | `2.2331` | `-15.4659%` | `+1.1824%` |
| `+20% core overlay sleeve` | `26.5857%` | `2.2457` | `-15.5310%` | `+1.5784%` |

The sleeve improved return and Sharpe monotonically with size, but drawdown still worsened slightly. Larger full-structure sleeves raised return even further, but with more drawdown pressure.

## 7. Conclusion

The project did not find a deployable alpha or gate. It did find a credible internal market-state signal:

`breadth_risk_off` is a real stress overlay for structure/level alphas.

However:

- It does not generalize to reversal/exhaustion alphas.
- It does not survive full-portfolio integration as a strong drawdown reducer.
- It does not meet the shadow-candidate promotion bar.

The final research state is therefore:

- `breadth_risk_off` retained as a research overlay.
- Structure sleeve allocation retained as a research-only improvement path.
- No deployable strategy approved.

## Appendix A. Full Alpha Registry

### A.1 Core Five

- `bollinger_percent_b_mean_reversion_20`
- `stochastic_mean_reversion_14`
- `williams_r_mean_reversion_14`
- `fisher_transform_reversal_10`
- `inverse_fisher_rsi_reversal_10`

### A.2 Broader Twenty

Breakout / continuation:

- `breakout_20`
- `keltner_breakout_20`
- `squeeze_breakout_20`
- `relative_volume_breakout_20`

Trend / confirmation:

- `supertrend_direction_10`
- `parabolic_sar_trend`
- `chandelier_trend`
- `multi_timeframe_confirmation`

Structure / gap:

- `opening_gap_regime_score`
- `support_resistance_position_20`
- `support_trendline_position_20`

Candlestick / reversal:

- `doji_reversal_score`
- `engulfing_reversal_score`
- `hammer_shooting_star_score`
- `inside_outside_bar_score`
- `piercing_dark_cloud_score`

Derived helpers:

- `failed_breakout_score_20`
- `failed_reversal_score`
- `trend_volume_composite`
- `hybrid_confirmation`

## Appendix B. Result Ledger

### B.1 Broad Activator Suite

- Best portfolio throttle: `drawdown_only_throttle`
- Sharpe: `2.19 -> 2.40`
- Max drawdown: `-15.27% -> -13.03%`
- Best alpha lead: `doji_reversal_score + soft_aggressive`
- Mean fold delta: `+0.4052%`
- Left-tail improvement: `+2.0907%`
- Right-tail retention: `91.77%`
- CI low: `-0.0320%`
- Decision: research-only

### B.2 Survivor Diagnostic

- Candidate: `support_trendline_position_20 + volatility_expansion high + soft_aggressive`
- Mean delta: `+0.2458%`
- Left-tail delta: `+1.0461%`
- Right-tail retention: `95.35%`
- Net blocker: `+4.0347`
- Helped folds: `12`
- Hurt folds: `11`

### B.3 Stress Confirmation

- `breadth_risk_off` beat volatility-only on ordinary-fold behavior.
- `breadth_risk_off` beat the volatility AND breadth condition on net blocker value.
- `AND` was unnecessary.

### B.4 Breadth-Only Diagnostic

- Return: `20.6556%` vs `10.4521%` baseline
- Sharpe: `1.2140` vs `0.7206`
- Right-tail retention: `111.7451%`
- Unmatched delta: `+0.2230%`
- Stress delta: `+0.8779%`
- CI low remained negative

### B.5 Family Replication

- Structure / level: positive and partially generalizing
- Reversal / exhaustion: rejected
- Best structure names: `support_trendline_position_20`, `support_resistance_position_20`, `failed_reversal_score`
- Weak names: `failed_breakout_score_20`, `inside_outside_bar_score`

### B.6 Portfolio Integration

- `full_stack_structure_overlay`: weak return gain, worse Sharpe, worse drawdown
- `full_stack_core_structure_overlay`: best portfolio candidate, but still not shadow-ready
- Negative control: rejected

### B.7 Sleeve Allocation

- Best weighted sleeve: `+20% core overlay sleeve`
- Return improved: `+1.5784%` vs baseline
- Sharpe improved: `2.2457` vs `2.1899`
- Max drawdown still worsened slightly

## Appendix C. Artifact Index

- [Broad activator suite memo](/home/wm0395/Investment/mft_project/research/projects/price_action_strategy_lab/reports/nse_broad_price_action_activator_suite/research_review_memo.md)
- [Survivor diagnostic](/home/wm0395/Investment/mft_project/research/projects/price_action_strategy_lab/reports/nse_survivor_diagnostic/20260610T112604Z/support_trendline_survivor_report.md)
- [Stress confirmation](/home/wm0395/Investment/mft_project/research/projects/price_action_strategy_lab/reports/nse_stress_confirmation/20260610T120055Z/support_trendline_stress_confirmation_report.md)
- [Breadth-only diagnostic](/home/wm0395/Investment/mft_project/research/projects/price_action_strategy_lab/reports/nse_breadth_only_diagnostic/20260610T122047Z/support_trendline_breadth_only_report.md)
- [Family replication](/home/wm0395/Investment/mft_project/research/projects/price_action_strategy_lab/reports/nse_breadth_family_replication/20260610T131159Z/breadth_risk_off_family_replication_report.md)
- [Portfolio integration](/home/wm0395/Investment/mft_project/research/projects/price_action_strategy_lab/reports/nse_portfolio_integration/20260610T141709Z/breadth_risk_off_portfolio_integration_report.md)
- [Structure sleeve allocation](/home/wm0395/Investment/mft_project/research/projects/price_action_strategy_lab/reports/nse_breadth_risk_off_structure_sleeve/20260610T151205Z/breadth_risk_off_structure_sleeve_report.md)

## Appendix D. What To Inspect Next

If you want to inspect the raw evidence, start with:

1. The breadth-only and family-replication reports for fold concentration and significance.
2. The portfolio integration report for the full-stack aggregation failure.
3. The sleeve allocation report for the explicit sizing results.

The project is now in a stable research state: useful mechanism discovered, no deployable strategy approved.
