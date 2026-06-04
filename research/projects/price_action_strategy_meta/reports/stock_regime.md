# Stock Regime Map

## Protocol

- Universe: the top 100 high-vol names from each of `nifty500` and `expanded`.
- Horizons: `1d` and `5d` forward returns, with `5d` used for the main regime tilt readout.
- Regime pairs: high/low vol, bull/bear, bullish/bearish breadth, gap shock up/down, high/low liquidity, and risk on/off.
- News effect proxy: gap shock up vs down.
- The report is a stock-level overlay on top of the sector and selector-gate work.

## Regime Tilt Extremes

### vol_state: `high_vol` vs `low_vol`

Most positive spreads:

| universe | horizon | regime_dimension | positive_state | negative_state | symbol | industry | positive_mean_bps | negative_mean_bps | spread_bps | positive_win_rate | negative_win_rate | positive_obs | negative_obs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nifty500 | 5 | vol_state | high_vol | low_vol | ADANIENT | Metals & Mining | 399.595 | -19.462 | 419.058 | 0.527 | 0.518 | 1646 | 2238 |
| expanded | 5 | vol_state | high_vol | low_vol | ADANIENT | Metals & Mining | 381.899 | -10.368 | 392.268 | 0.522 | 0.521 | 1694 | 2220 |
| expanded | 5 | vol_state | high_vol | low_vol | TATASTEEL | Metals & Mining | 414.184 | 58.526 | 355.658 | 0.514 | 0.546 | 2536 | 2531 |
| nifty500 | 5 | vol_state | high_vol | low_vol | TATASTEEL | Metals & Mining | 413.654 | 74.224 | 339.430 | 0.513 | 0.541 | 2535 | 2536 |
| expanded | 5 | vol_state | high_vol | low_vol | CIPLA | Healthcare | 263.627 | 25.127 | 238.500 | 0.541 | 0.524 | 2536 | 2529 |
| nifty500 | 5 | vol_state | high_vol | low_vol | CIPLA | Healthcare | 261.372 | 24.235 | 237.137 | 0.536 | 0.531 | 2535 | 2535 |
| nifty500 | 5 | vol_state | high_vol | low_vol | CGPOWER | Capital Goods | 316.017 | 100.262 | 215.755 | 0.538 | 0.545 | 1646 | 2239 |
| expanded | 5 | vol_state | high_vol | low_vol | CGPOWER | Capital Goods | 301.306 | 106.567 | 194.740 | 0.536 | 0.546 | 1694 | 2222 |

Most negative spreads:

| universe | horizon | regime_dimension | positive_state | negative_state | symbol | industry | positive_mean_bps | negative_mean_bps | spread_bps | positive_win_rate | negative_win_rate | positive_obs | negative_obs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nifty500 | 5 | vol_state | high_vol | low_vol | HINDZINC | Metals & Mining | 79.339 | 1333.972 | -1254.633 | 0.409 | 0.430 | 1635 | 2235 |
| nifty500 | 5 | vol_state | high_vol | low_vol | SAMMAANCAP | Financial Services | -94.679 | 98.034 | -192.713 | 0.472 | 0.526 | 557 | 1337 |
| nifty500 | 5 | vol_state | high_vol | low_vol | BALRAMCHIN | Fast Moving Consumer Goods | 127.220 | 254.098 | -126.878 | 0.546 | 0.483 | 1646 | 2239 |
| nifty500 | 5 | vol_state | high_vol | low_vol | GLENMARK | Healthcare | 170.615 | 257.680 | -87.064 | 0.547 | 0.542 | 1646 | 2239 |
| expanded | 5 | vol_state | high_vol | low_vol | EDELWEISS | Financial Services | -8.709 | 68.430 | -77.139 | 0.478 | 0.486 | 1113 | 1706 |
| expanded | 5 | vol_state | high_vol | low_vol | GLENMARK | Healthcare | 165.521 | 240.935 | -75.414 | 0.545 | 0.545 | 1694 | 2222 |
| expanded | 5 | vol_state | high_vol | low_vol | BALRAMCHIN | Fast Moving Consumer Goods | 144.072 | 217.674 | -73.602 | 0.554 | 0.485 | 1694 | 2222 |
| nifty500 | 5 | vol_state | high_vol | low_vol | JUBLPHARMA | Healthcare | 127.984 | 176.340 | -48.356 | 0.550 | 0.510 | 1645 | 2239 |

