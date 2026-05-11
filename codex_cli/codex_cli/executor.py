from __future__ import annotations

from .models import ExecutionPacket, Task
from .paths import ProjectPaths
from .prompts import build_execution_packet


def execute_task(
    task: Task,
    paths: ProjectPaths,
    scratchpad: str,
    retrieved_context: tuple[str, ...],
    provider: str,
    budget: int,
) -> ExecutionPacket:
    return build_execution_packet(task, paths, scratchpad, retrieved_context, provider, budget)
