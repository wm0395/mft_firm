from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from rich import box
from rich.panel import Panel
from rich.table import Table

from project.cli.formatting_core import _mapping, _render_generic, _status_text
from project.cli.formatting_text import render_examples, render_guide


def _render_human(
    console: Any,
    command: str,
    result: object | None,
    status: str,
    warnings: tuple[str, ...],
) -> None:
    handlers = {
        "status": _render_status,
        "next": _render_next,
        "setup-init": _render_setup_init,
        "bootstrap": _render_bootstrap,
        "data-quality": _render_data_quality,
        "data-sync": _render_data_sync,
        "data-snapshot-create": _render_data_snapshot_create,
        "hypothesis-list": _render_hypothesis_list,
        "hypothesis-check": _render_hypothesis_check,
        "hypothesis-validate": _render_hypothesis_validate,
        "research-run": _render_research_run,
        "ideas-review": _render_ideas_review,
        "guide": lambda console, _result, _status, _warnings: render_guide(console),
        "examples": lambda console, _result, _status, _warnings: render_examples(console),
        "ideas-list": _render_ideas_review,
    }
    handler = handlers.get(command)
    if handler is None:
        _render_generic(console, command, result, status, warnings)
        return
    handler(console, result, status, warnings)


def _render_status(console: Any, result: object | None, status: str, warnings: tuple[str, ...]) -> None:
    payload = _mapping(result)
    table = Table(title="MFT System Status", box=box.SIMPLE_HEAVY, show_lines=False)
    table.add_column("Area", style="bold")
    table.add_column("Value")
    table.add_row("Database", _status_text(payload["database_status"], payload["database_message"]))
    table.add_row("Market Data", _status_text(payload["market_status"], payload["market_message"]))
    table.add_row("Assets", f'{payload["assets"]} loaded')
    table.add_row("Snapshots", f'{payload["snapshots"]} available')
    table.add_row("Research Runs", f'{payload["research_runs"]} completed')
    table.add_row(
        "Hypotheses",
        f'{payload["draft_hypotheses"]} draft, {payload["testing_hypotheses"]} testing, {payload["active_hypotheses"]} active',
    )
    console.print(table)
    _render_next_block(console, payload["next_action"], payload["next_command"])
    if payload.get("show_checks") and payload.get("checks"):
        console.print()
        checks = Table(title="Checks", box=box.SIMPLE)
        checks.add_column("Check", style="bold")
        checks.add_column("Status")
        checks.add_column("Note")
        for check in payload["checks"]:
            checks.add_row(
                str(check.get("check", "")),
                str(check.get("status", "")),
                str(check.get("note", "")),
            )
        console.print(checks)
    if warnings:
        console.print()
        console.print("Warnings:")
        for warning in warnings:
            console.print(f"- {warning}")


def _render_next(console: Any, result: object | None, status: str, warnings: tuple[str, ...]) -> None:
    payload = _mapping(result)
    console.print(Panel.fit("", title="Next Action", box=box.SIMPLE))
    _render_next_block(
        console,
        payload.get("next_action", "No action available"),
        payload.get("next_command", ""),
        payload.get("state"),
        payload.get("why"),
    )
    if warnings:
        console.print()
        console.print("Warnings:")
        for warning in warnings:
            console.print(f"- {warning}")


def _render_next_block(
    console: Any,
    next_action: object,
    next_command: object,
    state: object | None = None,
    why: object | None = None,
) -> None:
    if state:
        console.print("You are at:")
        console.print(str(state))
        console.print()
    if why:
        console.print("Why it matters:")
        console.print(str(why))
        console.print()
    console.print("Next:")
    console.print(str(next_action))
    console.print()
    console.print("Run:")
    console.print(str(next_command))


def _render_setup_init(console: Any, result: object | None, status: str, warnings: tuple[str, ...]) -> None:
    console.print(Panel.fit("Database initialized.", title="Setup", box=box.SIMPLE))


def _render_bootstrap(console: Any, result: object | None, status: str, warnings: tuple[str, ...]) -> None:
    payload = _mapping(result)
    console.print(Panel.fit("", title="Bootstrap", box=box.SIMPLE))
    console.print(f"Setup: {payload.get('setup_status', 'ok').upper()}")
    console.print(f"Status: {payload.get('system_status', 'unknown').upper()}")
    console.print(f"Next: {payload.get('next_action', '')}")
    console.print(f"Run: {payload.get('next_command', '')}")


def _render_data_quality(console: Any, result: object | None, status: str, warnings: tuple[str, ...]) -> None:
    payload = _mapping(result)
    console.print(Panel.fit("", title=f"Data Quality: {status.upper()}", box=box.SIMPLE))
    console.print("Problem:")
    console.print(str(payload.get("problem", "")))
    if payload.get("why"):
        console.print()
        console.print("Why it matters:")
        console.print(str(payload["why"]))
    console.print()
    console.print("Next:")
    console.print(str(payload.get("next_action", "")))
    console.print()
    console.print("Run:")
    console.print(str(payload.get("next_command", "")))
    console.print()
    table = Table(title="Symbols", box=box.SIMPLE)
    table.add_column("Symbol", style="bold")
    table.add_column("Rows")
    table.add_column("Latest")
    table.add_column("Status")
    table.add_column("Issues")
    for symbol in payload.get("symbols", []):
        issues = list(symbol.get("errors", ())) + list(symbol.get("warnings", ()))
        table.add_row(
            str(symbol.get("symbol", "")),
            str(symbol.get("row_count", 0)),
            str(symbol.get("latest_timestamp", "")),
            str(symbol.get("status", "")),
            "; ".join(issues),
        )
    console.print(table)


