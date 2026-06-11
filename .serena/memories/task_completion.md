# Task completion gate
- Prefer `./scripts/check.sh` as the single local completion command.
- If run piecemeal, the minimum gate is `python -m pytest`, `python -m ruff check .`, `python -m mypy`, `mft check architecture`, `mft check drift`.
- If code under `research/` or generated artifacts changed, rerun the affected generator(s) before finishing.
- Do not mark work done until tests, lint, typing, and architecture checks pass.