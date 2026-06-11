from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable, Iterable, Mapping

import pandas as pd

from research.notebooks.alpha_001.research.alpha101_engine import Alpha101Panel

ActivatorBuilder = Callable[[Alpha101Panel], pd.DataFrame]


@dataclass(frozen=True)
class ActivatorSpec:
    name: str
    family: str
    description: str
    builder: ActivatorBuilder
    tags: tuple[str, ...]


@dataclass(frozen=True)
class ActivatorRegistry:
    specs: tuple[ActivatorSpec, ...]
    by_name: Mapping[str, ActivatorSpec]


def activator_spec(
    *,
    name: str,
    family: str,
    description: str,
    tags: Iterable[str] = (),
) -> Callable[[ActivatorBuilder], ActivatorSpec]:
    def decorate(builder: ActivatorBuilder) -> ActivatorSpec:
        return ActivatorSpec(
            name=name,
            family=family,
            description=description,
            builder=builder,
            tags=tuple(tags),
        )

    return decorate


def build_activator_registry(specs: Iterable[ActivatorSpec]) -> ActivatorRegistry:
    spec_tuple = tuple(specs)
    by_name = _specs_by_name(spec_tuple)
    return ActivatorRegistry(specs=spec_tuple, by_name=MappingProxyType(by_name))


def get_activator(registry: ActivatorRegistry, name: str) -> ActivatorSpec:
    try:
        return registry.by_name[name]
    except KeyError as exc:
        raise KeyError(f"unknown activator spec: {name}") from exc


def _specs_by_name(specs: tuple[ActivatorSpec, ...]) -> dict[str, ActivatorSpec]:
    by_name: dict[str, ActivatorSpec] = {}
    for spec in specs:
        if spec.name in by_name:
            raise ValueError(f"duplicate activator spec: {spec.name}")
        by_name[spec.name] = spec
    return by_name
