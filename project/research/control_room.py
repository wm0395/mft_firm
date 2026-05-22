from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import json

try:
    import yaml  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover - optional dependency
    yaml = None  # type: ignore[assignment]

from project.research.control_room_renderers import (
    render_alpha101_status_markdown,
    render_data_source_status_markdown,
    render_multi_asset_status_markdown,
    render_research_control_room_markdown,
    render_weekly_review_markdown,
)


REPORT_FILENAMES = {
    "research_control_room": "research_control_room.md",
    "alpha101_status": "alpha101_status.md",
    "data_source_status": "data_source_status.md",
    "multi_asset_status": "multi_asset_status.md",
    "weekly_review": "weekly_review.md",
}


def materialize_reports(root: Path | None = None) -> dict[str, dict[str, Any]]:
    base = root or Path.cwd()
    reports_dir = base / "research" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    payloads = {
        "research_control_room": build_research_control_room_payload(base),
        "alpha101_status": build_alpha101_status_payload(base),
        "data_source_status": build_data_source_status_payload(base),
        "multi_asset_status": build_multi_asset_status_payload(base),
        "weekly_review": build_weekly_review_payload(base),
    }
    renderers = {
        "research_control_room": render_research_control_room_markdown,
        "alpha101_status": render_alpha101_status_markdown,
        "data_source_status": render_data_source_status_markdown,
        "multi_asset_status": render_multi_asset_status_markdown,
        "weekly_review": render_weekly_review_markdown,
    }
    for name, payload in payloads.items():
        _write_text(reports_dir / REPORT_FILENAMES[name], renderers[name](payload))
    return payloads


def build_research_control_room_payload(root: Path) -> dict[str, Any]:
    firm_state = _load_firm_state(root)
    alpha_state = _load_alpha101_state(root)
    queue = _load_queue(root)
    return {
        "generated_at": _now(),
        "last_updated": firm_state.get("last_updated", _now()),
        "active_projects": firm_state.get("active_projects", ()),
        "current_alpha_lanes": firm_state.get("current_alpha_lanes", ()),
        "asset_class_lanes": firm_state.get("asset_class_lanes", ()),
        "data_source_lanes": firm_state.get("data_source_lanes", ()),
        "blocked_lanes": firm_state.get("blocked_lanes", ()),
        "promoted_alphas": firm_state.get("promoted_alphas", ()),
        "demoted_alphas": firm_state.get("demoted_alphas", ()),
        "active_focus_queue": firm_state.get("active_focus_queue", ()),
        "next_actions": firm_state.get("next_actions", ()),
        "queue": queue,
        "alpha101": alpha_state,
    }


def build_alpha101_status_payload(root: Path) -> dict[str, Any]:
    alpha_state = _load_alpha101_state(root)
    promotion_rows = _promotion_rows(alpha_state)
    focus = alpha_state.get("strict_liquidity_focus", {})
    promotion_summary = alpha_state.get("promotion_summary", {})
    focus_queue = tuple(
        _string_list(focus.get("queue", alpha_state.get("active_focus_queue", ())))
    )
    return {
        "generated_at": _now(),
        "project_id": alpha_state.get(
            "project_id",
            "research_project:alpha101_formulaic_alphas",
        ),
        "project_status": alpha_state.get("project_status", "draft"),
        "focus_queue": focus_queue,
        "blocked_lanes": tuple(alpha_state.get("blocked_lanes", ())),
        "promoted_total": len(promotion_rows)
        or len(alpha_state.get("promoted_alphas", ())),
        "batch1_promotions": _count_items(promotion_rows, "batch", 1),
        "batch2_near_misses": _count_items(promotion_rows, "batch", 2),
        "median_active_sharpe": promotion_summary.get("median_active_sharpe", "nan"),
        "positive_sharpe_rate": promotion_summary.get("positive_sharpe_rate", "nan"),
        "validation_pass_rate": promotion_summary.get("validation_pass_rate", "nan"),
        "validation_failures": tuple(alpha_state.get("validation_failures", ())),
        "blocked_reasons": tuple(_blocked_reasons(alpha_state)),
        "current_focus_status": _focus_status_map(focus),
        "review_packs_ready": alpha_state.get("review_pack_status", "").startswith(
            "review"
        ),
        "next_queue": tuple(
            alpha_state.get("next_hygiene_steps", alpha_state.get("next_queue", ()))
        ),
        "promotion_rows": promotion_rows,
        "promoted_alphas": tuple(alpha_state.get("promoted_alphas", ())),
        "near_miss_alphas": tuple(alpha_state.get("near_miss_alphas", ())),
    }


