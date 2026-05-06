from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class KnowledgeEntry:
    entry_type: Literal["hypothesis", "insight", "observation"]
    content: str
    linked_hypothesis: str
    source: Literal["book", "experience", "data"]
    confidence: str
    evidence: Literal["backtest", "live"]


def create_entry(
    entry_type: Literal["hypothesis", "insight", "observation"],
    content: str,
    linked_hypothesis: str,
    source: Literal["book", "experience", "data"],
    confidence: str,
    evidence: Literal["backtest", "live"],
) -> KnowledgeEntry:
    if not content or not linked_hypothesis:
        raise ValueError("content and linked_hypothesis are required")
    return KnowledgeEntry(entry_type, content, linked_hypothesis, source, confidence, evidence)
