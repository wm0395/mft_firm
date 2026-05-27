from __future__ import annotations

from typing import Any

from rich import box
from rich.panel import Panel


def render_intro(console: Any) -> None:
    console.print(
        Panel.fit(
            "\n".join(
                [
                    "[bold]MFT Investment System[/bold]",
                    "",
                    "Modern entrypoints:",
                    "  mft status",
                    "  mft next",
                    "  mft guide",
                    "",
                    "Workflow map:",
                    "  Setup: mft setup init",
                    "  Data: mft data quality AAPL MSFT, mft data sync AAPL MSFT",
                    (
                        "  Snapshot: mft data snapshot create AAPL MSFT "
                        "--market US --from 2026-05-01 --to 2026-05-19"
                    ),
                    (
                        "  Research: mft research run "
                        "hypothesis:rsi_mean_reversion AAPL --snapshot latest"
                    ),
                    "  Hypotheses: mft hypothesis list | check | validate | promote",
                    "  Ideas: mft ideas review",
                    "  Explain: mft explain trade hypothesis:rsi_mean_reversion",
                    "",
                    "Use `mft --help` for the grouped command map.",
                ]
            ),
            title="Welcome",
            box=box.SIMPLE,
        )
    )


def render_guide(console: Any) -> None:
    console.print(
        Panel.fit(
            "\n".join(
                [
                    "Recommended sequence:",
                    "",
                    "1. Initialize the schema: mft setup init",
                    "2. Check system status: mft status",
                    "3. Load market data: mft data sync AAPL MSFT",
                    (
                        "4. Create a snapshot: mft data snapshot create "
                        "AAPL MSFT --market US --from 2026-05-01 --to 2026-05-19"
                    ),
                    (
                        "5. Run research: mft research run "
                        "hypothesis:rsi_mean_reversion AAPL --snapshot latest"
                    ),
                    "6. Review hypotheses: mft hypothesis list",
                    "7. Review trade ideas: mft ideas review",
                ]
            ),
            title="Guided Workflow",
            box=box.SIMPLE,
        )
    )


def render_examples(console: Any) -> None:
    console.print(
        Panel.fit(
            "\n".join(
                [
                    "Quick examples:",
                    "",
                    "1. First-time setup",
                    "   mft setup init",
                    "",
                    "2. Check what to do next",
                    "   mft next",
                    "",
                    "3. Run research",
                    (
                        "   mft research run "
                        "hypothesis:rsi_mean_reversion RELIANCE --snapshot latest"
                    ),
                    "",
                    "4. Review trade ideas",
                    "   mft ideas review",
                ]
            ),
            title="Examples",
            box=box.SIMPLE,
        )
    )
