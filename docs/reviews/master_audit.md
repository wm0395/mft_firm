# Master Audit

## Current State

- Branch: `main`
- Git status: dirty worktree
- Tracked modifications:
  - `project/backtesting/engine.py`
  - `project/common/__init__.py`
  - `project/common/explainability.py`
  - `project/hypotheses/engine.py`
  - `project/hypotheses/ma_crossover.py`
  - `project/learning/engine.py`
  - `project/replay/engine.py`
  - `project/research_validation.py`
  - `project/signals/registry.py`
  - `project/validation/engine.py`
  - `project/validation/models.py`
  - `project/validation/validators.py`
  - `pyproject.toml`
  - `tests/test_project_pipeline.py`
  - `tests/test_validation_new.py`
- Untracked items:
  - `.tmp_task001_clone/`
  - `docs/research/`

## Install Status

- `python -m pip install -e ./codex_cli`: passed
- `mft` editable install is usable from the repo root

## Test Status

- `python -m pytest`: passed, `103 passed`

## Ruff Status

- `python -m ruff check .`: passed

## Mypy Status

- `python -m mypy`: passed, no issues found in the scoped typed surface

## Architecture Status

- `mft check architecture`: passed
- Layer lint: passed
- Architecture tests: passed

## Drift Status

- `mft check drift`: passed
- Drift score: `100`
- Violations: none reported

## CLI Health

- `mft --help`: passed
- `mft check architecture`: passed
- `mft check drift`: passed
- `python project/main.py --help`: failed with `ModuleNotFoundError: No module named 'project'`

## Database and Schema Health

- `project/data/schema.py` defines `REQUIRED_TABLES` and the schema SQL for the main platform tables
- `DuckDBAccess.initialize_schema()` applies the schema statements deterministically
- I did not reach a successful direct script smoke test for `init-db` because the documented `project/main.py` entrypoint is broken

## codex_cli Health

- Editable installation works
- `mft --help` is available
- Architecture and drift checks are healthy
- The package appears operational for its enforced checks and task tooling

## Top P0 / P1 Issues

1. `project/main.py` is not a runnable script entrypoint.
   - Direct execution fails immediately with `ModuleNotFoundError: No module named 'project'`
   - The file is currently only an import shim and does not invoke `main()` when executed
   - This blocks the documented `python project/main.py ...` workflow

2. README command truthfulness is currently overstated.
   - The README advertises direct `project/main.py` commands that are not usable in the current state
   - That creates a false setup path for new developers

## Recommended Execution Order

1. Fix `project/main.py` so the documented script entrypoint actually works and remains thin.
2. Reconcile README command examples with the real runtime behavior.
3. Clean root-level clutter and move stale planning/review artifacts into the documented `docs/` structure.
4. Smoke test `init-db` and the deterministic fixture workflow on a fresh database.
5. Then continue through signals, hypotheses, replay, backtesting, and decision/reporting hardening.

