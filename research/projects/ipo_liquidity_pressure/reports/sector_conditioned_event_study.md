# Sector-Conditioned Event Study

## Objective

Test whether the same-sector peer signal survives a sector-return adjustment using the new sector proxy panel.

## Coverage

- Sector mapping is available for 26 of the 38 seed IPO symbols in the expanded-parent panel.
- Missing from the sector map for this pass: MEDIASSIST, EUROPRATIK, YATRA, TRUALT, SAATVIK, OMFREIGHT, BRIGHOTEL, GLOTTIS, FABTECH, CHEMPLASTS, FINOPB, KRN.

## Same-Sector Peer Reading

| pressure_class | raw_abnormal_return | sector_window_return | sector_adjusted_abnormal_return |
| --- | --- | --- | --- |
| extreme | -0.005030 | -0.010909 | 0.005879 |
| high | 0.004739 | 0.012127 | -0.007388 |
| medium | 0.001010 | 0.008820 | -0.007810 |
| low | -0.003897 | -0.010747 | 0.006850 |

| pressure_class | raw_abnormal_return | sector_window_return | sector_adjusted_abnormal_return |
| --- | --- | --- | --- |
| extreme | -0.001886 | 0.001357 | -0.003242 |
| high | 0.008095 | 0.000198 | 0.007897 |
| medium | 0.001076 | 0.003852 | -0.002777 |
| low | 0.003275 | 0.006625 | -0.003351 |

## Interpretation

- The sector layer gives a direct falsification check for the same-sector basket instead of relying only on broad-market adjustment.
- The sector-adjusted same-sector peer averages stay mixed across pressure buckets in both windows.
- If the sector-adjusted same-sector peer averages remain mixed, sector drift is not rescuing the pull/release story.
- The sector proxy panel is helpful, but it still does not replace direct turnover or delivery history.