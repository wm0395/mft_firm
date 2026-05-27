from __future__ import annotations

from project.ui.components.status_card import render_status_cards
from project.ui.views.common import StatusCardView


def render_dossier_summary(st, dossier: dict[str, object]) -> None:
    render_status_cards(_cards(dossier))
    st.info(_note(dossier))
    if (line := _next_step(dossier)):
        st.info(line)
    if (line := _evidence_summary(dossier)):
        st.info(line)
    blockers = _strings(dossier.get("tradeability_blockers"))
    if blockers:
        st.info("Blockers: " + "; ".join(blockers))
    validation_errors = _strings(dossier.get("validation_errors"))
    if validation_errors:
        st.info("Validation errors: " + ", ".join(validation_errors))
    st.info("Read the summary above, then inspect the raw dossier JSON below.")


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
            "ok" if tradeability == "eligible" else "warning" if tradeability == "blocked" else "action",
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
        return f"{strategy} • {tradeability} • {len(blockers)} blockers"
    return f"{strategy} • {tradeability}"


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


def _strings(value: object) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value)
    if value:
        return (str(value),)
    return ()
