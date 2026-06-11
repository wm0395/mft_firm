from __future__ import annotations

import argparse
from pathlib import Path

from research.projects.price_action_strategy_lab.portfolio_integration import run_portfolio_integration_config
from research.projects.price_action_strategy_lab.portfolio_integration import write_portfolio_integration


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    args = parser.parse_args(argv)
    result = run_portfolio_integration_config(args.config)
    write_portfolio_integration(result)
    print(f"wrote portfolio integration reports to {result.report_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
