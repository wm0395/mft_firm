from __future__ import annotations

import json
from pathlib import Path

from .cache import estimate_tokens
from .models import ExecutionPacket, PacketBlock, ReviewPacket, Task
from .paths import ProjectPaths
from .review_schema import reviewer_name


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
    "opencode": "Use this packet in OpenCode as the primary execution or review prompt.",
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
    blocks = _build_blocks(task, paths, scratchpad, retrieved_context, REVIEWER_PROMPT, persona)
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
    persona: str | None = None,
) -> tuple[PacketBlock, ...]:
    blocks = [
        PacketBlock("system_rules", read_prompt(SYSTEM_PROMPT)),
        PacketBlock("agents_rules", _read_agents(paths)),
        PacketBlock("task", _task_block(task)),
        PacketBlock("scratchpad", scratchpad),
        PacketBlock("retrieved_context", _context_block(retrieved_context)),
        PacketBlock("relevant_files", _files_block(task.files)),
        PacketBlock("check_results", _check_results_block(task)),
        PacketBlock("known_failure_patterns", _known_failures()),
    ]
    if persona:
        blocks.append(PacketBlock("reviewer_persona", _reviewer_prompt(paths, persona)))
    blocks.append(PacketBlock("instruction", read_prompt(prompt_name)))
    return tuple(blocks)


def _read_agents(paths: ProjectPaths) -> str:
    return paths.agents_file.read_text(encoding="utf-8") if paths.agents_file.exists() else ""


def _task_block(task: Task) -> str:
    payload = {
        "id": task.id,
        "objective": task.objective,
        "files": list(task.files),
        "constraints": list(task.constraints),
        "done_conditions": list(task.done_conditions),
        "risk_level": task.risk_level,
        "allowed_change_set": list(task.allowed_change_set),
        "required_checks": list(task.required_checks),
        "required_reviewers": list(task.required_reviewers),
        "workflow_stage": task.workflow_stage,
        "review_status": task.review_status,
        "implementation_status": task.implementation_status,
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


def _check_results_block(task: Task) -> str:
    if not task.check_history:
        return "Latest Managed Checks:\n- None recorded."
    latest = task.check_history[-1]
    lines = ["Latest Managed Checks:"]
    lines.append(f"- Status: {latest.get('status', 'unknown')}")
    for item in latest.get("checks", ()):
        if not isinstance(item, dict):
            continue
        name = item.get("name", "unknown")
        status = item.get("status", "unknown")
        lines.append(f"- {name}: {status}")
    return "\n".join(lines)


def _reviewer_prompt(paths: ProjectPaths, persona: str) -> str:
    reviewer = reviewer_name(persona)
    candidates = (
        paths.workspace_root / "docs" / "prompts" / f"{reviewer}.md",
        Path(__file__).resolve().parents[2] / "docs" / "prompts" / f"{reviewer}.md",
        paths.workspace_root / "agents" / "prompts" / f"{reviewer}.md",
        Path(__file__).resolve().parents[2] / "agents" / "prompts" / f"{reviewer}.md",
    )
    for target in candidates:
        if not target.exists():
            continue
        text = target.read_text(encoding="utf-8").strip()
        if not text:
            raise ValueError(f"Reviewer prompt is empty: {reviewer}")
        return text
    raise FileNotFoundError(f"Reviewer prompt not found: {reviewer}")


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