### trend_state: `bull` vs `bear`

Most positive spreads:

| universe | horizon | regime_dimension | positive_state | negative_state | symbol | industry | positive_mean_bps | negative_mean_bps | spread_bps | positive_win_rate | negative_win_rate | positive_obs | negative_obs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nifty500 | 5 | trend_state | bull | bear | HINDZINC | Metals & Mining | 1082.758 | 54.442 | 1028.316 | 0.365 | 0.540 | 2791 | 654 |
| nifty500 | 5 | trend_state | bull | bear | VOLTAS | Consumer Durables | 288.932 | -77.816 | 366.748 | 0.563 | 0.468 | 2806 | 654 |
| expanded | 5 | trend_state | bull | bear | VOLTAS | Consumer Durables | 291.056 | -74.134 | 365.190 | 0.563 | 0.470 | 2756 | 651 |
| expanded | 5 | trend_state | bull | bear | ADANIENT | Metals & Mining | 307.267 | 27.079 | 280.188 | 0.521 | 0.519 | 2754 | 651 |
| nifty500 | 5 | trend_state | bull | bear | ADANIENT | Metals & Mining | 293.717 | 20.705 | 273.012 | 0.512 | 0.512 | 2804 | 654 |
| expanded | 5 | trend_state | bull | bear | GLENMARK | Healthcare | 253.264 | -7.617 | 260.881 | 0.545 | 0.542 | 2756 | 651 |
| nifty500 | 5 | trend_state | bull | bear | GLENMARK | Healthcare | 244.473 | 1.850 | 242.624 | 0.541 | 0.537 | 2806 | 654 |
| nifty500 | 5 | trend_state | bull | bear | JUBLPHARMA | Healthcare | 176.818 | -63.410 | 240.227 | 0.523 | 0.476 | 2804 | 654 |

Most negative spreads:

| universe | horizon | regime_dimension | positive_state | negative_state | symbol | industry | positive_mean_bps | negative_mean_bps | spread_bps | positive_win_rate | negative_win_rate | positive_obs | negative_obs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nifty500 | 5 | trend_state | bull | bear | TATACOMM | Telecommunication | 42.276 | 101.056 | -58.780 | 0.513 | 0.541 | 2800 | 654 |
| expanded | 5 | trend_state | bull | bear | TATACOMM | Telecommunication | 45.499 | 100.701 | -55.202 | 0.515 | 0.541 | 2750 | 651 |
| nifty500 | 5 | trend_state | bull | bear | DRREDDY | Healthcare | 47.570 | 94.503 | -46.932 | 0.535 | 0.574 | 3447 | 863 |
| expanded | 5 | trend_state | bull | bear | DRREDDY | Healthcare | 48.736 | 94.320 | -45.584 | 0.538 | 0.573 | 3387 | 876 |
| expanded | 5 | trend_state | bull | bear | HINDUNILVR | Fast Moving Consumer Goods | 31.570 | 68.912 | -37.341 | 0.505 | 0.580 | 3393 | 876 |
| nifty500 | 5 | trend_state | bull | bear | HINDUNILVR | Fast Moving Consumer Goods | 32.422 | 65.376 | -32.954 | 0.505 | 0.581 | 3453 | 863 |
| nifty500 | 5 | trend_state | bull | bear | HEROMOTOCO | Automobile and Auto Components | 42.241 | 72.817 | -30.576 | 0.532 | 0.575 | 2800 | 654 |
| expanded | 5 | trend_state | bull | bear | HEROMOTOCO | Automobile and Auto Components | 46.473 | 76.272 | -29.799 | 0.536 | 0.581 | 2750 | 651 |

