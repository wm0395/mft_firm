# OHLCV Strategy Research

This note captures the first reusable OHLCV math bundle and the literature that
motivates it. It is research-only and does not claim executable promotion.

## Objective

Build a deterministic formula layer that can support price-action, breakout,
trend, mean-reversion, and volume-confirmation work without re-deriving the
same math in each strategy.

## Primary Sources

- Wilder, *New Concepts in Technical Trading Systems* (1978). The book is the
  canonical source for RSI, ATR, DMI/ADX, and stop-and-reverse style thinking.
  - Open Library record:
    https://openlibrary.org/books/OL25090843M/New_concepts_in_technical_trading_systems
  - Google Books record:
    https://books.google.com/books/about/
    New_Concepts_in_Technical_Trading_System.html?id=WesJAQAAMAAJ
- Brock, Lakonishok, and LeBaron (1992), *Simple Technical Trading Rules and
  the Stochastic Properties of Stock Returns*.
  - PDF:
    https://technicalanalysis.org.uk/support-and-resistance/
    BrockLakonishokLeBaron1992.pdf
- Lo, Mamaysky, and Wang (2000), *Foundations of Technical Analysis*.
  - NBER PDF:
    https://business.columbia.edu/sites/default/files-efs/pubfiles/19268/
    Lo-Mamaysky_wang_foundations.pdf
- Moskowitz, Ooi, and Pedersen (2012), *Time Series Momentum*.
  - PDF: https://w4.stern.nyu.edu/facdir/lpederse/papers/TimeSeriesMomentum.pdf
- Bollinger, *Bollinger on Bollinger Bands* (2001).
  - Official book page: https://www.bollingerbands.com/bollinger-band-book
  - Google Books record:
    https://books.google.com/books/about/
    Bollinger_on_Bollinger_Bands.html?id=MVrJdo8VOnIC
- Bollinger official squeeze material.
  - Squeeze package: https://www.bollingerbands.com/tradestation-squeeze
  - Rules page: https://www.bollingerbands.com/bollinger-band-rules
- Marshall, Young, and Rose, *Candlestick technical trading strategies: Can
  they create value for investors?*
  - SSRN PDF:
    https://papers.ssrn.com/sol3/Delivery.cfm/
    SSRN_ID1083064_code114671.pdf?abstractid=980583&mirid=1
- Brooks, *Reading Price Charts Bar by Bar* (2009).
  - Google Books record:
    https://books.google.com/books/about/
    Reading_Price_Charts_Bar_by_Bar.html?id=apdVDwAAQBAJ
- Brooks, *Trading Price Action Reversals* (2012).
  - Google Books record:
    https://books.google.com/books/about/
    Trading_Price_Action_Reversals.html?id=3A6Fo0Xy3doC
- Crabel, *Day Trading with Short Term Price Patterns and Opening Range
  Breakout* (1990).
  - Google Books record:
    https://books.google.com/books/about/
    Day_Trading_with_Short_Term_Price_Patter.html?id=xpgbAAAACAAJ
- Person, *Candlestick and Pivot Point Trading Triggers* (2007).
  - Google Books record:
    https://books.google.com/books/about/
    Candlestick_and_Pivot_Point_Trading_Trig.html?id=Piv7chZppGIC
- Droke, *Support and Resistance Simplified* (2003).
  - Google Books record: https://books.google.com/books/about/
    Support_Resistance_Simplified.html?id=KoYnAAAACAAJ
- Murphy, *Technical Analysis of the Financial Markets* (1999).
  - Google Books record: https://books.google.com/books/about/
    Technical_Analysis_of_the_Financial_Mark.html?id=teitAAAAQBAJ
- Schwager, *Getting Started in Technical Analysis* (1999).
  - Google Books record: https://books.google.com/books/about/
    Getting_Started_in_Technical_Analysis.html?id=tmvDDwAAQBAJ
- Schabacker, *Technical Analysis and Stock Market Profits*.
  - Google Books record: https://books.google.com/books/about/
    Technical_Analysis_and_Stock_Market_Prof.html?id=iA0fEAAAQBAJ
