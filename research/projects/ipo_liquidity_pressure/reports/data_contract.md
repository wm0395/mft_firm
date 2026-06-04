# IPO Data Contract

The first pass needs explicit, point-in-time data categories.

The canonical IPO event export is `ipo_events.csv`.

## IPO-Level Fields

- company_name
- symbol_after_listing
- sector or industry
- issue_size
- fresh_issue_amount
- offer_for_sale_amount
- price_band
- final_issue_price
- market_cap_at_listing
- ipo_open_date
- ipo_close_date
- allotment_date
- listing_date
- subscription_total
- subscription_retail
- subscription_nii
- subscription_qib
- listing_gain_or_loss

## Market-Level Fields

- index returns
- cash market turnover
- delivery volume
- breadth and advance-decline measures
- market volatility
- flow regime labels
- sector index returns

## Stock-Level Fields

- OHLCV
- adjusted returns
- turnover
- market capitalization
- free-float market capitalization
- liquidity measures
- momentum
- volatility
- sector classification

## Derived Variables

- IPO pressure score
- subscription pressure score
- retail pressure score
- NII pressure score
- vulnerability score
- abnormal return by window
- reversal score
- pull/release case label

## Quality Rules

- Dates must be logically ordered.
- Mainboard and SME IPOs must be separated in the first pass.
- No lookahead is allowed in derived features.
- Missing critical dates should fail the record, not be silently imputed.
- When the official allotment notice splits NII into `₹0.2m-₹1.0m` and
  `>₹1.0m` buckets, keep both subcategory ratios if available.
