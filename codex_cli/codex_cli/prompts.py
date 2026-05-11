from __future__ import annotations

import json
from pathlib import Path

from .cache import estimate_tokens
from .models import ExecutionPacket, PacketBlock, ReviewPacket, Task
from .paths import ProjectPaths


PROMPTS_DIR = "prompts"
SYSTEM_PROMPT = "system.txt"
EXECUTOR_PROMPT = "executor.txt"
REVIEWER_PROMPT = "reviewer.txt"
KNOWN_FAILURES = (
    "avoid signal leakage",
    "avoid cross-layer dependencies",
    "avoid mutable dataclasses",
)
PROVIDER_HINTS = {
    "codex": "Paste this packet into Codex CLI as the implementation prompt.",
    "gemini": "Use this packet in Gemini as the planning or review prompt.",
    "opencode": "Use this packet in OpenCode for bulk execution or test generation.",
}


def build_execution_packet(
    task: Task,
    paths: ProjectPaths,
    scratchpad: str,
    retrieved_context: tuple[str, ...],
    provider: str,
    budget: int,
) -> ExecutionPacket:
    blocks = _build_blocks(task, paths, scratchpad, retrieved_context, EXECUTOR_PROMPT)
    trimmed = _trim_blocks(blocks, provider, budget, paths)
    prompt = "\n\n".join(block.content for block in trimmed)
    token_estimate, _ = estimate_tokens(paths, provider, _as_pairs(trimmed))
    return ExecutionPacket(
        task_id=task.id,
        provider=provider,
        role="executor",
        budget=budget,
        prompt=prompt,
        prompt_blocks=trimmed,
        retrieved_context=retrieved_context,
        token_estimate=token_estimate,
        command_hint=PROVIDER_HINTS[provider],
    )


def build_review_packet(
    task: Task,
    paths: ProjectPaths,
    scratchpad: str,
    retrieved_context: tuple[str, ...],
    provider: str,
    persona: str,
    budget: int,
) -> ReviewPacket:
    blocks = _build_blocks(task, paths, scratchpad, retrieved_context, REVIEWER_PROMPT)
    trimmed = _trim_blocks(blocks, provider, budget, paths)
    prompt = "\n\n".join(block.content for block in trimmed)
    token_estimate, _ = estimate_tokens(paths, provider, _as_pairs(trimmed))
    return ReviewPacket(
        task_id=task.id,
        provider=provider,
        persona=persona,
        budget=budget,
        prompt=prompt,
        prompt_blocks=trimmed,
        retrieved_context=retrieved_context,
        token_estimate=token_estimate,
        command_hint=PROVIDER_HINTS[provider],
    )


def read_prompt(name: str) -> str:
    path = Path(__file__).resolve().parent / PROMPTS_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {name}")
    return path.read_text(encoding="utf-8").strip()


def _build_blocks(
    task: Task,
    paths: ProjectPaths,
    scratchpad: str,
    retrieved_context: tuple[str, ...],
    prompt_name: str,
) -> tuple[PacketBlock, ...]:
    return (
        PacketBlock("system_rules", read_prompt(SYSTEM_PROMPT)),
        PacketBlock("agents_rules", _read_agents(paths)),
        PacketBlock("task", _task_block(task)),
        PacketBlock("scratchpad", scratchpad),
        PacketBlock("retrieved_context", _context_block(retrieved_context)),
        PacketBlock("relevant_files", _files_block(task.files)),
        PacketBlock("known_failure_patterns", _known_failures()),
        PacketBlock("instruction", read_prompt(prompt_name)),
    )


def _read_agents(paths: ProjectPaths) -> str:
    return paths.agents_file.read_text(encoding="utf-8") if paths.agents_file.exists() else ""


def _task_block(task: Task) -> str:
    payload = {
        "id": task.id,
        "objective": task.objective,
        "files": list(task.files),
        "constraints": list(task.constraints),
        "done_conditions": list(task.done_conditions),
        "route": task.route,
        "recommended_provider": task.recommended_provider,
    }
    return "Task:\n" + json.dumps(payload, indent=2)


def _context_block(retrieved_context: tuple[str, ...]) -> str:
    items = "\n".join(f"- {path}" for path in retrieved_context) if retrieved_context else "- None retrieved."
    return f"Retrieved Context:\n{items}"


def _files_block(files: tuple[str, ...]) -> str:
    items = "\n".join(f"- {path}" for path in files) if files else "- None declared."
    return f"Relevant Files:\n{items}"


def _known_failures() -> str:
    return "KNOWN FAILURE PATTERNS:\n" + "\n".join(f"- {item}" for item in KNOWN_FAILURES)


def _trim_blocks(
    blocks: tuple[PacketBlock, ...],
    provider: str,
    budget: int,
    paths: ProjectPaths,
) -> tuple[PacketBlock, ...]:
    kept = list(blocks)
    total, _ = estimate_tokens(paths, provider, _as_pairs(tuple(kept)))
    while total > budget and len(kept) > 6:
        kept.pop(4)
        total, _ = estimate_tokens(paths, provider, _as_pairs(tuple(kept)))
    return tuple(kept)


def _as_pairs(blocks: tuple[PacketBlock, ...]) -> tuple[tuple[str, str], ...]:
    return tuple((block.name, block.content) for block in blocks)