- Achelis, *Technical Analysis from A to Z* (2nd ed.).
  - Google Books record: https://books.google.com/books/about/
    Technical_Analysis_from_A_to_Z_2nd_Editi.html?id=XuiF-2eWHYUC
- Chande and Kroll, *The New Technical Trader* (1994).
  - Google Books record: https://books.google.com/books/about/
    The_New_Technical_Trader.html?id=uPMJAQAAMAAJ
- Elder, *Trading for a Living* (1993).
  - Google Books record: https://books.google.com/books/about/
    Trading_for_a_Living.html?id=u7S4RG_fmvwC
- Elliott, *Ichimoku Charts: An introduction to Ichimoku Kinko Clouds* (2007).
  - Google Books record: https://books.google.com/books/about/
    Ichimoku_Charts.html?id=KG45O18e-a0C
- Pring, *Technician's Guide to Day and Swing Trading* (2002).
  - Google Books record: https://books.google.com/books/about/
    Technician_s_Guide_to_Day_and_Swing_Trad.html?id=LHyY8NdwtmEC
- Pring, *Pring on Price Patterns* (2004).
  - Google Books record:
    https://books.google.com/books/about/
    Pring_on_Price_Patterns.html?id=KYqEYbA6RR8C
- Keltner Channels, modern ATR-based version.
  - StockCharts page:
    https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/keltner-channels
- SuperTrend, official calculation reference.
  - TradingView support:
    https://www.tradingview.com/support/solutions/43000634738-supertrend/
- Choppiness Index formula and thresholds.
  - McClellan Financial chart note:
    https://www.mcoscillator.com/learning_center/weekly_chart/golds_choppiness_index/
- TRIX, triple-exponential smoothing oscillator.
  - StockCharts TRIX reference:
    https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/trix
- Ehlers, *Cybernetic Analysis for Stocks and Futures*.
  - Wiley excerpt (Fisher Transform chapter):
    https://catalogimages.wiley.com/images/db/pdf/0471463078.c01.pdf
- Ehlers, *The Inverse Fisher Transform*.
  - Traders.com abstract:
    https://traders.com/documentation/feedbk_docs/2004/05/Abstracts_new/Ehlers/ehlers.html
- Detrended Price Oscillator (DPO).
  - StockCharts ChartSchool:
    https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/detrended-price-oscillator-dpo
- Mass Index.
  - StockCharts ChartSchool:
    https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/mass-index
- Botes and Siepman, *The Vortex Indicator*.
  - Stocks & Commodities PDF:
    https://technical.traders.com/free/V28C01005BOTE.pdf
- Williams, *The Ultimate Oscillator*.
  - Stocks & Commodities PDF:
    https://williamspercentr.com/newsletters/ULTI.pdf
- Williams, *Original Williams %R*.
  - Official excerpt page:
    https://williamspercentr.com/the-original-percent-r
- Merkle, *Relative Strength and Stock Market Timing*.
  - Google Books record:
    https://books.google.com/books/about/
    Relative_Strength_and_Stock_Market_Timin.html?id=mikcAQAAMAAJ
- Carr, *Smarter Investing in Any Economy: The Definitive Guide to Relative
  Strength Investing* (2008).
  - Google Books record:
    https://books.google.com/books/about/
    Smarter_Investing_in_Any_Economy.html?id=EvJQQW3UkGYC
- Faber, *A Quantitative Approach to Tactical Asset Allocation*.
  - SSRN PDF:
    https://papers.ssrn.com/sol3/Delivery.cfm/
    SSRN_ID2403936_code649342.pdf?abstractid=962461
- Blau, *Momentum, Direction, and Divergence*.
  - Wiley page:
    https://www.wiley-vch.de/en/areas-interest/finance-economics-law/
    momentum-direction-and-divergence-978-0-471-02729-4
- McClellan, *Understanding Oscillators and Other Indicators*.
  - Official PDF:
    https://www.mcoscillator.com/download/docs/UnderstandingOscillators.pdf
- McClellan Financial, *Watching for a Zweig Breadth Thrust Signal*.
  - Learning center article:
    https://www.mcoscillator.com/learning_center/weekly_chart/
    watching_for_a_zweig_breadth_thrust_signal/
