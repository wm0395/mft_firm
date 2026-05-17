from __future__ import annotations

from project.cli_utils import (
    decision_action,
    decision_reason,
    emit,
    find_asset,
    find_evaluation,
    hypotheses,
    load_json,
    parse_datetime,
    research_assets,
)
from project.research_batch import run_research_batch
from project.research_validation import (
    evaluation_from_output,
    validate_outputs,
    validation_payload,
)
from project.strategy_dossier import build_strategy_dossier

__all__ = [
    "build_strategy_dossier",
    "decision_action",
    "decision_reason",
    "emit",
    "emit_error",
    "emit_response",
    "evaluation_from_output",
    "find_asset",
    "find_evaluation",
    "hypotheses",
    "load_json",
    "parse_datetime",
    "research_assets",
    "run_research_batch",
    "validate_outputs",
    "validation_payload",
]


def emit_response(
    command: str,
    result: object,
    *,
    status: str = "ok",
    warnings: tuple[str, ...] = (),
    error: str | None = None,
) -> None:
    emit(
        {
            "command": command,
            "status": status,
            "result": result,
            "warnings": list(warnings),
            "error": error,
        }
    )


def emit_error(
    command: str, error: Exception | str, *, warnings: tuple[str, ...] = ()
) -> None:
    emit_response(command, None, status="error", warnings=warnings, error=str(error))
