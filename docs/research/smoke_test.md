# Smoke Test

Use the deterministic fixture data under `tests/fixtures/market_data/NIFTY.csv`.

```bash
python project/main.py init-db --database /tmp/mft_smoke.duckdb
python project/main.py load-ohlcv-csv --file-path tests/fixtures/market_data/NIFTY.csv --asset-symbol NIFTY --database /tmp/mft_smoke.duckdb
python project/main.py run-research-batch --database /tmp/mft_smoke.duckdb
python project/main.py show-validation-failures --database /tmp/mft_smoke.duckdb
python project/main.py replay-evaluate NIFTY 2026-04-24T00:00:00+00:00 short hypothesis:rsi_mean_reversion --database /tmp/mft_smoke.duckdb
python project/main.py backtest-hypothesis hypothesis:rsi_mean_reversion NIFTY 2026-04-20 2026-05-14 --database /tmp/mft_smoke.duckdb
python project/main.py report-hypotheses --horizon 20 --database /tmp/mft_smoke.duckdb
python project/main.py show-trade-idea trade:asset:NIFTY:hypothesis:rsi_mean_reversion:1 --database /tmp/mft_smoke.duckdb
python project/main.py review-trade-idea trade:asset:NIFTY:hypothesis:rsi_mean_reversion:1 approve --reason market_conditions --notes "fixture smoke test" --database /tmp/mft_smoke.duckdb
./scripts/check.sh
```

