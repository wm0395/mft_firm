from __future__ import annotations

from dataclasses import replace

from project.common.models import HypothesisDefinition, HypothesisStatus


VALID_TRANSITIONS = {
    ("draft", "testing"),
    ("testing", "active"),
    ("active", "deprecated"),
    ("deprecated", "archived"),
}


def validate_transition(
    current_status: HypothesisStatus,
    target_status: HypothesisStatus,
    force: bool = False,
) -> None:
    if current_status == target_status:
        return
    if force:
        return
    if (current_status, target_status) not in VALID_TRANSITIONS:
        raise ValueError(
            f"invalid hypothesis transition: {current_status} -> {target_status}"
        )


def promote_definition(
    definition: HypothesisDefinition,
    target_status: HypothesisStatus,
    force: bool = False,
) -> HypothesisDefinition:
    validate_transition(definition.status, target_status, force=force)
    return replace(definition, status=target_status)
