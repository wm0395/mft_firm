from __future__ import annotations

import argparse
from pathlib import Path

from research.projects.price_action_strategy_lab.advance_decline_stress_overlay import run_advance_decline_stress_config
from research.projects.price_action_strategy_lab.advance_decline_stress_overlay import write_advance_decline_stress_reports


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    args = parser.parse_args(argv)
    result = run_advance_decline_stress_config(args.config)
    write_advance_decline_stress_reports(result, args.config)
    print(f"wrote advance-decline stress overlay reports to {result.report_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
