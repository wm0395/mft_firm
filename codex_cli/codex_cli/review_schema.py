from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any


REVIEW_APPROVE = "approve"
REVIEW_CHANGES_REQUESTED = "changes_requested"
REVIEW_FAILED = "review_failed"
REVIEW_STATUS_APPROVED = "approved"


@dataclass(frozen=True)
class ReviewViolation:
    file: str
    rule: str
    evidence: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReviewViolation":
        return cls(
            file=_require_string(data, "file"),
            rule=_require_string(data, "rule"),
            evidence=_require_string(data, "evidence"),
        )

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ReviewEvidence:
    file: str
    reason: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReviewEvidence":
        return cls(
            file=_require_string(data, "file"),
            reason=_require_string(data, "reason"),
        )

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ReviewDecision:
    decision: str
    reviewer: str
    violations: tuple[ReviewViolation, ...]
    required_fixes: tuple[str, ...]
    evidence: tuple[ReviewEvidence, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any], expected_reviewer: str) -> "ReviewDecision":
        decision = _require_string(data, "decision")
        if decision not in {REVIEW_APPROVE, REVIEW_CHANGES_REQUESTED}:
            raise ValueError(f"Unsupported review decision: {decision}")
        reviewer = _require_string(data, "reviewer")
        if reviewer != expected_reviewer:
            raise ValueError(f"Reviewer mismatch: expected {expected_reviewer}, got {reviewer}")
        violations = tuple(ReviewViolation.from_dict(item) for item in _require_object_list(data, "violations"))
        evidence = tuple(ReviewEvidence.from_dict(item) for item in _require_object_list(data, "evidence"))
        required_fixes = _require_string_list(data, "required_fixes")
        return cls(
            decision=decision,
            reviewer=reviewer,
            violations=violations,
            required_fixes=required_fixes,
            evidence=evidence,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "reviewer": self.reviewer,
            "violations": [item.to_dict() for item in self.violations],
            "required_fixes": list(self.required_fixes),
            "evidence": [item.to_dict() for item in self.evidence],
        }


def parse_review_output(text: str, expected_reviewer: str) -> ReviewDecision:
    payload = _load_review_payload(text)
    if not isinstance(payload, dict):
        raise ValueError("Review output must decode to a JSON object.")
    return ReviewDecision.from_dict(payload, expected_reviewer)


def review_status(decision: str) -> str:
    if decision == REVIEW_APPROVE:
        return REVIEW_STATUS_APPROVED
    if decision == REVIEW_CHANGES_REQUESTED:
        return REVIEW_CHANGES_REQUESTED
    return REVIEW_FAILED


def reviewer_name(persona: str) -> str:
    aliases = {
        "architecture": "architecture_reviewer",
        "architecture_reviewer": "architecture_reviewer",
        "complexity": "complexity_reviewer",
        "complexity_reviewer": "complexity_reviewer",
        "determinism": "determinism_auditor",
        "determinism_auditor": "determinism_auditor",
        "financial_logic": "financial_logic_auditor",
        "financial_logic_auditor": "financial_logic_auditor",
        "test_failure": "test_failure_reviewer",
        "test_failure_reviewer": "test_failure_reviewer",
    }
    return aliases.get(persona, persona)


def _require_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Review field '{key}' must be a non-empty string.")
    return value.strip()


def _require_string_list(data: dict[str, Any], key: str) -> tuple[str, ...]:
    values = _require_list(data, key)
    result = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Review field '{key}' must contain only non-empty strings.")
        result.append(value.strip())
    return tuple(result)


def _require_object_list(data: dict[str, Any], key: str) -> tuple[dict[str, Any], ...]:
    values = _require_list(data, key)
    result = []
    for value in values:
        if not isinstance(value, dict):
            raise ValueError(f"Review field '{key}' must contain only JSON objects.")
        result.append(value)
    return tuple(result)


def _require_list(data: dict[str, Any], key: str) -> list[Any]:
    value = data.get(key)
    if not isinstance(value, list):
        raise ValueError(f"Review field '{key}' must be a list.")
    return value


def _load_review_payload(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if not stripped:
        raise ValueError("Review output must be a single JSON object.")
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        payload = _payload_from_jsonl(stripped)
    if not isinstance(payload, dict):
        raise ValueError("Review output must be a single JSON object.")
    return payload


def _payload_from_jsonl(text: str) -> dict[str, Any]:
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        payload = _payload_from_event(event)
        if payload is not None:
            return payload
    raise ValueError("Review output must be a single JSON object.")


def _payload_from_event(event: object) -> dict[str, Any] | None:
    if not isinstance(event, dict):
        return None
    item = event.get("item")
    if not isinstance(item, dict):
        return None
    if item.get("type") != "agent_message":
        return None
    text = item.get("text")
    if not isinstance(text, str):
        return None
    try:
        payload = json.loads(text.strip())
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None
