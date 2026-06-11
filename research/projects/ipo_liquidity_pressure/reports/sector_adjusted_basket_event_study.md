# Sector-Adjusted Basket Event Study

## Objective

Check whether the main basket signals survive a sector-return adjustment, not just the same-sector peer basket.

## Coverage

- Sector mapping is available for 26 of the 38 seed IPO symbols.
- The sector-adjusted basket pass therefore covers 650 of the 950 pilot rows; missing symbols: MEDIASSIST, EUROPRATIK, YATRA, TRUALT, SAATVIK, OMFREIGHT, BRIGHOTEL, GLOTTIS, FABTECH, CHEMPLASTS, FINOPB, KRN.

## Window Reading

### Application

| basket_name | extreme | high | low | medium |
| --- | --- | --- | --- | --- |
| same_sector_peer | 0.005879 | -0.007388 | 0.006850 | -0.007810 |
| recent_winners_60d_top50 | 0.011310 | -0.012608 | 0.011152 | -0.004641 |
| cash_source_60d_top50 | 0.011367 | -0.007752 | 0.013743 | -0.010398 |
| smallcap250 | 0.008957 | -0.013788 | 0.009299 | -0.006192 |
| midcap150 | 0.013891 | -0.012916 | 0.013821 | -0.010065 |

### Release 5

| basket_name | extreme | high | low | medium |
| --- | --- | --- | --- | --- |
| same_sector_peer | -0.003242 | 0.007897 | -0.003351 | -0.002777 |
| recent_winners_60d_top50 | 0.001360 | -0.000524 | -0.003708 | 0.003485 |
| cash_source_60d_top50 | 0.005264 | -0.007680 | -0.005419 | -0.009962 |
| smallcap250 | -0.002193 | 0.000611 | -0.005136 | -0.001542 |
| midcap150 | 0.002110 | -0.000632 | -0.007750 | -0.005332 |


## Interpretation

- Sector adjustment does not cleanly organize the baskets into a monotonic pressure gradient.
- The sector-adjusted basket averages remain mixed across application and release windows.
- Recent winners, cash sources, and the small/midcap baskets remain mixed after sector adjustment.
- The sector proxy layer is useful as a falsification check, but it does not rescue a broad pull/release thesis.