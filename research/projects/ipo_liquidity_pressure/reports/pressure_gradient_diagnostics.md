# Pressure Gradient Diagnostics

## Objective

Test whether any basket/window pair shows a stable pressure gradient after raw and sector-adjusted conditioning.

## Summary

- Rows analyzed: 20 basket-window-study combinations.
- Non-mixed pressure directions: 1.
- Strong gradients with |Spearman rho| >= 0.8: 1.

## Top Gradients by |rho|

| study_type | window_name | basket_name | pressure_direction | pressure_spearman_rho | pressure_linear_slope | pressure_spread_extreme_minus_low |
| --- | --- | --- | --- | --- | --- | --- |
| sector_adjusted | release_5 | midcap150 | nondecreasing | 1.000000 | 0.003428 | 0.009860 |
| raw | application | smallcap250 | mixed | -0.800000 | -0.000654 | -0.001248 |
| raw | application | recent_winners_60d_top50 | mixed | -0.600000 | -0.000891 | -0.000140 |
| raw | application | midcap150 | mixed | 0.400000 | 0.000271 | 0.000443 |
| raw | release_5 | same_sector_peer | mixed | -0.400000 | -0.000846 | -0.005160 |
| raw | release_5 | smallcap250 | mixed | -0.400000 | -0.000095 | -0.000236 |
| sector_adjusted | application | smallcap250 | mixed | -0.400000 | -0.000862 | -0.000341 |
| sector_adjusted | release_5 | cash_source_60d_top50 | mixed | 0.400000 | 0.003433 | 0.010683 |
| sector_adjusted | release_5 | recent_winners_60d_top50 | mixed | 0.400000 | 0.001120 | 0.005068 |
| sector_adjusted | release_5 | same_sector_peer | mixed | 0.400000 | 0.001100 | 0.000108 |

## Reading

- The sector-adjusted basket layer remains mixed, and the raw layer does not rescue a cleaner ordering.
- The only non-mixed row is sector_adjusted / release_5 / midcap150, which orders low -> medium -> high -> extreme and produces rho 1.0.
- A few basket/window pairs show partial ordering, but the overall pattern is not a stable monotonic pressure gradient.
- This keeps the hypothesis in the falsification zone rather than promoting it into a tradable rule.