from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from itertools import product
import json
from typing import Any, Mapping

from project.research.models import ParameterAxis, ParameterSet, ResearchFamily


CANONICAL_PARAMETER_GRIDS: dict[ResearchFamily, tuple[ParameterAxis, ...]] = {
    "momentum_continuation": (
        ParameterAxis("lookback_bars", (3, 5, 10)),
        ParameterAxis("entry_threshold", (0.005, 0.01)),
        ParameterAxis("exit_threshold", (0.0, 0.0025)),
        ParameterAxis("holding_bars", (2, 4)),
    ),
    "mean_reversion": (
        ParameterAxis("lookback_bars", (5, 10, 20)),
        ParameterAxis("entry_zscore", (0.75, 1.25)),
        ParameterAxis("exit_zscore", (0.25, 0.5)),
        ParameterAxis("holding_bars", (2, 4)),
    ),
}


def canonical_parameter_grid(strategy_family: ResearchFamily) -> tuple[ParameterAxis, ...]:
    try:
        return CANONICAL_PARAMETER_GRIDS[strategy_family]
    except KeyError as error:
        raise ValueError(f"unsupported strategy family: {strategy_family}") from error


def expand_parameter_sets(
    strategy_family: ResearchFamily,
    axes: tuple[ParameterAxis, ...] | None = None,
) -> tuple[ParameterSet, ...]:
    grid_axes = axes or canonical_parameter_grid(strategy_family)
    parameter_sets: list[ParameterSet] = []
    for values in product(*(axis.values for axis in grid_axes)):
        parameters = tuple(sorted((axis.name, value) for axis, value in zip(grid_axes, values, strict=True)))
        parameter_sets.append(_build_parameter_set(strategy_family, parameters))
    return tuple(parameter_sets)


def parameter_set_hash(strategy_family: ResearchFamily, parameters: Mapping[str, Any] | tuple[tuple[str, Any], ...]) -> str:
    normalized = _normalized_parameters(parameters)
    payload = json.dumps(
        {"strategy_family": strategy_family, "parameters": normalized},
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(payload.encode("utf-8")).hexdigest()


def parameter_grid_hash(
    strategy_family: ResearchFamily,
    axes: tuple[ParameterAxis, ...] | None = None,
) -> str:
    grid_axes = axes or canonical_parameter_grid(strategy_family)
    payload = json.dumps(
        {
            "strategy_family": strategy_family,
            "parameter_grid": [
                {"name": axis.name, "values": [_canonical_value(value) for value in axis.values]}
                for axis in grid_axes
            ],
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(payload.encode("utf-8")).hexdigest()


def parameter_axes_from_mapping(
    strategy_family: ResearchFamily,
    mapping: Mapping[str, Any],
) -> tuple[ParameterAxis, ...]:
    canonical_axes = canonical_parameter_grid(strategy_family)
    unknown = sorted(key for key in mapping if key not in {axis.name for axis in canonical_axes})
    if unknown:
        raise ValueError("unknown parameter grid axes: " + ", ".join(unknown))
    return tuple(replace(axis, values=_axis_values(axis.name, mapping, axis.values)) for axis in canonical_axes)


def _build_parameter_set(
    strategy_family: ResearchFamily,
    parameters: tuple[tuple[str, Any], ...],
) -> ParameterSet:
    digest = parameter_set_hash(strategy_family, parameters)
    return ParameterSet(
        strategy_family=strategy_family,
        parameters=parameters,
        parameter_set_hash=digest,
        parameter_set_id=f"research_parameter_set:{strategy_family}:{digest[:16]}",
    )


def _axis_values(
    axis_name: str,
    mapping: Mapping[str, Any],
    default_values: tuple[Any, ...],
) -> tuple[Any, ...]:
    values = mapping.get(axis_name, default_values)
    if isinstance(values, tuple):
        return values
    if isinstance(values, list):
        return tuple(values)
    if isinstance(values, set):
        return tuple(sorted(values))
    return tuple(default_values)


def _normalized_parameters(
    parameters: Mapping[str, Any] | tuple[tuple[str, Any], ...],
) -> list[list[Any]]:
    items = parameters.items() if isinstance(parameters, Mapping) else parameters
    return [[name, _canonical_value(value)] for name, value in sorted(items)]


def _canonical_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _canonical_value(item) for key, item in sorted(value.items())}
    if isinstance(value, tuple):
        return [_canonical_value(item) for item in value]
    if isinstance(value, list):
        return [_canonical_value(item) for item in value]
    return value
