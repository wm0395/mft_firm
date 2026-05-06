from __future__ import annotations

import json
from typing import Any

from .models import Task
from .paths import ProjectPaths


FIX_AGENT_PROMPT = """Goal:
Fix architecture violations ONLY.

Rules:
- no redesign
- no new abstractions
- preserve behavior

Steps:
1. identify violation
2. apply minimal fix
3. revalidate
"""


def diagnose_task(task: Task, paths: ProjectPaths) -> dict[str, object]:
    patterns = _read_patterns(paths)
    matched = _match_patterns(task, patterns)
    return {
        "task_id": task.id,
        "violations": matched,
        "known_patterns": patterns,
    }


def build_fix_prompt(task: Task, diagnosis: dict[str, object]) -> dict[str, object]:
    return {
        "task_id": task.id,
        "status": "ready",
        "message": "Fix prompt built. Apply this prompt to Codex for the architecture-only fix step.",
        "prompt": "\n\n".join(
            (
                FIX_AGENT_PROMPT.strip(),
                f"Task:\n{json.dumps(task.to_dict(), indent=2)}",
                f"Diagnosis:\n{json.dumps(diagnosis, indent=2)}",
            )
        ),
    }


def _read_patterns(paths: ProjectPaths) -> dict[str, Any]:
    if not paths.violation_patterns.exists():
        return {}
    return json.loads(paths.violation_patterns.read_text(encoding="utf-8"))


def _match_patterns(task: Task, patterns: dict[str, Any]) -> list[dict[str, object]]:
    review = task.review or {}
    haystack = json.dumps(
        {
            "description": task.description,
            "subtasks": [subtask.to_dict() for subtask in task.subtasks],
            "review": review,
        }
    ).lower()

    matches = []
    for key, value in patterns.items():
        pattern_text = str(value.get("pattern", "")).lower() if isinstance(value, dict) else ""
        tokens = [token for token in key.split("_") if token]
        if pattern_text and pattern_text in haystack:
            matches.append(_match(key, value, "pattern"))
            continue
        if any(token in haystack for token in tokens):
            matches.append(_match(key, value, "keyword"))

    return matches


def _match(key: str, value: Any, source: str) -> dict[str, object]:
    if not isinstance(value, dict):
        value = {}
    return {
        "violation": key,
        "cause": value.get("pattern", "matched known architecture violation"),
        "fix": value.get("fix", "apply minimal architecture-preserving fix"),
        "confidence": 0.9 if source == "pattern" else 0.6,
    }
