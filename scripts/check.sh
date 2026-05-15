#!/usr/bin/env bash
set -euo pipefail

python -m pytest
python -m ruff check .
python -m mypy
mft check architecture
mft check drift
