from __future__ import annotations

import json
from pathlib import Path

from .models import Task


PROMPTS_DIR = "prompts"
SYSTEM_PROMPT = "system.txt"
EXECUTOR_PROMPT = "executor.txt"
KNOWN_FAILURES = (
    "avoid signal leakage",
    "avoid raw data in hypothesis",
)


def build_prompt(task: Task, scratchpad: str, agents_rules: str) -> str:
    system_prompt = read_prompt(SYSTEM_PROMPT)
    executor_prompt = read_prompt(EXECUTOR_PROMPT)
    subtask = task.subtasks[0].to_dict() if task.subtasks else {
        "id": task.id,
        "desc": task.description,
        "files": task.files,
    }
    context = _build_context(task, agents_rules)

    return "\n\n".join(
        (
            system_prompt,
            _known_failure_patterns(),
            executor_prompt.format(
                SUBTASK=json.dumps(subtask, indent=2),
                CONTEXT=context,
                FILES=json.dumps(task.files, indent=2),
                SCRATCHPAD=scratchpad,
            ),
        )
    )


def read_prompt(name: str) -> str:
    path = Path(__file__).resolve().parent / PROMPTS_DIR / name
    if path.exists():
        return path.read_text(encoding="utf-8").strip()

    raise FileNotFoundError(f"Prompt file not found: {name}")


def _build_context(task: Task, agents_rules: str) -> str:
    return f"""Goal:
{task.description}

Context:
Task id: {task.id}
Route: {task.route}

AGENTS.md Rules:
{agents_rules}

Done when:
- Requested code changes are complete
- Reviewer verdict is recorded
- Tests or manual verification are documented
"""


def _known_failure_patterns() -> str:
    failures = "\n".join(f"- {failure}" for failure in KNOWN_FAILURES)
    return f"""KNOWN FAILURE PATTERNS:
{failures}"""