- *Technical Analysis: The Complete Resource for Financial Market Technicians*,
  Chapter 8, *Measuring Market Strength*.
  - O'Reilly chapter:
    https://www.oreilly.com/library/view/technical-analysis-the/9780134137186/ch08.html
- The support/resistance line method as an optimal stopping problem.
  - arXiv: https://arxiv.org/abs/2103.02331
- Orthogonalized factors and systematic risk decomposition.
  - ScienceDirect:
    https://www.sciencedirect.com/science/article/pii/S1062976913000185
- Parkinson, *The Extreme Value Method for Estimating the Variance of the
  Rate of Return* (1980).
  - EconPapers record:
    https://econpapers.repec.org/RePEc%3Aucp%3Ajnlbus%3Av%3A53%3Ay%3A1980%3Ai%3A1%3Ap%3A
    61-65
- Garman and Klass, *On the Estimation of Security Price Volatilities from
  Historical Data* (1980).
  - PDF mirror:
    https://www-2.rotman.utoronto.ca/~kan/3032/pdf/FinancialAssetReturns/
    Garman_Klass_JB_1980.pdf
- Rogers and Satchell, *Estimating Variance from High, Low and Closing
  Prices* (1991).
  - PDF mirror:
    https://www.skokholm.co.uk/wp-content/uploads/2016/01/
    R_Satchell_HLOC.pdf
- Yang and Zhang, *Drift-Independent Volatility Estimation Based on High,
  Low, Open, and Close Prices* (2000).
  - RePEc record:
    https://ideas.repec.org/a/ucp/jnlbus/
    v73y2000i3p477-91.html
- Hurst, *Long-Term Storage Capacity of Reservoirs* (1951).
  - CiNii record:
    https://cir.nii.ac.jp/crid/1571980074853982464?lang=en
- Lo and MacKinlay (1988), *Stock Market Prices Do Not Follow Random Walks:
  Evidence from a Simple Specification Test*.
  - NBER PDF: https://www.nber.org/papers/w2168.pdf
- Engle (1982), *Autoregressive Conditional Heteroscedasticity with Estimates
  of the Variance of United Kingdom Inflation*.
  - PDF mirror: https://finance.martinsewell.com/arch-garch/Engle1982.pdf
- Bollerslev (1986), *Generalized Autoregressive Conditional Heteroskedasticity*.
  - Duke PDF: https://public.econ.duke.edu/~boller/Published_Papers/joe_86.pdf
- Tharp, *Van Tharp's Definitive Guide to Position Sizing* (2008).
  - Google Books record:
    https://books.google.com/books/about/
    The_Definitive_Guide_to_Position_Sizing.html?id=0sa9PQAACAAJ
- Faith, *Way of the Turtle* (2007).
  - Google Books record:
    https://books.google.com/books/about/
    Way_of_the_Turtle_The_Secret_Methods_tha.html?id=tatZTyKeL2AC
- Pring, *Reverse Divergences and Momentum* (article).
  - PDF mirror:
    https://traderonthestreet.com/wp-content/uploads/2021/06/
    48.Reverse_Divergences_and_Momentum.pdf
- Antonacci, *Optimal Momentum: A Global Cross Asset Approach*.
  - SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1833722
- Geczy and Samonov, *Two Centuries of Multi-Asset Momentum*.
  - SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2607730
- Dalton, Jones, and Dalton, *Mind Over Markets: Power Trading with Market
  Generated Information* (updated edition).
  - Wiley-VCH page:
    https://www.wiley-vch.de/en?isbn=9781118531730&option=com_eshop&view=product
- Admati and Pfleiderer (1988), *A Theory of Intraday Patterns: Volume and
  Price Variability*.
  - Oxford Academic PDF:
    https://academic.oup.com/rfs/article-pdf/1/1/3/24434731/010003.pdf
- Plastun et al. (2020), *Price gap anomaly in the US stock market: the whole
  story*.
  - University of Pretoria repository:
    https://repository.up.ac.za/handle/2263/78336
- Cheng et al. (2023), *Stocks Opening Price Gaps and Adjustments to New
  Information*.
  - PMC full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC10017064/
- Abidou (2020), *Filling Open Price Gap on Intraday Timeframe: A Case Study
  for DJIA Index Stocks*.
  - SSRN record:
    https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3592938
