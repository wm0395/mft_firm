# Phase 1 Review

## Files Changed

- `project/main.py`
- `tests/test_cli_runtime.py`
- `codex_cli/codex_cli/prompts.py`
- `codex_cli/tests/test_review_gate.py`
- `codex_cli/tests/test_packaging_entrypoint.py`
- `IMPLEMENT.md`
- `docs/reviews/master_audit.md`
- `docs/prompts/architecture_reviewer.md`
- `docs/prompts/complexity_reviewer.md`
- `docs/prompts/determinism_auditor.md`
- `docs/prompts/financial_logic_auditor.md`
- `docs/prompts/test_failure_reviewer.md`
- Removed from root:
  - `agents/prompts/architecture_reviewer.md`
  - `agents/prompts/complexity_reviewer.md`
  - `agents/prompts/determinism_auditor.md`
  - `agents/prompts/financial_logic_auditor.md`
  - `agents/prompts/test_failure_reviewer.md`
  - `install_openclaw_nvidia.sh`
  - `package-lock.json`
  - `project/main.py.bak`

## Commands Run

- `python project/main.py --help`
- `python project/main.py init-db --database /tmp/mft_test.duckdb`
- `python -m pytest`
- `python -m ruff check .`
- `python -m mypy`
- `mft check architecture`
- `mft check drift`
- `python -m pip install -e ./codex_cli`

## Results

- `python project/main.py --help`: passed
- `python project/main.py init-db --database /tmp/mft_test.duckdb`: passed
- `python -m pytest`: passed, `105 passed`
- `python -m ruff check .`: passed
- `python -m mypy`: passed
- `mft check architecture`: passed
- `mft check drift`: passed
- `python -m pip install -e ./codex_cli`: passed

## Remaining Issues

- `docs/research/baseline_001.md` is still a blank template and should either be filled with a real baseline entry or archived in a later phase.
- The broader research workflow docs in `docs/` still need phase-specific expansion, but no false root-level commands remain.

## Review Findings

- P0: none
- P1: none
- P2: `docs/research/baseline_001.md` remains a placeholder and is not yet a finished research artifact.
- P3: the old prompt-file location was cleaned up and the canonical path is now `docs/prompts/`.

## Fixes Applied

- Made `project/main.py` a script-safe thin entrypoint.
- Added regression tests for direct script and module help invocation.
- Moved reviewer prompt files from `agents/prompts/` to `docs/prompts/`.
- Updated codex_cli prompt loading to prefer `docs/prompts/` with a fallback for older workspaces.
- Updated the codex_cli packaging smoke test to seed the canonical prompt location.
- Removed noncanonical root artifacts that were not part of the runtime surface.

## Phase Decision

- Accepted: yes

