from __future__ import annotations

import json
from typing import Any


def render_research_control_room_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Research Control Room",
        "",
        f"- generated_at: {payload['generated_at']}",
        f"- last_updated: {payload['last_updated']}",
        f"- active_projects: {len(payload['active_projects'])}",
        f"- blocked_lanes: {len(payload['blocked_lanes'])}",
        f"- promoted_alphas: {len(payload['promoted_alphas'])}",
        f"- demoted_alphas: {len(payload['demoted_alphas'])}",
        "",
        "## Active Projects",
        _bullet_lines(payload["active_projects"]),
        "",
        "## Active Focus Queue",
        _bullet_lines(payload["active_focus_queue"]),
        "",
        "## Blocked Lanes",
        _bullet_lines(payload["blocked_lanes"]),
        "",
        "## Next Actions",
        _bullet_lines(payload["next_actions"]),
        "",
        "## Queue",
        _table(
            ("task_id", "owner_role", "priority", "status"),
            _queue_rows(payload["queue"]),
        ),
    ]
    return "\n".join(line for line in lines if line is not None).strip() + "\n"


def render_alpha101_status_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Alpha101 Status",
        "",
        f"- project_id: {payload['project_id']}",
        f"- project_status: {payload['project_status']}",
        f"- promoted_total: {payload['promoted_total']}",
        f"- batch1_promotions: {payload['batch1_promotions']}",
        f"- batch2_near_misses: {payload['batch2_near_misses']}",
        f"- median_active_sharpe: {payload['median_active_sharpe']}",
        f"- positive_sharpe_rate: {payload['positive_sharpe_rate']}",
        f"- validation_pass_rate: {payload['validation_pass_rate']}",
        "",
        "## Focus Queue",
        _bullet_lines(payload["focus_queue"]),
        "",
        "## Blocked Lanes",
        _bullet_lines(payload["blocked_lanes"]),
        "",
        "## Current Focus Status",
        _table(("alpha_id", "status"), payload["current_focus_status"].items()),
        "",
        "## Next Queue",
        _bullet_lines(payload["next_queue"]),
    ]
    return "\n".join(line for line in lines if line is not None).strip() + "\n"


def render_data_source_status_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Data Source Status",
        "",
        f"- generated_at: {payload['generated_at']}",
        f"- source_count: {payload['source_count']}",
        f"- restricted_licenses: {len(payload['restricted_licenses'])}",
        f"- unknown_licenses: {len(payload['unknown_licenses'])}",
        f"- blocked_sources: {len(payload['blocked_sources'])}",
        "",
        "## Restricted Licenses",
        _bullet_lines(payload["restricted_licenses"]),
        "",
        "## Unknown Licenses",
        _bullet_lines(payload["unknown_licenses"]),
        "",
        "## Sources",
        _table(
            (
                "source_id",
                "license_status",
                "adapter_status",
                "data_quality_status",
                "owner_role",
            ),
            (
                (
                    source.get("source_id", ""),
                    source.get("license_status", ""),
                    source.get("adapter_status", ""),
                    source.get("data_quality_status", ""),
                    source.get("owner_role", ""),
                )
                for source in payload["sources"]
            ),
        ),
    ]
    return "\n".join(lines).strip() + "\n"


def render_multi_asset_status_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Multi-Asset Status",
        "",
        f"- generated_at: {payload['generated_at']}",
        f"- project_status: {payload['project_status']}",
        f"- project_phase: {payload['project_phase']}",
        f"- asset_class_count: {payload['asset_class_count']}",
        "",
        "## Asset Classes",
        _table(
            ("asset_class_id", "benchmark", "price_type"),
            (
                (
                    asset_class.get("asset_class_id", ""),
                    asset_class.get("benchmark", ""),
                    asset_class.get("price_type", ""),
                )
                for asset_class in payload["asset_classes"]
            ),
        ),
        "",
        "## Queues",
        _table(
            ("research_id", "asset_class", "source_dependency"),
            _multi_asset_queue_rows(payload["queues"]),
        ),
    ]
    return "\n".join(lines).strip() + "\n"


def render_weekly_review_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Weekly Review",
        "",
        f"- generated_at: {payload['generated_at']}",
        "",
        "## Top Next Actions",
        _bullet_lines(payload["top_next_actions"]),
        "",
        "## Alpha101 Focus Queue",
        _bullet_lines(payload["alpha101_focus_queue"]),
        "",
        "## Blocked Lanes",
        _bullet_lines(payload["blocked_lanes"]),
        "",
        "## Unknown Source Licenses",
        _bullet_lines(payload["unknown_source_licenses"]),
        "",
        "## Restricted Source Licenses",
        _bullet_lines(payload["restricted_source_licenses"]),
        "",
        f"- multi_asset_project_status: {payload['multi_asset_project_status']}",
        f"- multi_asset_project_phase: {payload['multi_asset_project_phase']}",
    ]
    return "\n".join(lines).strip() + "\n"


def _queue_rows(entries: Any) -> tuple[tuple[str, str, str, str], ...]:
    rows = []
    if not isinstance(entries, (list, tuple)):
        return ()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        rows.append(
            (
                str(entry.get("task_id", "")),
                str(entry.get("owner_role", "")),
                str(entry.get("priority", "")),
                str(entry.get("status", "")),
            )
        )
    return tuple(rows)


def _multi_asset_queue_rows(entries: Any) -> tuple[tuple[str, str, str], ...]:
    rows = []
    if not isinstance(entries, (list, tuple)):
        return ()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        source_dependency = entry.get("source_dependency", ())
        if isinstance(source_dependency, list):
            dependency_text = ", ".join(str(item) for item in source_dependency)
        else:
            dependency_text = str(source_dependency)
        rows.append(
            (
                str(entry.get("research_id", "")),
                str(entry.get("asset_class", "")),
                dependency_text,
            )
        )
    return tuple(rows)


def _table(headers: tuple[str, ...], rows: Any) -> str:
    materialized = tuple(rows)
    if not materialized:
        return "_none_\n"
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in materialized:
        lines.append("| " + " | ".join(_cell(value) for value in row) + " |")
    return "\n".join(lines)


def _bullet_lines(items: Any) -> str:
    values = tuple(_bullet_text(item) for item in items if _bullet_text(item))
    if not values:
        return "_none_"
    return "\n".join(f"- {item}" for item in values)


def _bullet_text(item: Any) -> str:
    if isinstance(item, str):
        return item.strip()
    if isinstance(item, dict):
        keys = (
            "project_id",
            "alpha_id",
            "lane_id",
            "lane",
            "task_id",
            "source_id",
            "asset_class_id",
            "status",
            "phase",
            "reason",
            "priority",
            "owner_role",
            "asset_class",
            "source_dependency",
            "strict_liquidity_active_sharpe",
        )
        parts = []
        for key in keys:
            value = item.get(key)
            if value not in (None, ""):
                parts.append(f"{key}={value}")
        if parts:
            return " | ".join(parts)
        return json.dumps(item, sort_keys=True)
    if (
        isinstance(item, tuple)
        and len(item) == 2
        and all(isinstance(value, str) for value in item)
    ):
        return f"{item[0]}: {item[1]}"
    text = str(item).strip()
    return text


def _cell(value: Any) -> str:
    if isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], str):
        return f"{value[0]}: {value[1]}"
    if isinstance(value, dict):
        if "alpha_id" in value:
            return str(value["alpha_id"])
        if "task_id" in value:
            return str(value["task_id"])
        return json.dumps(value, sort_keys=True)
    if value is None:
        return ""
    return str(value)