### breadth_state: `bullish` vs `bearish`

Most positive spreads:

| universe | horizon | regime_dimension | positive_state | negative_state | symbol | industry | positive_mean_bps | negative_mean_bps | spread_bps | positive_win_rate | negative_win_rate | positive_obs | negative_obs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nifty500 | 5 | breadth_state | bullish | bearish | ADANIENT | Metals & Mining | 288.921 | -87.841 | 376.763 | 0.544 | 0.490 | 1640 | 1354 |
| expanded | 5 | breadth_state | bullish | bearish | ADANIENT | Metals & Mining | 281.813 | -87.342 | 369.155 | 0.540 | 0.493 | 1645 | 1384 |
| nifty500 | 5 | breadth_state | bullish | bearish | VOLTAS | Consumer Durables | 282.287 | 1.600 | 280.687 | 0.557 | 0.503 | 1640 | 1355 |
| expanded | 5 | breadth_state | bullish | bearish | VOLTAS | Consumer Durables | 283.521 | 6.543 | 276.978 | 0.557 | 0.501 | 1645 | 1385 |
| nifty500 | 5 | breadth_state | bullish | bearish | HFCL | Telecommunication | 171.524 | -59.374 | 230.897 | 0.470 | 0.410 | 1639 | 1333 |
| expanded | 5 | breadth_state | bullish | bearish | MARKSANS | Healthcare | 172.346 | -58.199 | 230.545 | 0.466 | 0.379 | 1644 | 1378 |
| nifty500 | 5 | breadth_state | bullish | bearish | BEML | Capital Goods | 152.880 | -72.981 | 225.861 | 0.553 | 0.449 | 1639 | 1353 |
| nifty500 | 5 | breadth_state | bullish | bearish | ANANTRAJ | Realty | 172.135 | -46.896 | 219.031 | 0.535 | 0.470 | 1392 | 1112 |

Most negative spreads:

| universe | horizon | regime_dimension | positive_state | negative_state | symbol | industry | positive_mean_bps | negative_mean_bps | spread_bps | positive_win_rate | negative_win_rate | positive_obs | negative_obs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nifty500 | 5 | breadth_state | bullish | bearish | TATASTEEL | Metals & Mining | 149.223 | 307.118 | -157.895 | 0.548 | 0.486 | 1642 | 2400 |
| expanded | 5 | breadth_state | bullish | bearish | TATASTEEL | Metals & Mining | 150.646 | 304.817 | -154.171 | 0.545 | 0.487 | 1647 | 2425 |
| nifty500 | 5 | breadth_state | bullish | bearish | BALRAMCHIN | Fast Moving Consumer Goods | 88.862 | 146.877 | -58.015 | 0.528 | 0.493 | 1640 | 1355 |
| nifty500 | 5 | breadth_state | bullish | bearish | IOC | Oil Gas & Consumable Fuels | 84.051 | 136.496 | -52.446 | 0.541 | 0.474 | 1641 | 2348 |
| expanded | 5 | breadth_state | bullish | bearish | BALRAMCHIN | Fast Moving Consumer Goods | 91.729 | 143.755 | -52.026 | 0.528 | 0.494 | 1645 | 1385 |
| expanded | 5 | breadth_state | bullish | bearish | IOC | Oil Gas & Consumable Fuels | 82.397 | 133.624 | -51.226 | 0.541 | 0.475 | 1646 | 2373 |
| expanded | 5 | breadth_state | bullish | bearish | INFY | Information Technology | 37.853 | 81.397 | -43.544 | 0.551 | 0.563 | 1647 | 2425 |
| expanded | 5 | breadth_state | bullish | bearish | WIPRO | Information Technology | 34.459 | 75.934 | -41.475 | 0.534 | 0.501 | 1647 | 2425 |

### gap_state: `up_gap_shock` vs `down_gap_shock`

Most positive spreads:

