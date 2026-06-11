# Pressure Gradient Stability

## Objective

Stress-test the one clean sector-adjusted pressure-gradient case against adjacent windows and nearby basket definitions.

## Summary

- Rows analyzed: 15 stability combinations.
- Midcap150 rows analyzed: 10.
- Non-mixed midcap150 rows: 3.
- Non-mixed release_5 sector-adjusted baskets: 1.

## Midcap150 Across Windows

| section | study_type | window_name | pressure_direction | pressure_spearman_rho | pressure_linear_slope | pressure_spread_extreme_minus_low |
| --- | --- | --- | --- | --- | --- | --- |
| midcap_path | raw | application | mixed | 0.400000 | 0.000271 | 0.000443 |
| midcap_path | raw | blocking | insufficient |  |  |  |
| midcap_path | raw | release_3 | mixed | 0.800000 | 0.000686 | 0.001636 |
| midcap_path | raw | release_5 | mixed | 0.200000 | 0.000285 | 0.001205 |
| midcap_path | raw | listing_5 | mixed | -0.600000 | -0.000722 | -0.000919 |
| midcap_path | sector_adjusted | application | mixed | 0.200000 | -0.000264 | 0.000070 |
| midcap_path | sector_adjusted | blocking | insufficient |  |  |  |
| midcap_path | sector_adjusted | release_3 | mixed | 0.600000 | 0.004577 | 0.007949 |
| midcap_path | sector_adjusted | release_5 | nondecreasing | 1.000000 | 0.003428 | 0.009860 |
| midcap_path | sector_adjusted | listing_5 | mixed | 0.400000 | 0.000516 | 0.001446 |

## Release_5 Sector-Adjusted Basket Neighborhood

| section | basket_name | pressure_direction | pressure_spearman_rho | pressure_linear_slope | pressure_spread_extreme_minus_low |
| --- | --- | --- | --- | --- | --- |
| basket_neighborhood | same_sector_peer | mixed | 0.400000 | 0.001100 | 0.000108 |
| basket_neighborhood | recent_winners_60d_top50 | mixed | 0.400000 | 0.001120 | 0.005068 |
| basket_neighborhood | cash_source_60d_top50 | mixed | 0.400000 | 0.003433 | 0.010683 |
| basket_neighborhood | smallcap250 | mixed | 0.400000 | 0.001098 | 0.002943 |
| basket_neighborhood | midcap150 | nondecreasing | 1.000000 | 0.003428 | 0.009860 |

## Reading

- The clean sector-adjusted midcap150 release_5 case does not generalize to adjacent windows.
- The release_5 basket neighborhood remains mixed outside midcap150, so the one clean case looks isolated rather than structural.
- This makes the sector-adjusted gradient look like a narrow lead, not a stable pressure regime.