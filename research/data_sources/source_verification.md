# Source Verification

This document records the current official legal posture for the initial data
source candidates. It is a review note, not a production approval.

## Verified posture

| source_id | official_url | posture | reason |
| --- | --- | --- | --- |
| `nse_official_reports` | https://www.nseindia.com/static/nse-terms-of-use | `restricted` | NSE terms prohibit systematic or automated data collection and describe website content as NSE-owned or licensed content. NSE data policy also requires relevant agreements for market data and limits redistribution. |
| `mcx_official_bhavcopy` | https://www.mcxindia.com/terms-and-conditions-of-usage-for-website | `restricted` | MCX terms prohibit systematic or automated data collection, copying, and redistribution without prior written permission. |
| `fred_api` | https://fred.stlouisfed.org/docs/api/terms_of_use.html | `restricted` | FRED API use is allowed under the posted terms, but third-party series ownership and copyright restrictions remain in force, so source-level research use is not blanket-approved. |
| `stooq_free_daily` | https://stooq.com/stooq/ | `unknown` | The site footer exposes a terms-of-service link, but the public terms target was not retrievable in this environment. Treat as unverified pending legal review. |
| `alpha_vantage_free_tier` | https://www.alphavantage.co/terms_of_service/ | `restricted` | Alpha Vantage treats research, testing, and monitoring as commercial use; the free tier is personal, non-commercial use only unless a separate agreement is in place. |

## Current operating rule

- No source above is production-ready.
- No source may be promoted until adapter behavior, legal posture, and quality
  checks are all explicit.
- Unknown or restricted posture stays visible in the registry and reports.
