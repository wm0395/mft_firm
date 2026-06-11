from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable, Iterable, Mapping

import pandas as pd

from research.notebooks.alpha_001.research.alpha101_engine import Alpha101Panel


AlphaBuilder = Callable[[Alpha101Panel], pd.DataFrame]


@dataclass(frozen=True)
class AlphaSpec:
    name: str
    family: str
    description: str
    builder: AlphaBuilder
    inputs: tuple[str, ...]
    horizons: tuple[int, ...]
    expression_modes: tuple[str, ...]
    default_cost_bps: float
    tags: tuple[str, ...]


@dataclass(frozen=True)
class AlphaRegistry:
    specs: tuple[AlphaSpec, ...]
    by_name: Mapping[str, AlphaSpec]


def alpha_spec(
    *,
    name: str,
    family: str,
    description: str,
    inputs: Iterable[str],
    horizons: Iterable[int] = (5,),
    expression_modes: Iterable[str] = ("cross_sectional_quintile",),
    default_cost_bps: float = 10.0,
    tags: Iterable[str] = (),
) -> Callable[[AlphaBuilder], AlphaSpec]:
    def decorate(builder: AlphaBuilder) -> AlphaSpec:
        return AlphaSpec(
            name=name,
            family=family,
            description=description,
            builder=builder,
            inputs=tuple(inputs),
            horizons=tuple(horizons),
            expression_modes=tuple(expression_modes),
            default_cost_bps=float(default_cost_bps),
            tags=tuple(tags),
        )

    return decorate


def build_alpha_registry(specs: Iterable[AlphaSpec]) -> AlphaRegistry:
    spec_tuple = tuple(specs)
    by_name = _specs_by_name(spec_tuple)
    return AlphaRegistry(specs=spec_tuple, by_name=MappingProxyType(by_name))


def get_alpha(registry: AlphaRegistry, name: str) -> AlphaSpec:
    try:
        return registry.by_name[name]
    except KeyError as exc:
        raise KeyError(f"unknown alpha spec: {name}") from exc


def _specs_by_name(specs: tuple[AlphaSpec, ...]) -> dict[str, AlphaSpec]:
    by_name: dict[str, AlphaSpec] = {}
    for spec in specs:
        if spec.name in by_name:
            raise ValueError(f"duplicate alpha spec: {spec.name}")
        by_name[spec.name] = spec
    return by_name