def _render_data_sync(console: Any, result: object | None, status: str, warnings: tuple[str, ...]) -> None:
    payload = _mapping(result)
    console.print(Panel.fit("", title="Data Sync", box=box.SIMPLE))
    console.print(f"Loaded symbols: {', '.join(payload.get('symbols', ())) or 'none'}")
    console.print(f"Rows loaded: {payload.get('rows_loaded', {})}")


def _render_data_snapshot_create(
    console: Any,
    result: object | None,
    status: str,
    warnings: tuple[str, ...],
) -> None:
    payload = _mapping(result)
    console.print(Panel.fit("", title="Dataset Snapshot", box=box.SIMPLE))
    console.print(f"Snapshot: {payload.get('dataset_snapshot_id', '')}")
    console.print(f"Universe: {payload.get('universe_id', '')}")
    console.print(f"Quality: {payload.get('quality_status', '')}")


def _render_hypothesis_list(console: Any, result: object | None, status: str, warnings: tuple[str, ...]) -> None:
    payload = _mapping(result)
    table = Table(title="Hypotheses", box=box.SIMPLE)
    table.add_column("ID", style="bold")
    table.add_column("Name")
    table.add_column("Status")
    table.add_column("Version")
    table.add_column("Signals")
    for item in payload.get("hypotheses", []):
        table.add_row(
            str(item.get("hypothesis_id", "")),
            str(item.get("name", "")),
            str(item.get("status", "")),
            str(item.get("version", "")),
            ", ".join(item.get("required_signals", ())),
        )
    console.print(table)


def _render_hypothesis_check(
    console: Any,
    result: object | None,
    status: str,
    warnings: tuple[str, ...],
) -> None:
    payload = _mapping(result)
    console.print(Panel.fit("", title=f"Hypothesis: {payload.get('name', payload.get('hypothesis_id', ''))}", box=box.SIMPLE))
    console.print(f"Status: {payload.get('status', '')}")
    console.print(f"Readiness: {payload.get('readiness', '')}")
    if payload.get("missing_evidence"):
        console.print()
        console.print("Missing evidence:")
        for item in payload["missing_evidence"]:
            console.print(f"- {item}")
    if payload.get("next_action"):
        console.print()
        console.print("Next:")
        console.print(str(payload["next_action"]))
    if payload.get("next_command"):
        console.print()
        console.print("Run:")
        console.print(str(payload["next_command"]))


def _render_hypothesis_validate(
    console: Any,
    result: object | None,
    status: str,
    warnings: tuple[str, ...],
) -> None:
    payload = _mapping(result)
    console.print(Panel.fit("", title="Hypothesis Validation", box=box.SIMPLE))
    console.print(f"Hypothesis: {payload.get('hypothesis_id', '')}")
    console.print(f"Valid: {payload.get('valid', False)}")
    if payload.get("reasons"):
        console.print("Reasons:")
        for reason in payload["reasons"]:
            console.print(f"- {reason}")


def _render_research_run(console: Any, result: object | None, status: str, warnings: tuple[str, ...]) -> None:
    payload = _mapping(result)
    console.print(Panel.fit("", title="Research Run", box=box.SIMPLE))
    console.print(f"Run: {payload.get('research_run_id', '')}")
    console.print(f"Hypothesis: {payload.get('hypothesis_id', '')}")
    console.print(f"Asset: {payload.get('asset_symbol', payload.get('asset_id', ''))}")
    console.print(f"Snapshot: {payload.get('dataset_snapshot_id', '')}")
    console.print(f"Status: {payload.get('status', '')}")
    metrics = payload.get("metrics", {})
    if isinstance(metrics, Mapping) and metrics:
        console.print()
        metric_table = Table(title="Metrics", box=box.SIMPLE)
        metric_table.add_column("Name", style="bold")
        metric_table.add_column("Value")
        for key, value in metrics.items():
            metric_table.add_row(str(key), str(value))
        console.print(metric_table)


def _render_ideas_review(console: Any, result: object | None, status: str, warnings: tuple[str, ...]) -> None:
    payload = _mapping(result)
    ideas = payload.get("ideas", [])
    console.print(Panel.fit("", title="Open Trade Ideas", box=box.SIMPLE))
    if not ideas:
        console.print("No open trade ideas.")
        return
    table = Table(box=box.SIMPLE)
    table.add_column("#", style="bold")
    table.add_column("Trade")
    table.add_column("Symbol")
    table.add_column("Hypothesis")
    table.add_column("Confidence")
    table.add_column("Status")
    for index, idea in enumerate(ideas, start=1):
        table.add_row(
            str(index),
            str(idea.get("trade_id", "")),
            str(idea.get("symbol", "")),
            str(idea.get("hypothesis_id", "")),
            f"{float(idea.get('confidence', 0.0)):.2f}",
            str(idea.get("status", "needs review")),
        )
    console.print(table)