def build_data_source_status_payload(root: Path) -> dict[str, Any]:
    registry = _load_registry(
        root / "research" / "data_sources" / "source_registry.yaml"
    )
    sources = tuple(_registry_entries(registry, "sources"))
    license_counts = _counter(sources, "license_status")
    adapter_counts = _counter(sources, "adapter_status")
    quality_counts = _counter(sources, "data_quality_status")
    return {
        "generated_at": _now(),
        "source_count": len(sources),
        "sources": sources,
        "license_counts": license_counts,
        "adapter_counts": adapter_counts,
        "quality_counts": quality_counts,
        "restricted_licenses": tuple(
            source.get("source_id", "")
            for source in sources
            if source.get("license_status") == "restricted"
        ),
        "unknown_licenses": tuple(
            source.get("source_id", "")
            for source in sources
            if source.get("license_status") == "unknown"
        ),
        "blocked_sources": tuple(
            source.get("source_id", "")
            for source in sources
            if source.get("adapter_status") != "production"
        ),
    }


def build_multi_asset_status_payload(root: Path) -> dict[str, Any]:
    registry = _load_registry(
        root / "research" / "asset_classes" / "asset_class_registry.yaml"
    )
    asset_classes = tuple(_registry_entries(registry, "asset_classes"))
    project = _load_registry(
        root / "research" / "projects" / "multi_asset_expansion" / "project.json"
    )
    queues = _load_multi_asset_queues(root)
    return {
        "generated_at": _now(),
        "project_status": project.get("status", "not_created")
        if isinstance(project, dict)
        else "not_created",
        "asset_class_count": len(asset_classes),
        "asset_classes": asset_classes,
        "queues": queues,
    }


def build_weekly_review_payload(root: Path) -> dict[str, Any]:
    control_room = build_research_control_room_payload(root)
    alpha101 = control_room["alpha101"]
    data_sources = build_data_source_status_payload(root)
    multi_asset = build_multi_asset_status_payload(root)
    return {
        "generated_at": _now(),
        "top_next_actions": tuple(control_room.get("next_actions", ()))[:5],
        "alpha101_focus_queue": tuple(alpha101.get("focus_queue", ())),
        "blocked_lanes": tuple(control_room.get("blocked_lanes", ())),
        "restricted_source_licenses": data_sources["restricted_licenses"],
        "unknown_source_licenses": data_sources["unknown_licenses"],
        "multi_asset_project_status": multi_asset["project_status"],
    }


def _load_firm_state(root: Path) -> dict[str, Any]:
    payload = _load_registry(root / "research" / "firm" / "daily_research_state.json")
    return payload if isinstance(payload, dict) else {}


def _load_queue(root: Path) -> tuple[dict[str, Any], ...]:
    payload = _load_registry(root / "research" / "firm" / "research_queue.json")
    tasks = payload.get("tasks") if isinstance(payload, dict) else payload
    if not isinstance(tasks, list):
        return ()
    return tuple(task for task in tasks if isinstance(task, dict))


