# IPO Regime Control Panel

## Objective

Check whether the pilot pull-and-release signal survives conditioning on broad-market regime, breadth, and turnover pressure.

## Controls

- Control date: the previous trading day before the measured window starts.
- Market regime: NIFTY 20-bar snapshot compressed into bull, bear, volatile, or calm.
- Breadth proxy: average share of positive returns across the expanded high-volatility parent universe.
- Pressure proxy: IPO issue size divided by trailing 20-day expanded-universe turnover in crore INR.

## Basket Readout

### Same Sector Peer
| pressure_class | window_name | observations | mean_abnormal_return | mean_window_nifty_return | mean_issue_to_turnover | dominant_market_regime |
| --- | --- | --- | --- | --- | --- | --- |
| extreme | application | 6 | -0.1358% | 0.0073% | 6.3449% | volatile |
| extreme | release_5 | 6 | -0.5637% | 1.2020% | 6.2455% | volatile |
| high | application | 4 | 0.4739% | -0.2371% | 5.9578% | volatile |
| high | release_5 | 4 | 0.8095% | -0.1488% | 5.9648% | volatile |
| low | application | 10 | -0.3214% | -0.4671% | 6.5609% | volatile |
| low | release_5 | 10 | 0.3167% | -0.2798% | 6.6413% | volatile |
| medium | application | 8 | 0.0006% | -0.1065% | 3.0168% | volatile |
| medium | release_5 | 8 | 0.3139% | -0.5861% | 3.0972% | volatile |

### Recent Winners 60D Top50
| pressure_class | window_name | observations | mean_abnormal_return | mean_window_nifty_return | mean_issue_to_turnover | dominant_market_regime |
| --- | --- | --- | --- | --- | --- | --- |
| extreme | application | 6 | 0.0506% | 0.0073% | 6.3449% | volatile |
| extreme | release_5 | 6 | 0.1569% | 1.2020% | 6.2455% | volatile |
| high | application | 4 | -0.2749% | -0.2371% | 5.9578% | volatile |
| high | release_5 | 4 | -0.0267% | -0.1488% | 5.9648% | volatile |
| low | application | 10 | -0.0288% | -0.4671% | 6.5609% | volatile |
| low | release_5 | 10 | 0.4909% | -0.2798% | 6.6413% | volatile |
| medium | application | 8 | 0.5322% | -0.1065% | 3.0168% | volatile |
| medium | release_5 | 8 | 0.1511% | -0.5861% | 3.0972% | volatile |

### Cash Source 60D Top50
| pressure_class | window_name | observations | mean_abnormal_return | mean_window_nifty_return | mean_issue_to_turnover | dominant_market_regime |
| --- | --- | --- | --- | --- | --- | --- |
| extreme | application | 6 | 0.1726% | 0.0073% | 6.3449% | volatile |
| extreme | release_5 | 6 | 0.7657% | 1.2020% | 6.2455% | volatile |
| high | application | 4 | 0.4868% | -0.2371% | 5.9578% | volatile |
| high | release_5 | 4 | -0.6508% | -0.1488% | 5.9648% | volatile |
| low | application | 10 | 0.2450% | -0.4671% | 6.5609% | volatile |
| low | release_5 | 10 | -0.1164% | -0.2798% | 6.6413% | volatile |
| medium | application | 8 | -0.0265% | -0.1065% | 3.0168% | volatile |
| medium | release_5 | 8 | -0.0670% | -0.5861% | 3.0972% | volatile |

## Regime Readout

| control_market_regime | window_name | observations | mean_abnormal_return | mean_window_breadth | mean_window_turnover |
| --- | --- | --- | --- | --- | --- |
| volatile | application | 140 | 0.0815% | 41.8423% | 87163.0422 |
| volatile | release_5 | 140 | 0.0890% | 41.7487% | 84935.4229 |

## Reading

- The pressure proxy stays largest for the extreme cases (0.0630 mean issue-to-turnover), which keeps the blocking-liquidity mechanism plausible.
- The control panel does not collapse the sample into one clean regime: all focus windows sit in the volatile bucket.
- Same-sector peers remain split: extreme -0.1358% on application and -0.5637% on release_5, high 0.4739%/0.8095%, low -0.3214%/0.3167%.
- Recent winners are negative on application for extreme 0.0506% and high -0.2749%, while low is -0.0288% and medium is 0.5322%.
- Cash-source names stay positive across pressure classes: extreme 0.1726%/0.7657%, high 0.4868%/-0.6508%, low 0.2450%/-0.1164%, medium -0.0265%/-0.0670%.
- The dominant control-state bucket is `volatile`, but the regime split does not explain away the mixed basket behavior.