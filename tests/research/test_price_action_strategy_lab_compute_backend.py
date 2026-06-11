from __future__ import annotations

import pandas as pd

from research.projects.price_action_strategy_lab.compute_backend import ComputeBackend
from research.projects.price_action_strategy_lab.compute_backend import GpuConfig
from research.projects.price_action_strategy_lab.compute_backend import build_rank_pct
from research.projects.price_action_strategy_lab.compute_backend import resolve_compute_backend


def test_resolve_compute_backend_defaults_to_cpu() -> None:
    backend = resolve_compute_backend(GpuConfig(enabled=False))

    assert backend == ComputeBackend(name="cpu", is_gpu=False, reason=None)


def test_build_rank_pct_matches_pandas_rank_on_cpu() -> None:
    signal = pd.DataFrame(
        [[1.0, 1.0, 3.0, None], [4.0, 2.0, 2.0, 1.0]],
        columns=list("abcd"),
    )
    backend = ComputeBackend(name="cpu", is_gpu=False)

    result = build_rank_pct(signal, backend)

    expected = signal.rank(axis=1, pct=True, method="average")
    pd.testing.assert_frame_equal(result, expected)