def _load_alpha101_state(root: Path) -> dict[str, Any]:
    current = _load_registry(
        root
        / "research"
        / "projects"
        / "alpha101_formulaic_alphas"
        / "research_state.json"
    )
    if isinstance(current, dict):
        return current
    legacy = _load_registry(
        root
        / "research"
        / "projects"
        / "alpha101_formulaic_alphas"
        / "alpha101_research_state.json"
    )
    if not isinstance(legacy, dict):
        return {}
    promoted = tuple(_normalize_alpha_rows(legacy.get("promoted_queue", ())))
    focus = legacy.get("strict_liquidity_positive_focus", ())
    return {
        "project_id": legacy.get(
            "project_id",
            "research_project:alpha101_formulaic_alphas",
        ),
        "project_status": legacy.get("project_status", "draft"),
        "promoted_alphas": promoted,
        "active_focus_queue": (
            tuple(focus) if isinstance(focus, list) else tuple(focus or ())
        ),
        "blocked_lanes": tuple(legacy.get("blocked_lanes", ())),
        "median_active_sharpe": legacy.get(
            "strict_liquidity_median_test_active_sharpe",
            "nan",
        ),
        "positive_sharpe_rate": legacy.get(
            "strict_liquidity_positive_sharpe_rate",
            "nan",
        ),
        "validation_pass_rate": legacy.get("validation_pass_rate", "nan"),
        "validation_failures": tuple(legacy.get("validation_failed_checks", ())),
        "blocked_reasons": tuple(legacy.get("blockers", ())),
        "current_focus_status": {
            "alpha024": "positive",
            "alpha018": "borderline",
            "alpha040": "holdout",
            "alpha023": "positive",
        },
        "review_packs_ready": False,
        "next_queue": tuple(legacy.get("next_experiments", ())),
    }


def _promotion_rows(alpha_state: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    rows = alpha_state.get("promotion_rows")
    if isinstance(rows, list):
        return tuple(row for row in rows if isinstance(row, dict))
    rows = alpha_state.get("promoted_queue")
    if isinstance(rows, list):
        return tuple(row for row in rows if isinstance(row, dict))
    return ()


def _focus_status_map(focus: Any) -> dict[str, str]:
    if not isinstance(focus, dict):
        return {}
    queue = _string_list(focus.get("queue", ()))
    statuses = {}
    for name in queue:
        if name in _string_list(focus.get("positive", ())):
            statuses[name] = "positive"
        elif name in _string_list(focus.get("borderline", ())):
            statuses[name] = "borderline"
        elif name in _string_list(focus.get("holdout", ())):
            statuses[name] = "holdout"
        else:
            statuses[name] = "unknown"
    return statuses


def _blocked_reasons(alpha_state: dict[str, Any]) -> tuple[str, ...]:
    lanes = alpha_state.get("blocked_lanes", ())
    if not isinstance(lanes, list):
        return ()
    reasons = []
    for lane in lanes:
        if isinstance(lane, dict):
            reason = str(lane.get("reason", "")).strip()
            if reason:
                reasons.append(reason)
    return tuple(reasons)


def _string_list(values: Any) -> tuple[str, ...]:
    if isinstance(values, list):
        return tuple(str(item) for item in values if str(item))
    if isinstance(values, tuple):
        return tuple(str(item) for item in values if str(item))
    if isinstance(values, set):
        return tuple(str(item) for item in sorted(values) if str(item))
    return ()


def _normalize_alpha_rows(rows: Any) -> tuple[dict[str, Any], ...]:
    if not isinstance(rows, list):
        return ()
    return tuple(row for row in rows if isinstance(row, dict))


def _load_multi_asset_queues(root: Path) -> tuple[dict[str, Any], ...]:
    queues_dir = root / "research" / "projects" / "multi_asset_expansion" / "queues"
    if not queues_dir.exists():
        return ()
    rows: list[dict[str, Any]] = []
    for path in sorted(queues_dir.glob("*.yaml")):
        payload = _load_registry(path)
        if isinstance(payload, list):
            items = payload
        elif isinstance(payload, dict):
            items = payload.get("items", [])
        else:
            items = []
        for item in items:
            if isinstance(item, dict):
                rows.append(item)
    return tuple(rows)


def _registry_entries(payload: Any, key: str) -> tuple[dict[str, Any], ...]:
    if isinstance(payload, list):
        return tuple(item for item in payload if isinstance(item, dict))
    if isinstance(payload, dict):
        value = payload.get(key, ())
        if isinstance(value, list):
            return tuple(item for item in value if isinstance(item, dict))
    return ()


def _counter(entries: tuple[dict[str, Any], ...], field: str) -> dict[str, int]:
    counts = Counter(str(entry.get(field, "")) for entry in entries)
    return dict(sorted(counts.items()))


def _count_items(entries: tuple[dict[str, Any], ...], field: str, value: int) -> int:
    return sum(1 for entry in entries if int(entry.get(field, -1)) == value)


def _load_registry(path: Path) -> Any:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        if yaml is not None:
            return yaml.safe_load(text)
        raise


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()
