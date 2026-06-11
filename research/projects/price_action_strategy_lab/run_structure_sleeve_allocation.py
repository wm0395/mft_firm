from __future__ import annotations

import argparse
from pathlib import Path

from research.projects.price_action_strategy_lab.structure_sleeve_allocation import run_structure_sleeve_allocation_config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    args = parser.parse_args(argv)
    result = run_structure_sleeve_allocation_config(args.config)
    print(f"wrote structure sleeve allocation reports to {result.report_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
