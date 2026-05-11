from __future__ import annotations

from .models import ReviewPacket, Task
from .paths import ProjectPaths
from .prompts import build_review_packet


def review_task(
    task: Task,
    paths: ProjectPaths,
    scratchpad: str,
    retrieved_context: tuple[str, ...],
    provider: str,
    persona: str,
    budget: int,
) -> ReviewPacket:
    return build_review_packet(task, paths, scratchpad, retrieved_context, provider, persona, budget)
