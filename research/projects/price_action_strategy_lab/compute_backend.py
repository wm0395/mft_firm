from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class GpuConfig:
    enabled: bool = False
    backend: str = "auto"


@dataclass(frozen=True)
class ComputeBackend:
    name: str
    is_gpu: bool
    reason: str | None = None


def resolve_compute_backend(config: GpuConfig) -> ComputeBackend:
    if not config.enabled or config.backend == "cpu":
        return ComputeBackend(name="cpu", is_gpu=False)
    if config.backend not in {"auto", "cupy"}:
        raise ValueError(f"unsupported gpu backend: {config.backend}")
    if importlib.util.find_spec("cupy") is None:
        return ComputeBackend(
            name="cpu_fallback_no_cupy",
            is_gpu=False,
            reason="cupy is not installed",
        )
    return ComputeBackend(name="cupy", is_gpu=True)


def build_rank_pct(signal: pd.DataFrame, backend: ComputeBackend) -> pd.DataFrame:
    if not backend.is_gpu:
        return signal.rank(axis=1, pct=True, method="average")
    try:
        import cupy as cp  # type: ignore[import-not-found]
    except ImportError:
        return signal.rank(axis=1, pct=True, method="average")
    return _build_rank_pct_gpu(signal, cp)


def _build_rank_pct_gpu(signal: pd.DataFrame, xp: Any) -> pd.DataFrame:
    values = xp.asarray(signal.to_numpy(dtype=float))
    ranked = xp.full(values.shape, xp.nan, dtype=float)
    for row_index in range(values.shape[0]):
        ranked[row_index] = _rank_row_average(values[row_index], xp)
    array = xp.asnumpy(ranked) if hasattr(xp, "asnumpy") else np.asarray(ranked)
    return pd.DataFrame(array, index=signal.index, columns=signal.columns)


def _rank_row_average(row: Any, xp: Any) -> Any:
    valid = ~xp.isnan(row)
    count = int(valid.sum().item())
    ranked = xp.full(row.shape, xp.nan, dtype=float)
    if count == 0:
        return ranked
    values = row[valid]
    order = xp.argsort(values)
    sorted_values = values[order]
    positions = xp.nonzero(valid)[0][order]
    start = 0
    while start < count:
        end = start + 1
        first = float(sorted_values[start].item())
        while end < count and float(sorted_values[end].item()) == first:
            end += 1
        ranked[positions[start:end]] = (start + 1 + end) / (2.0 * count)
        start = end
    return ranked
