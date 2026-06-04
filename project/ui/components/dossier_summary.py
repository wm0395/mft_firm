from __future__ import annotations

import html
from collections.abc import Sequence
from typing import Any, cast

from project.ui.components.status_card import render_status_cards
from project.ui.views.common import StatusCardView


def render_dossier_summary(st, dossier: dict[str, object]) -> None:
    render_status_cards(_cards(dossier))
    markdown_fn = getattr(st, "markdown", None)
    if callable(markdown_fn):
        markdown_fn(_summary_html(dossier), unsafe_allow_html=True)
    else:
        st.write(_note(dossier))
    _render_fact_rows(st, _fact_rows(dossier))
    if (line := _evidence_summary(dossier)):
        st.write(line)
    blockers = _strings(dossier.get("tradeability_blockers"))
    if blockers:
        _surface_warning(st, "Blockers: " + "; ".join(blockers))
    validation_errors = _strings(dossier.get("validation_errors"))
    if validation_errors:
        _surface_warning(st, "Validation errors: " + ", ".join(validation_errors))
    _surface_note(st, "Read the summary above, then inspect the raw dossier JSON below.")


def _cards(dossier: dict[str, object]) -> tuple[StatusCardView, ...]:
    tradeability = str(dossier.get("tradeability_status") or "unknown")
    return (
        StatusCardView(
            "Strategy",
            str(dossier.get("strategy_name") or dossier.get("hypothesis_id") or "n/a"),
            "ok",
            str(dossier.get("hypothesis_id") or "Strategy identity"),
        ),
        StatusCardView(
            "Tradeability",
            tradeability,
            (
                "ok"
                if tradeability == "eligible"
                else "warning"
                if tradeability == "blocked"
                else "action"
            ),
            str(dossier.get("activation_status") or "Activation status"),
        ),
        StatusCardView(
            "Snapshot",
            str(dossier.get("dataset_snapshot_id") or "missing"),
            "ok" if dossier.get("dataset_snapshot_id") else "warning",
            "Latest dataset snapshot",
        ),
        StatusCardView(
            "Next step",
            str(dossier.get("next_action") or "n/a"),
            "action" if dossier.get("next_action") else "warning",
            str(dossier.get("next_command") or "Launch command"),
        ),
    )


def _note(dossier: dict[str, object]) -> str:
    strategy = str(
        dossier.get("strategy_name") or dossier.get("hypothesis_id") or "Strategy dossier"
    )
    tradeability = str(dossier.get("tradeability_status") or "unknown")
    blockers = _strings(dossier.get("tradeability_blockers"))
    if blockers:
        blocker_text = f"{len(blockers)} blocker{'s' if len(blockers) != 1 else ''}"
        return f"{strategy} • {tradeability} • {blocker_text}"
    return f"{strategy} • {tradeability}"


def _fact_rows(dossier: dict[str, object]) -> tuple[tuple[str, str], ...]:
    return (
        (
            "Strategy",
            str(dossier.get("strategy_name") or dossier.get("hypothesis_id") or "n/a"),
        ),
        (
            "Tradeability",
            f"{dossier.get('tradeability_status') or 'unknown'}"
            f" • {dossier.get('activation_status') or 'activation pending'}",
        ),
        (
            "Snapshot",
            str(dossier.get("dataset_snapshot_id") or "missing"),
        ),
        (
            "Best backtest",
            _best_backtest(dossier) or "No backtest recorded yet.",
        ),
        (
            "Next step",
            _next_step(dossier) or "No next step configured.",
        ),
    )


def _render_fact_rows(st, rows: Sequence[tuple[str, str]]) -> None:
    columns_fn = getattr(st, "columns", None)
    if not callable(columns_fn):
        for label, value in rows:
            st.write(f"**{label}**: {value}")
        return
    left, right = columns_fn(2)
    for column, group in zip((left, right), _pair_rows(rows)):
        with column:
            for label, value in group:
                st.write(f"**{label}**: {value}")


def _pair_rows(rows: Sequence[tuple[str, str]]) -> tuple[tuple[tuple[str, str], ...], ...]:
    midpoint = (len(rows) + 1) // 2
    return tuple(rows[:midpoint]), tuple(rows[midpoint:])


def _next_step(dossier: dict[str, object]) -> str:
    next_action = str(dossier.get("next_action") or "").strip()
    next_command = str(dossier.get("next_command") or "").strip()
    if not next_action and not next_command:
        return ""
    return f"Next step: {next_action or 'n/a'} | Command: {next_command or 'n/a'}"


def _evidence_summary(dossier: dict[str, object]) -> str:
    summary = dossier.get("evidence_summary")
    if not isinstance(summary, dict):
        return ""
    text = str(summary.get("summary") or "").strip()
    return f"Evidence summary: {text}" if text else ""


def _best_backtest(dossier: dict[str, object]) -> str:
    backtest = dossier.get("best_backtest")
    if not isinstance(backtest, dict):
        return ""
    hypothesis_id = str(backtest.get("hypothesis_id") or "n/a")
    return (
        f"{hypothesis_id} • "
        f"{_float_value(backtest.get('total_return_pct')):.2f}% / "
        f"Sharpe {_float_value(backtest.get('sharpe_ratio')):.2f} • "
        f"{_int_value(backtest.get('total_trades'))} trades"
    )


