from __future__ import annotations

from .models import Task
from .prompts import build_prompt


def execute_task(task: Task, scratchpad: str, agents_rules: str) -> dict[str, str]:
    prompt = build_prompt(task, scratchpad, agents_rules)
    return {
        "status": "ready",
        "message": "Execution prompt built. Apply this prompt to Codex for the implementation step.",
        "prompt": prompt,
    }
