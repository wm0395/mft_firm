from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from .models import IndexEntry, TokenLedgerEntry
from .paths import ProjectPaths


SYMBOL_PATTERN = re.compile(r"^(?:def|class)\s+([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE)
SKIP_PREFIXES = (
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".env",
    "__pycache__",
    "codex_cli/tasks",
    "codex_cli/memory",
    "codex_cli/runtime",
    "codex_cli/state",
    "codex_cli/mft_codex_cli.egg-info",
)
TEXT_SUFFIXES = {".py", ".md", ".toml", ".yml", ".yaml", ".json", ".txt"}


def build_index(paths: ProjectPaths) -> dict[str, object]:
    entries = [_index_file(path, paths.workspace_root) for path in _candidate_files(paths.workspace_root)]
    for entry in entries:
        target = paths.cache_index / f"{_safe_name(entry.path)}.json"
        target.write_text(json.dumps(entry.to_dict(), indent=2) + "\n", encoding="utf-8")
    return {"status": "ready", "entries": len(entries)}


def cache_status(paths: ProjectPaths) -> dict[str, object]:
    index_entries = sorted(paths.cache_index.glob("*.json"))
    token_entries = sorted(paths.cache_tokens.rglob("*.json"))
    return {
        "status": "ready",
        "index_entries": len(index_entries),
        "token_entries": len(token_entries),
        "stale_entries": 0,
    }


def retrieve_context(paths: ProjectPaths, query: str, limit: int = 5) -> tuple[str, ...]:
    entries = retrieve_context_entries(paths, query, (), limit)
    return tuple(entry.path for entry in entries)


def retrieve_context_entries(
    paths: ProjectPaths,
    query: str,
    declared_files: tuple[str, ...],
    limit: int = 5,
) -> tuple[IndexEntry, ...]:
    scored = []
    for entry in _load_index(paths):
        score = _score(query.lower(), entry, declared_files)
        if score > 0:
            scored.append((score, entry))
    scored.sort(key=lambda item: (-item[0], item[1].path))
    return tuple(entry for _, entry in scored[:limit])


def render_context_document(paths: ProjectPaths, entry: IndexEntry, max_lines: int = 20) -> str:
    target = paths.workspace_root / entry.path
    if not target.exists():
        return f"File: {entry.path}\nSummary: {entry.summary}"
    snippet = "\n".join(target.read_text(encoding="utf-8").splitlines()[:max_lines]).strip()
    lines = [f"File: {entry.path}", f"Summary: {entry.summary}"]
    if entry.symbols:
        lines.append("Symbols: " + ", ".join(entry.symbols))
    if snippet:
        lines.extend(("Snippet:", snippet))
    return "\n".join(lines)


def estimate_tokens(paths: ProjectPaths, provider: str, blocks: tuple[tuple[str, str], ...]) -> tuple[int, list[dict[str, object]]]:
    total = 0
    ledger_entries: list[dict[str, object]] = []
    for kind, content in blocks:
        token_count, entry = _cache_tokens(paths, kind, kind, provider, content)
        total += token_count
        ledger_entries.append(entry.to_dict())
    return total, ledger_entries


def _candidate_files(root: Path) -> list[Path]:
    files = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        relative = path.relative_to(root).as_posix()
        if any(relative.startswith(prefix) for prefix in SKIP_PREFIXES):
            continue
        files.append(path)
    return files


def _index_file(path: Path, root: Path) -> IndexEntry:
    text = path.read_text(encoding="utf-8")
    relative = path.relative_to(root).as_posix()
    return IndexEntry(
        path=relative,
        sha256=_sha256(text),
        symbols=tuple(SYMBOL_PATTERN.findall(text)),
        summary=_summary(text),
        tags=_tags(relative),
        mtime=path.stat().st_mtime,
    )


def _summary(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:120]
    return ""


def _tags(relative: str) -> tuple[str, ...]:
    return tuple(relative.split("/")[:2])


def _score(query: str, entry: IndexEntry, declared_files: tuple[str, ...]) -> int:
    haystacks = (entry.path.lower(), entry.summary.lower(), " ".join(entry.symbols).lower())
    score = sum(2 for haystack in haystacks if any(token in haystack for token in query.split()))
    score += _declared_file_bonus(entry.path, declared_files)
    return score


def _declared_file_bonus(path: str, declared_files: tuple[str, ...]) -> int:
    bonus = 0
    for declared in declared_files:
        if path == declared:
            bonus = max(bonus, 100)
        elif declared and path.startswith(f"{declared.rstrip('/')}/"):
            bonus = max(bonus, 80)
    return bonus


def _load_index(paths: ProjectPaths) -> list[IndexEntry]:
    entries = []
    for path in sorted(paths.cache_index.glob("*.json")):
        entries.append(IndexEntry(**json.loads(path.read_text(encoding="utf-8"))))
    return entries


def _cache_tokens(
    paths: ProjectPaths,
    kind: str,
    source: str,
    provider: str,
    content: str,
) -> tuple[int, TokenLedgerEntry]:
    content_hash = _sha256(content)
    provider_dir = paths.cache_tokens / provider
    provider_dir.mkdir(parents=True, exist_ok=True)
    target = provider_dir / f"{content_hash}.json"
    if target.exists():
        entry = TokenLedgerEntry(**json.loads(target.read_text(encoding="utf-8")))
        return entry.token_count, entry
    entry = TokenLedgerEntry(
        kind=kind,
        source=source,
        provider=provider,
        content_hash=content_hash,
        tokenizer="deterministic-wordcount-v1",
        token_count=len(content.split()),
    )
    target.write_text(json.dumps(entry.to_dict(), indent=2) + "\n", encoding="utf-8")
    return entry.token_count, entry


def _safe_name(value: str) -> str:
    return value.replace("/", "__")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
