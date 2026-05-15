# MFT Firm

Deterministic market research platform for signal generation, hypothesis evaluation, validation, trade idea generation, replay analysis, and backtesting.

## Setup

Create or activate a Python 3.12 virtual environment, then install the project dependencies:

```bash
pip install -r project/requirements.txt
pip install -e ./codex_cli
```

Core runtime dependencies:
- `duckdb`
- `mypy`

## Entry Point

The project CLI is exposed through `project/main.py`, which delegates to the stabilized command handlers in `project/cli.py`.

Examples:

```bash
python project/main.py init-db
python project/main.py load-market-collector --source-database /path/to/market.duckdb --symbol AAPL
python project/main.py run-batch NIFTY
python project/main.py summarize-batch NIFTY
python project/main.py replay-evaluate AAPL 2026-05-01T10:00:00Z long hypothesis:rsi_mean_reversion
```

All commands accept `--database`, which defaults to `project_mft.duckdb`.

`init-db` is the only command that bootstraps schema. Read-only reporting commands open the database without writing.
Batch and mutation commands emit a structured JSON envelope with `status`, `command`, and `result` or `error`.

## market_collector Integration

If you already offload OHLCV data with `~/market_collector`, import that DuckDB output into this project with:

```bash
python project/main.py load-market-collector \
  --source-database /path/to/market.duckdb \
  --symbol AAPL
```

The loader reads rows from the `ohlcv` table, keeps the latest row per symbol and timestamp, and persists matching `assets`, `raw_market_data`, and close-price `raw_data` records.

## Main Commands

Pipeline and execution:
- `init-db`
- `load-market-collector --source-database <duckdb> [--symbol ...] [--resolution ...]`
- `load-ohlcv-csv --file-path <csv> --asset-symbol <symbol>`
- `run-batch <asset_id>`
- `summarize-batch <asset_id>`
- `review-trade-idea <trade_id> <approve|reject|watchlist>`

Research and evaluation:
- `replay-evaluate <asset_symbol> <timestamp> <direction> <hypothesis_id>`
- `backtest-hypothesis <hypothesis_id> <asset_symbol> <start_date> <end_date>`
- `backtest-results`
- `report-hypotheses --horizon {1,5,20}`
- `hypothesis-performance`

Inspection and reporting:
- `show-trade-idea <trade_id>`
- `show-hypothesis-evaluations [--asset-id ...] [--hypothesis-id ...]`
- `show-validation-failures`
- `show-competition [--asset-id ...] [--direction ...]`
- `show-explanation <evaluation_id>`
- `show-signal-lineage <asset_id>`
- `show-validation-path <evaluation_id>`
- `list-rejected-hypotheses`
- `regime-analysis <asset_symbol>`
- `lineage-trace [--signal-type ...] [--hypothesis-id ...]`
- `position-management [--asset-id ...] [--hypothesis-id ...] [--status open|closed]`
- `advanced-report <hypothesis_id> [--asset-id ...]`

## Data Model

The database schema now includes:
- `raw_market_data`
- `raw_data`
- `assets`
- `signals`
- `signal_registry`
- `hypothesis_evaluations`
- `signal_evaluations`
- `backtests`
- `hypotheses`
- `hypothesis_signal_map`
- `trade_ideas`
- `decisions`
- `positions`

The exported schema contract used by tests is `project.data.schema.REQUIRED_TABLES`.

## Architecture

Enforced layer order:

```text
data -> signals -> hypotheses -> trade_engine -> decision
```

Project constraints in practice:
- no upward imports across those layers
- immutable dataclasses for core models
- deterministic timestamps using timezone-aware UTC
- no runtime monkey patching

## Quality Gates

Current expected checks:

```bash
python -m pytest
python -m ruff check .
python -m mypy
```

Single local command:

```bash
./scripts/check.sh
```

`mypy` is intentionally scoped in `pyproject.toml` to the stabilized command and data surface:
- `project/main.py`
- `project/cli.py`
- `project/cli_support.py`
- `project/cli_utils.py`
- `project/cli_parsers.py`
- `project/cli_readonly.py`
- `project/research_batch.py`
- `project/research_validation.py`
- `project/strategy_dossier.py`
- `project/data/repository.py`
- `project/data/repository_base.py`
- `project/data/repository_assets.py`
- `project/data/repository_evaluations.py`
- `project/data/repository_market.py`
- `project/data/repository_research.py`
- `project/data/repository_signals.py`
- `project/data/repository_trading.py`
- `project/data/schema.py`
- `project/data/row_parsers.py`
- `project/data/reporting_store.py`
- `project/data/db.py`
- `project/data/yfinance_loader.py`
- `project/data/market_collector_loader.py`
- `project/replay/engine.py`
- `project/decision/models.py`

## codex_cli

The separate `codex_cli/` package provides the local `mft` task orchestration tool used for bounded implementation work and architecture enforcement.

Install it from the repo root:

```bash
pip install -e ./codex_cli
```

Common commands:
- `mft run "implement new signal"`
- `mft plan "refactor validation flow"`
- `mft scratch <task_id>`
- `mft exec <task_id>`
- `mft execute <task_id>`
- `mft review <task_id>`
- `mft check architecture`
- `mft check drift`
- `mft diagnose <task_id>`
- `mft heal <task_id>`

Execution workflow:
- `mft exec <task_id>` builds the execution packet as JSON without launching an external agent CLI
- `mft execute <task_id>` launches the task in either Codex CLI or OpenCode
- `mft review <task_id>` builds the review packet after implementation work
- `mft complete <task_id>` marks the task complete manually after checks pass

Launch examples:

```bash
mft execute task_001 --dry-run
mft execute task_001 --provider codex --mode interactive
mft execute task_001 --provider codex --mode oneshot --json
mft execute task_001 --provider opencode --mode interactive
mft execute task_001 --provider opencode --mode oneshot --json
```

Launch rules:
- supported launch providers are `codex` and `opencode`
- `gemini` remains packet-only for planning and review flows
- `--mode interactive` opens the provider session in your terminal
- `--mode oneshot` runs the provider non-interactively and returns its exit code
- `--json` is only supported with `--mode oneshot`
- task completion remains manual; `mft execute` records launch attempts but does not auto-complete the task
