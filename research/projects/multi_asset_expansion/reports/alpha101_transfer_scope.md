# Alpha101 Transfer Scope

This report records the low-compute expansion map while the cache is being
recomputed.

## Current Scope

- Indian ETF transfer is the first executable lane.
- NSE index transfer is non-tradable and stays benchmark-relative.
- NSE equity derivative transfer is continuous-contract only.
- MCX commodity transfer is continuous-contract only.
- Macro, FX, and global ETF proxies stay research-only and non-authoritative.

## Queue Coverage

| asset class | queue file | transfer mode | status |
| --- | --- | --- | --- |
| `indian_etf` | `queues/indian_etfs_queue.yaml` | exact OHLCV transfer | active |
| `indian_index` | `queues/nse_indices_queue.yaml` | index-relative diagnostics | scaffolded |
| `nse_equity_derivative` | `queues/nse_equity_derivatives_queue.yaml` | continuous-contract transfer | scaffolded |
| `mcx_commodity_future` | `queues/mcx_queue.yaml` | continuous-contract transfer | scaffolded |
| `macro_series` | `queues/macro_queue.yaml` | regime overlay | research-only |
| `fx_proxy` | `queues/global_proxy_queue.yaml` | proxy overlay | research-only |
| `global_etf_proxy` | `queues/global_proxy_queue.yaml` | proxy overlay | research-only |

## Done Conditions

- The ETF transfer lane remains explicit and reviewable.
- The new index, derivative, and commodity lanes are visible in the queue map.
- Proxy lanes remain labeled as research-only.

