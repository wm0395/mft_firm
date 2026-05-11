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
    return {
        "task_id": task.id,
        "violations": _match_patterns(task, patterns),
        "known_patterns": patterns,
    }


def build_fix_prompt(task: Task, diagnosis: dict[str, object]) -> dict[str, object]:
    return {
        "task_id": task.id,
        "status": "ready",
        "prompt": "\n\n".join(
            (
                FIX_AGENT_PROMPT.strip(),
                "Task:\n" + json.dumps(task.to_dict(), indent=2),
                "Diagnosis:\n" + json.dumps(diagnosis, indent=2),
            )
        ),
    }


def _read_patterns(paths: ProjectPaths) -> dict[str, Any]:
    if not paths.violation_patterns.exists():
        return {}
    return json.loads(paths.violation_patterns.read_text(encoding="utf-8"))


def _match_patterns(task: Task, patterns: dict[str, Any]) -> list[dict[str, object]]:
    haystack = json.dumps(task.to_dict()).lower()
    matches = []
    for key, value in patterns.items():
        if not isinstance(value, dict):
            continue
        pattern = str(value.get("pattern", "")).lower()
        if pattern and pattern in haystack:
            matches.append(_match(key, value, 0.9))
            continue
        if any(token in haystack for token in key.split("_")):
            matches.append(_match(key, value, 0.6))
    return matches


def _match(key: str, value: dict[str, object], confidence: float) -> dict[str, object]:
    return {
        "violation": key,
        "cause": value.get("pattern", "matched known architecture violation"),
        "fix": value.get("fix", "apply minimal architecture-preserving fix"),
        "confidence": confidence,
    }