| universe | horizon | regime_dimension | positive_state | negative_state | symbol | industry | positive_mean_bps | negative_mean_bps | spread_bps | positive_win_rate | negative_win_rate | positive_obs | negative_obs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| expanded | 5 | gap_state | up_gap_shock | down_gap_shock | ADANIENT | Metals & Mining | 542.757 | -70.486 | 613.244 | 0.500 | 0.522 | 642 | 299 |
| nifty500 | 5 | gap_state | up_gap_shock | down_gap_shock | GLENMARK | Healthcare | 495.447 | 65.003 | 430.443 | 0.572 | 0.574 | 670 | 298 |
| expanded | 5 | gap_state | up_gap_shock | down_gap_shock | GLENMARK | Healthcare | 505.015 | 113.406 | 391.609 | 0.560 | 0.579 | 643 | 299 |
| nifty500 | 5 | gap_state | up_gap_shock | down_gap_shock | ADANIENT | Metals & Mining | 454.773 | 117.504 | 337.269 | 0.495 | 0.523 | 669 | 298 |
| nifty500 | 5 | gap_state | up_gap_shock | down_gap_shock | RPOWER | Power | 202.041 | -45.879 | 247.920 | 0.556 | 0.482 | 279 | 195 |
| expanded | 5 | gap_state | up_gap_shock | down_gap_shock | RPOWER | Power | 208.988 | -31.485 | 240.473 | 0.561 | 0.500 | 269 | 192 |
| nifty500 | 5 | gap_state | up_gap_shock | down_gap_shock | JUBLPHARMA | Healthcare | 179.687 | -60.061 | 239.748 | 0.545 | 0.490 | 670 | 298 |
| nifty500 | 5 | gap_state | up_gap_shock | down_gap_shock | NCC | Construction | 226.800 | 6.781 | 220.019 | 0.442 | 0.425 | 658 | 292 |

Most negative spreads:

| universe | horizon | regime_dimension | positive_state | negative_state | symbol | industry | positive_mean_bps | negative_mean_bps | spread_bps | positive_win_rate | negative_win_rate | positive_obs | negative_obs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nifty500 | 5 | gap_state | up_gap_shock | down_gap_shock | TATASTEEL | Metals & Mining | 293.550 | 749.550 | -456.000 | 0.540 | 0.488 | 1282 | 621 |
| expanded | 5 | gap_state | up_gap_shock | down_gap_shock | TATASTEEL | Metals & Mining | 297.642 | 733.026 | -435.384 | 0.538 | 0.492 | 1265 | 638 |
| expanded | 5 | gap_state | up_gap_shock | down_gap_shock | IOC | Oil Gas & Consumable Fuels | 63.653 | 332.424 | -268.771 | 0.485 | 0.487 | 1255 | 635 |
| nifty500 | 5 | gap_state | up_gap_shock | down_gap_shock | IOC | Oil Gas & Consumable Fuels | 61.274 | 326.920 | -265.646 | 0.490 | 0.477 | 1272 | 618 |
| expanded | 5 | gap_state | up_gap_shock | down_gap_shock | YESBANK | Financial Services | 95.153 | 225.813 | -130.660 | 0.549 | 0.506 | 364 | 231 |
| nifty500 | 5 | gap_state | up_gap_shock | down_gap_shock | YESBANK | Financial Services | 105.479 | 223.110 | -117.630 | 0.545 | 0.513 | 389 | 238 |
| expanded | 5 | gap_state | up_gap_shock | down_gap_shock | TRIVENI | Fast Moving Consumer Goods | 122.349 | 158.958 | -36.609 | 0.500 | 0.576 | 354 | 229 |
| expanded | 5 | gap_state | up_gap_shock | down_gap_shock | PFC | Financial Services | 105.041 | 115.621 | -10.580 | 0.568 | 0.583 | 315 | 218 |

### liquidity_state: `high_liquidity` vs `low_liquidity`

Most positive spreads:

