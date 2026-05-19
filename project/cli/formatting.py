from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import is_dataclass
from pprint import pformat
from typing import Any

from rich import box
from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table

from project.cli.context import CLIContext
from project.cli.errors import CliError


def emit(
    context: CLIContext,
    command: str,
    result: object | None,
    *,
    status: str = "ok",
    warnings: tuple[str, ...] = (),
    error: CliError | str | None = None,
) -> None:
    if context.output_mode == "json":
        _emit_json(command, result, status, warnings, error)
        return
    if error is not None:
        _render_error(context.console, command, error)
        return
    if context.output_mode == "plain":
        _render_plain(context.console, command, result, status)
        return
    _render_human(context.console, command, result, status, warnings)


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


def _emit_json(
    command: str,
    result: object | None,
    status: str,
    warnings: tuple[str, ...],
    error: CliError | str | None,
) -> None:
    payload = {
        "command": command,
        "status": "error" if error is not None else status,
        "result": None if error is not None else _jsonable(result),
        "warnings": list(warnings),
        "error": None if error is None else str(error),
    }
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))


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


def _render_plain(
    console: Any,
    command: str,
    result: object | None,
    status: str,
) -> None:
    console.print(f"{_title(command)}: {status.upper()}")
    if result is None:
        return
    if isinstance(result, Mapping):
        for key, value in result.items():
            console.print(f"{key}: {_scalar(value)}")
        return
    if isinstance(result, Sequence) and not isinstance(result, (str, bytes)):
        for item in result:
            console.print(f"- {_scalar(item)}")
        return
    console.print(_scalar(result))


def _render_error(console: Any, command: str, error: CliError | str) -> None:
    console.print(Panel.fit("", title=f"{_title(command)}: Failed", box=box.SIMPLE))
    if isinstance(error, CliError):
        console.print("Problem:")
        console.print(error.message)
        if error.why:
            console.print()
            console.print("Why it matters:")
            console.print(error.why)
        if error.next_action:
            console.print()
            console.print("Next:")
            console.print(error.next_action)
        if error.command:
            console.print()
            console.print("Run:")
            console.print(error.command)
        return
    console.print("Problem:")
    console.print(str(error))


def _render_generic(
    console: Any,
    command: str,
    result: object | None,
    status: str,
    warnings: tuple[str, ...],
) -> None:
    title = f"{_title(command)}: {status.upper()}"
    body = Pretty(_jsonable(result), expand_all=False)
    console.print(Panel(body, title=title, box=box.SIMPLE))
    if warnings:
        console.print()
        console.print("Warnings:")
        for warning in warnings:
            console.print(f"- {warning}")


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


def _mapping(result: object | None) -> Mapping[str, Any]:
    if result is None:
        return {}
    if isinstance(result, Mapping):
        return result
    if is_dataclass(result):
        return json.loads(json.dumps(result, default=str))
    return {"value": result}


def _jsonable(result: object | None) -> object | None:
    if result is None:
        return None
    if isinstance(result, Mapping):
        return {key: _jsonable(value) for key, value in result.items()}
    if isinstance(result, Sequence) and not isinstance(result, (str, bytes)):
        return [_jsonable(item) for item in result]
    if is_dataclass(result):
        return _jsonable(result.__dict__)
    return result


def _status_text(status: object, message: object) -> str:
    if str(status) == "ok":
        return "OK"
    if message:
        return f"Warning: {message}"
    return "Warning"


def _scalar(value: object) -> str:
    if isinstance(value, Mapping):
        return pformat(dict(value))
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return ", ".join(_scalar(item) for item in value)
    return str(value)


def _title(command: str) -> str:
    return command.replace("-", " ").title()
