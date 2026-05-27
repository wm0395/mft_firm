# MFT Firm

Deterministic market research platform for signal generation, hypothesis evaluation, validation, trade idea generation, replay analysis, and backtesting.

## Setup

Create or activate a Python 3.12 virtual environment, then install the project dependencies:

```bash
pip install -r project/requirements.txt
pip install -r project/requirements-dev.txt
pip install -e ./codex_cli
```

Runtime dependencies live in `project/requirements.txt`. Developer tooling lives in `project/requirements-dev.txt`.

## Operator Cockpit

The primary operator surface is the Streamlit cockpit:

```bash
streamlit run project/ui/app.py
```

The cockpit is organized around Mission Control, Data, Research, Hypotheses,
Trade Ideas, Explainability, and Reports. It is the default way to inspect
system health, review evidence, and decide what to do next.

When `streamlit-option-menu` is installed, the sidebar uses a modern option
menu; otherwise it falls back to the built-in Streamlit radio selector.

## Operator Workflow

Start with the health and status commands:

```bash
mft status
mft next
mft guide
```

Recommended flow:

1. `mft status`
2. `mft setup init`
3. `mft data sync AAPL MSFT`
4. `mft data quality AAPL MSFT`
5. `mft data snapshot create AAPL MSFT --market US --from 2026-05-01 --to 2026-05-20`
6. `mft research run hypothesis:rsi_mean_reversion AAPL --snapshot latest`
7. `mft hypothesis check hypothesis:rsi_mean_reversion`
8. `mft hypothesis promote hypothesis:rsi_mean_reversion --to testing`

Use the cockpit for day-to-day work and the CLI when you need a direct command
for automation, scripting, or troubleshooting.

The modern grouped CLI is `mft`; prefer it for the supported commands in this
guide. Some compatibility examples below still use `python project/main.py`.

## Core Workflows

### Market Data

Use the Postgres-backed sync path when `MARKET_DB_URL` is available:

```bash
mft data sync AAPL MSFT --resolution 1d
```

Use the collector import path when you already have a DuckDB export from a separate `market_collector` checkout:

```bash
python project/main.py load-market-collector \
  --source-database /path/to/market.duckdb \
  --symbol AAPL
```

CSV ingestion remains available for local fixtures:

```bash
python project/main.py load-ohlcv-csv --file-path /path/to/file.csv --asset-symbol AAPL
```

### Data Quality and Snapshots

Inspect quality before building a snapshot:

```bash
mft data quality AAPL MSFT
mft data quality AAPL --strict
```

Build a reproducible dataset snapshot:

```bash
mft data snapshot create AAPL MSFT \
  --market US \
  --from 2026-05-01 \
  --to 2026-05-20 \
  --resolution 1d
```

### Research and Governance

Run the deterministic research workflow:

```bash
mft research run hypothesis:rsi_mean_reversion AAPL --snapshot latest
```

Check hypothesis promotion readiness:

```bash
mft hypothesis check hypothesis:rsi_mean_reversion
```

Review and promote hypotheses:

```bash
mft hypothesis list
mft hypothesis check hypothesis:rsi_mean_reversion
mft hypothesis validate hypothesis:rsi_mean_reversion
mft hypothesis promote hypothesis:rsi_mean_reversion --to testing
```

Some research lifecycle commands still use the compatibility entrypoint and
the same JSON envelope contract:

```bash
python project/main.py create-research-project --name research:rsi --description "RSI checks"
python project/main.py list-research-projects
python project/main.py show-research-project research_project:rsi
python project/main.py run-parameter-research \
  --research-run-config research/examples/nifty50_two_strategy_research/configs/research_run.yaml
python project/main.py list-research-runs --research-project-id research_project:rsi
python project/main.py compare-research-runs research_run:1 research_run:2
python project/main.py export-research-pack research_project:rsi --output-dir research/exports/rsi
python project/main.py promote-strategy-candidate strategy_candidate:rsi --to testing
```

See [research/README.md](research/README.md) for the notebook-safe workflow,
workspace layout, and artifact review rules.

### Inspection

The compatibility entrypoint also exposes these read-only inspection commands:

```bash
python project/main.py show-trade-idea <trade_id>
python project/main.py show-validation-path <evaluation_id>
python project/main.py show-explanation <evaluation_id>
python project/main.py show-validation-failures
python project/main.py report-hypotheses --horizon 20
python project/main.py backtest-results
python project/main.py hypothesis-performance
python project/main.py advanced-report hypothesis:rsi_mean_reversion
```

## CLI Output

All CLI commands emit a JSON envelope:

```json
{
  "command": "data-quality-report",
  "status": "ok",
  "result": {},
  "warnings": [],
  "error": null
}
```

Read-only inspection commands use the same shape as mutating commands. `data-quality-report` is non-fatal by default and only exits non-zero with `--strict`.

## Data Model

The database schema includes:

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
- `research_universes`
- `dataset_snapshots`
- `strategy_specs`
- `research_runs`
- `strategy_evidence_summaries`

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

The stabilized mypy surface is defined in `pyproject.toml` and now covers the CLI, operator workflow commands, research workflow, hypothesis registry, and the current MFT data surface.

## Operator Guide

See [docs/OPERATOR_GUIDE.md](docs/OPERATOR_GUIDE.md) for a workflow-oriented command guide.

## codex_cli

The separate `codex_cli/` package provides local task orchestration and architecture checks. Treat it as developer tooling, not runtime MFT code.

Install it from the repo root:

```bash
pip install -e ./codex_cli
```

The installed command is `ai_code`.
