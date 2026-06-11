from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from research.projects.price_action_strategy_lab.activator_specs import default_activator_registry
from research.projects.price_action_strategy_lab.alpha_specs import default_alpha_registry
from research.projects.price_action_strategy_lab.compute_backend import GpuConfig
from research.projects.price_action_strategy_lab.narrow_falsification import NarrowHypothesis
from research.projects.price_action_strategy_lab.run_activator_suite import _load_panel
from research.projects.price_action_strategy_lab.run_activator_suite import _read_config
from research.projects.price_action_strategy_lab.stress_confirmation import StressConfirmationConfig
from research.projects.price_action_strategy_lab.stress_confirmation import StressVariant
from research.projects.price_action_strategy_lab.stress_confirmation import run_stress_confirmation
from research.projects.price_action_strategy_lab.universe_adapter import to_alpha101_panel


@dataclass(frozen=True)
class StressConfirmationRunResult:
    report_dir: Path


def run_stress_confirmation_config(config_path: str | Path) -> StressConfirmationRunResult:
    raw = _read_config(Path(config_path))
    panel = to_alpha101_panel(_load_panel(raw))
    result = run_stress_confirmation(
        panel,
        default_alpha_registry(),
        default_activator_registry(),
        _config(raw),
    )
    return StressConfirmationRunResult(result.report_dir)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    args = parser.parse_args(argv)
    result = run_stress_confirmation_config(args.config)
    print(f"wrote stress confirmation reports to {result.report_dir}")
    return 0


def _config(raw: dict[str, Any]) -> StressConfirmationConfig:
    compute = dict(raw.get("compute", {}))
    backtests = dict(raw.get("backtests", {}))
    walk = dict(raw.get("walk_forward_validation", {}))
    gpu = dict(raw.get("gpu", {}))
    return StressConfirmationConfig(
        variants=tuple(_variant(item) for item in raw.get("variants", ())),
        cache_dir=Path(str(compute.get("cache_dir"))),
        report_root=Path(str(compute.get("report_root"))),
        source_report_dir=Path(str(compute.get("source_report_dir"))),
        mode=str(backtests.get("mode", "ranked_long_only")),
        horizon=int(backtests.get("horizon", 10)),
        cost_bps=tuple(float(item) for item in backtests.get("cost_bps", (10.0, 25.0, 50.0, 75.0))),
        train_size_days=int(walk.get("train_size_days", 126)),
        test_size_days=int(walk.get("test_size_days", 21)),
        step_size_days=int(walk.get("step_size_days", 21)),
        lookahead_days=int(walk.get("lookahead_days", 10)),
        max_folds=int(walk.get("max_folds", 24)),
        top_quantile=float(backtests.get("top_quantile", 0.8)),
        min_names=int(backtests.get("min_active_names", 20)),
        max_workers=int(compute.get("max_workers") or 1),
        gpu=GpuConfig(enabled=bool(gpu.get("enabled", False)), backend=str(gpu.get("backend") or "auto")),
    )


def _variant(item: dict[str, Any]) -> StressVariant:
    variant_id = str(item["variant_id"])
    hypothesis = NarrowHypothesis(
        hypothesis_id=variant_id,
        alphas=(str(item.get("alpha", "support_trendline_position_20")),),
        indicator=str(item.get("indicator", "stress_confirmation")),
        side="high",
        throttle_variant=str(item.get("throttle_variant", "soft_aggressive")),
        threshold_quantiles=tuple(float(value) for value in item.get("allowed_threshold_grid", (0.5, 0.6, 0.7, 0.8))),
        multiplier_grid=tuple(dict(row) for row in item.get("allowed_multiplier_grid", ({"down": 0.25, "up": 1.25},))),
    )
    return StressVariant(variant_id, tuple(str(value) for value in item.get("indicators", ())), str(item.get("combine", "single")), hypothesis)


if __name__ == "__main__":
    raise SystemExit(main())