def _summary_html(dossier: dict[str, object]) -> str:
    strategy = str(
        dossier.get("strategy_name") or dossier.get("hypothesis_id") or "Strategy dossier"
    )
    tradeability = str(dossier.get("tradeability_status") or "unknown")
    snapshot = str(dossier.get("dataset_snapshot_id") or "missing")
    next_step = _next_action(dossier)
    validation = _validation_summary(dossier)
    rows = [
        "<section style='margin:0.9rem 0 1rem;padding:1rem 1.1rem;"
        "border:1px solid #e2e8f0;border-radius:14px;"
        "background:linear-gradient(180deg,#ffffff 0%,#f8fafc 100%);"
        "box-shadow:0 6px 18px rgba(15,23,42,0.05);'>",
        "<div style='color:#64748b;font-size:0.68rem;font-weight:700;"
        "letter-spacing:0.14em;text-transform:uppercase;margin-bottom:0.25rem;'>"
        "Dossier at a glance</div>",
        f"<div style='color:#0f172a;font-size:1rem;font-weight:700;line-height:1.3;'>"
        f"{html.escape(strategy)}</div>",
        f"<div style='color:#475569;font-size:0.85rem;line-height:1.55;margin-top:0.35rem;'>"
        f"{html.escape(_note(dossier))}</div>",
        "<div style='display:flex;flex-wrap:wrap;gap:0.5rem;margin-top:0.85rem;'>",
        _summary_chip_html("Tradeability", tradeability, _tradeability_tone(tradeability)),
        _summary_chip_html("Snapshot", snapshot, _status_tone(snapshot)),
        _summary_chip_html("Next step", next_step, _status_tone(next_step)),
        _summary_chip_html("Validation", validation, _validation_tone(dossier)),
        "</div></section>",
    ]
    return "".join(rows)


def _summary_chip_html(label: str, value: str, tone: str) -> str:
    return "".join(
        [
            "<div style='display:flex;flex-direction:column;gap:0.1rem;"
            "padding:0.55rem 0.7rem;border-radius:12px;background:#ffffff;"
            "border:1px solid #e2e8f0;min-width:120px;'>",
            f"<div style='color:#64748b;font-size:0.62rem;font-weight:700;"
            f"letter-spacing:0.12em;text-transform:uppercase;'>{html.escape(label)}</div>",
            f"<div style='color:{_tone_color(tone)};font-size:0.84rem;font-weight:700;"
            f"line-height:1.35;word-break:break-word;'>{html.escape(value)}</div>",
            "</div>",
        ]
    )


def _next_action(dossier: dict[str, object]) -> str:
    next_action = str(dossier.get("next_action") or "").strip()
    return next_action or "No next step configured."


def _validation_summary(dossier: dict[str, object]) -> str:
    validation_errors = _strings(dossier.get("validation_errors"))
    if not validation_errors:
        return "Clear"
    count = len(validation_errors)
    return f"{count} error{'s' if count != 1 else ''}"


def _tradeability_tone(tradeability: str) -> str:
    if tradeability == "eligible":
        return "ok"
    if tradeability == "blocked":
        return "warning"
    return "action"


def _validation_tone(dossier: dict[str, object]) -> str:
    return "ok" if not _strings(dossier.get("validation_errors")) else "warning"


def _status_tone(value: str) -> str:
    if value in {"missing", "No next step configured."}:
        return "warning"
    return "ok"


def _tone_color(tone: str) -> str:
    if tone == "ok":
        return "#15803d"
    if tone == "warning":
        return "#b45309"
    return "#4f46e5"


def _strings(value: object) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value)
    if value:
        return (str(value),)
    return ()


def _float_value(value: object) -> float:
    try:
        return float(cast(Any, value))
    except (TypeError, ValueError):
        return 0.0


def _int_value(value: object) -> int:
    try:
        return int(cast(Any, value))
    except (TypeError, ValueError):
        return 0


def _surface_warning(st, text: str) -> None:
    warning_fn = getattr(st, "warning", None)
    if callable(warning_fn):
        warning_fn(text)
        return
    st.write(text)


def _surface_note(st, text: str) -> None:
    markdown_fn = getattr(st, "markdown", None)
    if callable(markdown_fn):
        markdown_fn(_note_html(text), unsafe_allow_html=True)
        return
    write_fn = getattr(st, "write", None)
    if callable(write_fn):
        write_fn(text)
        return
    caption_fn = getattr(st, "caption", None)
    if callable(caption_fn):
        caption_fn(text)


def _note_html(text: str) -> str:
    return "".join(
        [
            "<section style='margin:0.75rem 0 0;padding:0.85rem 1rem;"
            "border:1px solid #e2e8f0;border-radius:12px;"
            "background:linear-gradient(180deg,#ffffff 0%,#f8fafc 100%);'>",
            "<div style='color:#64748b;font-size:0.64rem;font-weight:700;"
            "letter-spacing:0.14em;text-transform:uppercase;margin-bottom:0.2rem;'>"
            "Review note</div>",
            f"<div style='color:#475569;font-size:0.82rem;line-height:1.5;'>"
            f"{html.escape(text)}</div>",
            "</section>",
        ]
    )
