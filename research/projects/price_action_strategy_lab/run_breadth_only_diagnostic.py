from __future__ import annotations

import argparse
from pathlib import Path

from research.projects.price_action_strategy_lab.breadth_only_diagnostic import run_breadth_only_config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    args = parser.parse_args(argv)
    result = run_breadth_only_config(args.config)
    print(f"wrote breadth-only diagnostic reports to {result.report_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
