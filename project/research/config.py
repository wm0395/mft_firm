from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from typing import Any, Mapping

try:
    import tomllib
except ImportError:  # pragma: no cover - Python 3.12 ships tomllib
    tomllib = None  # type: ignore[assignment]
try:
    import yaml  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover - dependency is declared with the project
    yaml = None  # type: ignore[assignment]

from project.research.parameter_grid import (
    canonical_parameter_grid,
    parameter_axes_from_mapping,
)
from project.research.models import ParameterAxis, ResearchFamily
from project.research.promotion import PromotionRules


@dataclass(frozen=True)
class ResearchConfig:
    strategy_family: ResearchFamily
    asset_symbol: str
    start_date: str
    end_date: str
    parameter_axes: tuple[ParameterAxis, ...]
    dataset_snapshot_id: str | None = None
    slippage_bps: float = 1.0
    promotion_rules: PromotionRules | None = None


@dataclass(frozen=True)
class ResearchRunConfig:
    research_project_id: str
    dataset_snapshot_id: str
    export_dir: str = "reports/research"
    strategy_grid_paths: tuple[str, ...] = ()



def load_research_config(source: Mapping[str, Any] | str | Path) -> ResearchConfig:
    payload = _load_payload(source)
    return _config_from_mapping(payload)


def parse_research_config(source: Mapping[str, Any] | str | Path) -> ResearchConfig:
    return load_research_config(source)


def load_research_run_config(source: Mapping[str, Any] | str | Path) -> ResearchRunConfig:
    payload = _load_payload(source)
    return _workflow_config_from_mapping(payload)


def research_config_hash(config: ResearchConfig) -> str:
    payload = json.dumps(
        {
            "strategy_family": config.strategy_family,
            "asset_symbol": config.asset_symbol,
            "start_date": config.start_date,
            "end_date": config.end_date,
            "dataset_snapshot_id": config.dataset_snapshot_id,
            "slippage_bps": config.slippage_bps,
            "parameter_axes": [
                {"name": axis.name, "values": list(axis.values)}
                for axis in config.parameter_axes
            ],
            "promotion_rules": _promotion_payload(config.promotion_rules),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    from hashlib import sha256

    return sha256(payload.encode("utf-8")).hexdigest()


def _config_from_mapping(mapping: Mapping[str, Any]) -> ResearchConfig:
    strategy_family = _strategy_family(mapping)
    parameter_axes = _parameter_axes(strategy_family, mapping)
    promotion_source = mapping.get("promotion") if "promotion" in mapping else mapping.get("promotion_rules")
    promotion_rules = _promotion_rules(promotion_source)
    return ResearchConfig(
        strategy_family=strategy_family,
        asset_symbol=str(mapping["asset_symbol"]).upper(),
        start_date=str(mapping["start_date"]),
        end_date=str(mapping["end_date"]),
        parameter_axes=parameter_axes,
        dataset_snapshot_id=_optional_text(mapping.get("dataset_snapshot_id")),
        slippage_bps=float(mapping.get("slippage_bps", 1.0)),
        promotion_rules=promotion_rules,
    )


def _parameter_axes(
    strategy_family: ResearchFamily,
    mapping: Mapping[str, Any],
) -> tuple[ParameterAxis, ...]:
    grid = mapping.get("parameter_grid") or mapping.get("grid") or mapping.get("axes")
    if grid is None:
        return canonical_parameter_grid(strategy_family)
    if isinstance(grid, Mapping):
        return parameter_axes_from_mapping(strategy_family, grid)
    if isinstance(grid, list):
        axes = []
        for item in grid:
            axes.append(ParameterAxis(str(item["name"]), tuple(item["values"])))
        return tuple(axes)
    raise ValueError("parameter_grid must be a mapping or list")


def _promotion_rules(value: Any) -> PromotionRules | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError("promotion rules must be a mapping")
    return PromotionRules(
        minimum_total_trades=int(value.get("minimum_total_trades", 0)),
        minimum_win_rate=float(value.get("minimum_win_rate", 0.0)),
        minimum_total_return_pct=float(value.get("minimum_total_return_pct", 0.0)),
        maximum_drawdown_pct=float(value.get("maximum_drawdown_pct", float("inf"))),
        minimum_sharpe_like_score=float(value.get("minimum_sharpe_like_score", 0.0)),
    )


def _strategy_family(mapping: Mapping[str, Any]) -> ResearchFamily:
    family = str(mapping.get("strategy_family") or mapping.get("family"))
    if family not in {"momentum_continuation", "mean_reversion"}:
        raise ValueError(f"unsupported strategy family: {family}")
    return family  # type: ignore[return-value]


def _load_payload(source: Mapping[str, Any] | str | Path) -> Mapping[str, Any]:
    if isinstance(source, Mapping):
        return source
    if isinstance(source, Path):
        text = source.read_text(encoding="utf-8")
    else:
        text = str(source)
        if not _looks_like_config_text(text) and Path(text).exists():
            text = Path(text).read_text(encoding="utf-8")
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        value = _load_non_json_payload(text)
    if not isinstance(value, Mapping):
        raise ValueError("research config must decode to a mapping")
    return value


def _load_non_json_payload(text: str) -> Any:
    if tomllib is not None:
        try:
            return tomllib.loads(text)
        except Exception:
            pass
    if yaml is not None:
        return yaml.safe_load(text)
    raise ValueError("YAML support is unavailable")


def _optional_text(value: Any) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def _promotion_payload(rules: PromotionRules | None) -> dict[str, Any] | None:
    if rules is None:
        return None
    return {
        "minimum_total_trades": rules.minimum_total_trades,
        "minimum_win_rate": rules.minimum_win_rate,
        "minimum_total_return_pct": rules.minimum_total_return_pct,
        "maximum_drawdown_pct": rules.maximum_drawdown_pct,
        "minimum_sharpe_like_score": rules.minimum_sharpe_like_score,
    }


def _looks_like_config_text(text: str) -> bool:
    stripped = text.lstrip()
    return stripped.startswith("{") or stripped.startswith("[") or "\n" in text


def _workflow_config_from_mapping(mapping: Mapping[str, Any]) -> ResearchRunConfig:
    research_project_id = str(
        mapping.get("research_project_id") or mapping.get("project_id") or ""
    ).strip()
    dataset_snapshot_id = str(mapping.get("dataset_snapshot_id") or "").strip()
    if not research_project_id:
        raise ValueError("research_project_id is required")
    if not dataset_snapshot_id:
        raise ValueError("dataset_snapshot_id is required")
    strategy_grid_paths = _strategy_grid_paths(
        mapping.get("strategy_grids")
        or mapping.get("strategy_grid_paths")
        or mapping.get("strategy_grid")
    )
    if not strategy_grid_paths:
        raise ValueError("strategy_grids is required")
    return ResearchRunConfig(
        research_project_id=research_project_id,
        dataset_snapshot_id=dataset_snapshot_id,
        export_dir=str(mapping.get("export_dir", "reports/research")),
        strategy_grid_paths=strategy_grid_paths,
    )


def _strategy_grid_paths(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Mapping):
        path = value.get("path")
        return (str(path),) if path else ()
    if isinstance(value, list):
        return tuple(
            str(item.get("path") if isinstance(item, Mapping) else item).strip()
            for item in value
            if str(item.get("path") if isinstance(item, Mapping) else item).strip()
        )
    raise ValueError("strategy_grids must be a string, mapping, or list")