- Chiarella et al. (2004), *Intraday price reversals in the US stock index
  futures market: A 15-year study*.
  - ScienceDirect page:
    https://www.sciencedirect.com/science/article/pii/S0378426604000949
- Baniya (2024), *Rough Gaps Exist? Opening Gaps Helps To Surge Returns in
  Swing and Intraday Trading*.
  - SSRN PDF:
    https://papers.ssrn.com/sol3/Delivery.cfm/
    SSRN_ID4834097_code6753027.pdf?abstractid=4834097&mirid=1

## Implemented Math Primitives

The new `project.alpha_math.ohlcv` module now exposes the following reusable
primitives:

- Trend and momentum: `ema`, `relative_strength_index`, `macd`,
  `average_directional_index`
- Volatility and channels: `true_range`, `average_true_range`,
  `bollinger_bands`, `donchian_channels`
- Volume confirmation: `on_balance_volume`, `money_flow_index`,
  `relative_volume`
- Candle anatomy: `typical_price`, `candle_body`, `upper_shadow`,
  `lower_shadow`, `close_location_value`
- Price-action patterns: `is_doji`, `is_inside_bar`, `is_outside_bar`,
  `is_bullish_engulfing`, `is_bearish_engulfing`
- Breakout geometry: `breakout_above`, `breakout_below`, `channel_position`

The `project.alpha_math.price_action` module adds:

- Volatility compression and squeeze: `bollinger_bandwidth`,
  `bollinger_percent_b`, `bollinger_squeeze`
- Regime stops and trend followers: `parabolic_sar`, `chandelier_exit`
- Pivot-based support and resistance: `pivot_points`
- ATR risk sizing: `atr_position_size`
- Session breakout logic: `opening_range_breakout`

The `project.alpha_math.market_structure` module adds:

- support and resistance projection: `support_resistance_levels`
- failed-breakout detection: `failed_breakout_signal`
- multi-timeframe confirmation: `multi_timeframe_confirmation`
- gap pressure and fill: `gap_pressure`

The `project.alpha_math.trend_indicators` module adds:

- Aroon and CCI-style trend oscillators: `aroon`, `commodity_channel_index`
- momentum oscillators: `chande_momentum_oscillator`
- cloud structure: `ichimoku_cloud`
- Elder trend power: `elder_ray`
- blended momentum: `know_sure_thing`
- directional oscillators: `vortex_indicator`, `ultimate_oscillator`,
  `williams_r`

The `project.alpha_math.trend_regimes` module adds:

- Keltner Channels: `keltner_channels`
- SuperTrend overlay: `supertrend`
- Choppiness Index: `choppiness_index`
- TRIX oscillator: `trix`

The `project.alpha_math.cycle_indicators` module adds:

- Fisher Transform: `fisher_transform`
- inverse Fisher compression: `inverse_fisher_transform`
- detrended price oscillator: `detrended_price_oscillator`
- Mass Index: `mass_index`

The `project.alpha_math.volume_flow` module adds:

- accumulation/distribution: `accumulation_distribution_line`
- Chaikin flow: `chaikin_money_flow`, `chaikin_oscillator`
- force pressure: `force_index`
- ease of movement: `ease_of_movement`
- price-volume trend: `price_volume_trend`

The `project.alpha_math.volume_profile` module adds:

- point-of-control and value-area projection: `volume_profile_levels`
- profile regime flags: `volume_profile_regime`

The `project.alpha_math.gap_regimes` module adds:

- opening-gap metrics: `opening_gap_metrics`
- opening-gap regime classification: `opening_gap_regime`

The `project.alpha_math.volatility_estimators` module adds:

- close-to-close baseline: `close_to_close_volatility`
- Parkinson range estimator: `parkinson_volatility`
- Garman-Klass estimator: `garman_klass_volatility`
- Rogers-Satchell estimator: `rogers_satchell_volatility`
- Yang-Zhang estimator: `yang_zhang_volatility`

The `project.alpha_math.regime_filters` module adds:

- variance ratio: `variance_ratio`
- Hurst exponent: `hurst_exponent`
- regime snapshot: `volatility_regime_filters`

