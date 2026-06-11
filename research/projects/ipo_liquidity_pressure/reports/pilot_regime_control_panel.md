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
| extreme | application | 10 | -0.5030% | 0.0904% | 5.4487% | volatile |
| extreme | release_5 | 10 | -0.1886% | 0.7895% | 5.4207% | volatile |
| high | application | 4 | 0.4739% | -0.2371% | 5.9578% | volatile |
| high | release_5 | 4 | 0.8095% | -0.1488% | 5.9648% | volatile |
| low | application | 14 | -0.3897% | -0.1792% | 5.5907% | volatile |
| low | release_5 | 14 | 0.3275% | 0.3249% | 5.6474% | volatile |
| medium | application | 10 | 0.1010% | -0.0452% | 2.8647% | volatile |
| medium | release_5 | 10 | 0.1076% | -0.3364% | 2.9350% | volatile |

### Recent Winners 60D Top50
| pressure_class | window_name | observations | mean_abnormal_return | mean_window_nifty_return | mean_issue_to_turnover | dominant_market_regime |
| --- | --- | --- | --- | --- | --- | --- |
| extreme | application | 10 | 0.0990% | 0.0904% | 5.4487% | volatile |
| extreme | release_5 | 10 | 0.2924% | 0.7895% | 5.4207% | volatile |
| high | application | 4 | -0.2749% | -0.2371% | 5.9578% | volatile |
| high | release_5 | 4 | -0.0267% | -0.1488% | 5.9648% | volatile |
| low | application | 14 | 0.1130% | -0.1792% | 5.5907% | volatile |
| low | release_5 | 14 | 0.1535% | 0.3249% | 5.6474% | volatile |
| medium | application | 10 | 0.5738% | -0.0452% | 2.8647% | volatile |
| medium | release_5 | 10 | 0.5607% | -0.3364% | 2.9350% | volatile |

### Cash Source 60D Top50
| pressure_class | window_name | observations | mean_abnormal_return | mean_window_nifty_return | mean_issue_to_turnover | dominant_market_regime |
| --- | --- | --- | --- | --- | --- | --- |
| extreme | application | 10 | 0.1582% | 0.0904% | 5.4487% | volatile |
| extreme | release_5 | 10 | 0.3742% | 0.7895% | 5.4207% | volatile |
| high | application | 4 | 0.4868% | -0.2371% | 5.9578% | volatile |
| high | release_5 | 4 | -0.6508% | -0.1488% | 5.9648% | volatile |
| low | application | 14 | 0.3190% | -0.1792% | 5.5907% | volatile |
| low | release_5 | 14 | 0.1837% | 0.3249% | 5.6474% | volatile |
| medium | application | 10 | -0.0378% | -0.0452% | 2.8647% | volatile |
| medium | release_5 | 10 | -0.1611% | -0.3364% | 2.9350% | volatile |

## Regime Readout

| control_market_regime | window_name | observations | mean_abnormal_return | mean_window_breadth | mean_window_turnover |
| --- | --- | --- | --- | --- | --- |
| volatile | application | 190 | 0.0744% | 40.5541% | 82720.2593 |
| volatile | release_5 | 190 | 0.1222% | 41.7897% | 84172.6968 |

## Reading

- The pressure proxy stays largest for the extreme cases (0.0543 mean issue-to-turnover), which keeps the blocking-liquidity mechanism plausible.
- The control panel does not collapse the sample into one clean regime: all focus windows sit in the volatile bucket.
- Same-sector peers remain split: extreme -0.5030% on application and -0.1886% on release_5, high 0.4739%/0.8095%, low -0.3897%/0.3275%.
- Recent winners are negative on application for extreme 0.0990% and high -0.2749%, while low is 0.1130% and medium is 0.5738%.
- Cash-source names stay positive across pressure classes: extreme 0.1582%/0.3742%, high 0.4868%/-0.6508%, low 0.3190%/0.1837%, medium -0.0378%/-0.1611%.
- The dominant control-state bucket is `volatile`, but the regime split does not explain away the mixed basket behavior.