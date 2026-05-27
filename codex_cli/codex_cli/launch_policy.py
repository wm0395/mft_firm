from __future__ import annotations

from dataclasses import dataclass
import json


DEFAULT_EXECUTION_PROVIDER = "opencode"
DEFAULT_EXECUTION_MODEL = "google/gemini-2.5-pro"
MODEL_ROTATION = (
    "google/gemini-2.5-pro",
    "anthropic/claude-sonnet-4.5",
    "openai/gpt-5.1-codex",
    "google/gemini-3-pro",
    "anthropic/claude-opus-4.5",
)
REVIEW_MODEL_BY_PERSONA = {
    "architecture_reviewer": "google/gemini-2.5-pro",
    "complexity_reviewer": "anthropic/claude-sonnet-4.5",
    "determinism_auditor": "openai/gpt-5.1-codex",
    "financial_logic_auditor": "anthropic/claude-opus-4.5",
    "test_failure_reviewer": "google/gemini-3-pro",
}
RATE_LIMIT_MARKERS = (
    "429",
    "rate limit",
    "usage limit",
    "limit reached",
    "try again in",
    "too many requests",
    "quota",
)


@dataclass(frozen=True)
class LaunchTarget:
    provider: str
    model: str | None

    def to_dict(self) -> dict[str, str | None]:
        return {"provider": self.provider, "model": self.model}


def default_execution_model(objective: str, route_name: str) -> str:
    text = objective.lower()
    if route_name == "planner" or "design review" in text or "architecture" in text:
        return "anthropic/claude-sonnet-4.5"
    if any(marker in text for marker in ("generate tests", "bulk", "mass", "sweep")):
        return "openai/gpt-5.1-codex"
    return DEFAULT_EXECUTION_MODEL


def default_review_model(persona: str) -> str:
    return REVIEW_MODEL_BY_PERSONA.get(persona, DEFAULT_EXECUTION_MODEL)


def default_execution_target(objective: str, route_name: str, provider: str | None, model: str | None) -> LaunchTarget:
    if provider == "codex":
        return LaunchTarget("codex", model)
    return LaunchTarget(DEFAULT_EXECUTION_PROVIDER, model or default_execution_model(objective, route_name))


def default_review_target(persona: str, provider: str | None, model: str | None) -> LaunchTarget:
    if provider == "codex":
        return LaunchTarget("codex", model)
    return LaunchTarget(DEFAULT_EXECUTION_PROVIDER, model or default_review_model(persona))


def next_launch_target(target: LaunchTarget) -> LaunchTarget:
    if target.provider != DEFAULT_EXECUTION_PROVIDER:
        return LaunchTarget(DEFAULT_EXECUTION_PROVIDER, MODEL_ROTATION[0])
    current = target.model or MODEL_ROTATION[0]
    if current not in MODEL_ROTATION:
        return LaunchTarget(DEFAULT_EXECUTION_PROVIDER, MODEL_ROTATION[0])
    index = MODEL_ROTATION.index(current)
    next_index = (index + 1) % len(MODEL_ROTATION)
    return LaunchTarget(DEFAULT_EXECUTION_PROVIDER, MODEL_ROTATION[next_index])


def is_rate_limit_text(*texts: str) -> bool:
    joined = "\n".join(texts).lower()
    return any(marker in joined for marker in RATE_LIMIT_MARKERS)


def opencode_config_json() -> str:
    payload = {
        "$schema": "https://opencode.ai/config.json",
        "autoupdate": False,
        "share": "disabled",
        "model": DEFAULT_EXECUTION_MODEL,
        "instructions": [
            "AGENTS.md",
            "README.md",
            "docs/OPERATOR_GUIDE.md",
            "docs/prompts/*.md",
            "research/firm/*.md",
            "research/projects/*/README.md",
        ],
    }
    return json.dumps(payload, indent=2) + "\n"