The `project.alpha_math.regime_filters` module also adds:

- higher-timeframe regime filters: `higher_timeframe_regime_filters`

The `project.alpha_math.trade_profiles` module adds:

- failed-breakout scoring: `failed_breakout_score`
- failed-reversal scoring: `failed_reversal_score`
- hybrid trend/volume composite: `trend_volume_composite`
- hybrid trend/volume score stacks: `hybrid_trend_volume_scores`
- ATR pyramiding and scale-out ladders: `pyramiding_ladder`

The `project.alpha_math.relative_strength` module adds:

- relative strength ratio: `relative_strength_ratio`
- relative strength spread: `relative_strength_spread`
- benchmark-relative overlay: `relative_strength_overlay`
- price/momentum/volume divergence: `divergence_scores`
- multi-horizon relative-strength ranking: `multi_horizon_relative_strength_rank`
- higher-order oscillator divergence stack: `higher_order_divergence_scores`

The `project.alpha_math.market_breadth` module adds:

- market breadth metrics: `market_breadth_metrics`
- relative rotation metrics: `relative_rotation_metrics`
- breadth thrust metrics: `breadth_thrust_metrics`
- breadth thrust composite: `breadth_thrust_composite`
- breadth dispersion metrics: `breadth_dispersion_metrics`
- breadth thrust plus volatility regime: `breadth_thrust_volatility_regime`
- nested-universe breadth normalization: `nested_universe_breadth_metrics`

The `project.alpha_math.oscillator_regimes` module adds:

- oscillator regime clusters: `oscillator_regime_clusters`
- oscillator regime analysis: `oscillator_regime_analysis`
- oscillator orthogonalization: `orthogonalize_oscillators`
- cross-timeframe oscillator cluster persistence:
  `oscillator_cluster_persistence`

## Strategy Families Now Expressible

The point of the math layer is to make these families explicit instead of
re-implementing their formulas in each strategy:

1. Trend following and time-series momentum
2. Donchian and closing-price breakouts
3. Bollinger-style mean reversion and squeeze expansion
4. RSI and MFI exhaustion reversals
5. Candlestick reversal and continuation setups
6. Gap fade and gap continuation setups
7. Support/resistance interaction via channels, pivots, and breakout filters
8. Volume-confirmed continuation and reversal
9. Bollinger squeeze and volatility-compression expansion
10. Parabolic SAR and ATR stop management
11. Opening-range breakout for intraday session structure
12. Support/resistance projection and failed-breakout detection
13. Multi-timeframe confirmation and gap-pressure scoring
14. Aroon, CCI, Ichimoku, Elder Ray, and KST trend-oscillator stacks
15. Chaikin, Force Index, EOM, and price-volume trend flow math
16. Range-based volatility estimation and regime filters
17. Rolling support/resistance trendline projection
18. Rolling volume-profile and liquidity overlays
19. Volatility regime filters and persistence gates
20. Opening-gap continuation and gap-fill regimes
21. Failed-breakout and failed-reversal scoring, trend-volume composites, and
    pyramiding ladders
22. Higher-timeframe regime confirmation and trend gating
23. Hybrid trend/volume score stacks for breakout, pullback, and exhaustion
24. Cross-asset relative-strength overlays and benchmark-relative trend gating
25. Price, momentum, and volume divergence scoring
26. Multi-horizon relative-strength ranking across asset universes
27. Higher-order oscillator and composite-factor divergence stacks
28. Cross-sectional breadth and rotation overlays
29. Relative rotation graph style regime labels
30. Zweig-style breadth thrust composites over sector and asset universes
31. Oscillator regime clustering and factor orthogonalization
32. Breadth dispersion and participation-decay overlays across nested universes
33. Breadth thrust plus volatility-compression regime transitions
34. Cross-timeframe oscillator cluster persistence
35. Nested-universe breadth normalization and expansion factors
36. Directional oscillators and bounded momentum extremes
37. Channel overlays and trend-regime filters
38. Cycle filters and transformed oscillator extremes

## Remaining Research Surface

The current bundle does not exhaust the universe of OHLCV strategy ideas, but
there are no further explicit options called out in this note.