| universe | horizon | regime_dimension | positive_state | negative_state | symbol | industry | positive_mean_bps | negative_mean_bps | spread_bps | positive_win_rate | negative_win_rate | positive_obs | negative_obs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| expanded | 5 | liquidity_state | high_liquidity | low_liquidity | TRIVENI | Fast Moving Consumer Goods | 78.845 | 24.687 | 54.158 | 0.506 | 0.455 | 2498 | 200 |
| expanded | 5 | liquidity_state | high_liquidity | low_liquidity | HINDALCO | Metals & Mining | 57.265 | 29.960 | 27.304 | 0.554 | 0.514 | 2498 | 2502 |
| nifty500 | 5 | liquidity_state | high_liquidity | low_liquidity | HINDALCO | Metals & Mining | 57.151 | 32.281 | 24.870 | 0.554 | 0.515 | 2498 | 2501 |
| expanded | 5 | liquidity_state | high_liquidity | low_liquidity | MASTEK | Information Technology | 75.568 | 55.577 | 19.991 | 0.512 | 0.528 | 2498 | 913 |
| expanded | 5 | liquidity_state | high_liquidity | low_liquidity | ESCORTS | Capital Goods | 61.361 | 41.618 | 19.743 | 0.532 | 0.473 | 2498 | 2499 |
| expanded | 5 | liquidity_state | high_liquidity | low_liquidity | MRPL | Oil Gas & Consumable Fuels | 55.783 | 39.619 | 16.164 | 0.483 | 0.378 | 2498 | 2499 |
| nifty500 | 5 | liquidity_state | high_liquidity | low_liquidity | ESCORTS | Capital Goods | 60.360 | 45.245 | 15.115 | 0.532 | 0.474 | 2498 | 2498 |
| expanded | 5 | liquidity_state | high_liquidity | low_liquidity | EDELWEISS | Financial Services | 58.381 | 43.686 | 14.695 | 0.491 | 0.500 | 2483 | 36 |

Most negative spreads:

| universe | horizon | regime_dimension | positive_state | negative_state | symbol | industry | positive_mean_bps | negative_mean_bps | spread_bps | positive_win_rate | negative_win_rate | positive_obs | negative_obs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nifty500 | 5 | liquidity_state | high_liquidity | low_liquidity | HINDZINC | Metals & Mining | 53.895 | 1299.190 | -1245.294 | 0.524 | 0.096 | 2498 | 882 |
| nifty500 | 5 | liquidity_state | high_liquidity | low_liquidity | BALRAMCHIN | Fast Moving Consumer Goods | 63.732 | 698.017 | -634.284 | 0.526 | 0.505 | 2498 | 912 |
| expanded | 5 | liquidity_state | high_liquidity | low_liquidity | BALRAMCHIN | Fast Moving Consumer Goods | 62.337 | 691.803 | -629.466 | 0.525 | 0.503 | 2498 | 913 |
| expanded | 5 | liquidity_state | high_liquidity | low_liquidity | VOLTAS | Consumer Durables | 45.952 | 617.250 | -571.298 | 0.532 | 0.559 | 2498 | 913 |
| nifty500 | 5 | liquidity_state | high_liquidity | low_liquidity | VOLTAS | Consumer Durables | 47.349 | 618.202 | -570.853 | 0.533 | 0.562 | 2498 | 912 |
| nifty500 | 5 | liquidity_state | high_liquidity | low_liquidity | GLENMARK | Healthcare | 45.319 | 610.289 | -564.969 | 0.532 | 0.558 | 2498 | 912 |
| expanded | 5 | liquidity_state | high_liquidity | low_liquidity | GLENMARK | Healthcare | 47.493 | 610.387 | -562.894 | 0.535 | 0.556 | 2498 | 913 |
| nifty500 | 5 | liquidity_state | high_liquidity | low_liquidity | TATASTEEL | Metals & Mining | 51.286 | 563.313 | -512.026 | 0.552 | 0.524 | 2498 | 2501 |

### risk_state: `risk_on` vs `risk_off`

Most positive spreads:

| universe | horizon | regime_dimension | positive_state | negative_state | symbol | industry | positive_mean_bps | negative_mean_bps | spread_bps | positive_win_rate | negative_win_rate | positive_obs | negative_obs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nifty500 | 5 | risk_state | risk_on | risk_off | VOLTAS | Consumer Durables | 380.594 | -247.769 | 628.362 | 0.570 | 0.399 | 949 | 173 |
| expanded | 5 | risk_state | risk_on | risk_off | VOLTAS | Consumer Durables | 388.258 | -199.108 | 587.366 | 0.568 | 0.401 | 929 | 192 |
| nifty500 | 5 | risk_state | risk_on | risk_off | CHENNPETRO | Oil Gas & Consumable Fuels | 176.010 | -273.910 | 449.920 | 0.580 | 0.393 | 949 | 173 |
| nifty500 | 5 | risk_state | risk_on | risk_off | SUZLON | Capital Goods | 127.845 | -304.725 | 432.571 | 0.485 | 0.382 | 851 | 173 |
| expanded | 5 | risk_state | risk_on | risk_off | CHENNPETRO | Oil Gas & Consumable Fuels | 169.648 | -257.527 | 427.176 | 0.573 | 0.406 | 929 | 192 |
| nifty500 | 5 | risk_state | risk_on | risk_off | WOCKPHARMA | Healthcare | 130.436 | -190.745 | 321.180 | 0.544 | 0.370 | 949 | 173 |
| nifty500 | 5 | risk_state | risk_on | risk_off | JUBLPHARMA | Healthcare | 100.680 | -216.028 | 316.708 | 0.492 | 0.445 | 949 | 173 |
| expanded | 5 | risk_state | risk_on | risk_off | WOCKPHARMA | Healthcare | 123.117 | -190.016 | 313.133 | 0.531 | 0.391 | 929 | 192 |

Most negative spreads:

| universe | horizon | regime_dimension | positive_state | negative_state | symbol | industry | positive_mean_bps | negative_mean_bps | spread_bps | positive_win_rate | negative_win_rate | positive_obs | negative_obs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nifty500 | 5 | risk_state | risk_on | risk_off | TATASTEEL | Metals & Mining | 57.789 | 427.393 | -369.604 | 0.553 | 0.477 | 949 | 237 |
| expanded | 5 | risk_state | risk_on | risk_off | TATASTEEL | Metals & Mining | 69.243 | 400.570 | -331.327 | 0.562 | 0.490 | 929 | 245 |
| nifty500 | 5 | risk_state | risk_on | risk_off | DRREDDY | Healthcare | 11.744 | 206.483 | -194.739 | 0.536 | 0.650 | 949 | 237 |
| expanded | 5 | risk_state | risk_on | risk_off | DRREDDY | Healthcare | 10.342 | 196.881 | -186.539 | 0.538 | 0.649 | 929 | 245 |
| nifty500 | 5 | risk_state | risk_on | risk_off | IOC | Oil Gas & Consumable Fuels | 91.584 | 252.513 | -160.929 | 0.543 | 0.549 | 949 | 237 |
| expanded | 5 | risk_state | risk_on | risk_off | IOC | Oil Gas & Consumable Fuels | 86.528 | 243.989 | -157.461 | 0.540 | 0.555 | 929 | 245 |
| nifty500 | 5 | risk_state | risk_on | risk_off | TATACOMM | Telecommunication | 48.812 | 191.623 | -142.810 | 0.519 | 0.561 | 949 | 173 |
| expanded | 5 | risk_state | risk_on | risk_off | TATACOMM | Telecommunication | 44.946 | 186.130 | -141.184 | 0.507 | 0.573 | 929 | 192 |

## Notable Stocks

- The summary CSV carries the full long-form stock/state panel for downstream analysis.
- The spread CSV is the cleaner gate input: it shows which names tilt into one regime and away from the opposite one.

## Takeaway

- Stock behavior is not uniform across regimes; the strongest tilts are concentrated in reversal-heavy names during high-vol, bear, risk-off, and gap-shock states.
- The stock map is meant to feed the selector as context, not to turn into a naive always-on stock picker.