from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import csv
import json
from pathlib import Path
from typing import Any

from project.research.config import ResearchConfig
from project.research.models import ParameterEvaluation


@dataclass(frozen=True)
class ResearchArtifactInput:
    config: ResearchConfig
    config_hash: str
    generated_at: str
    best_parameter_set_hash: str | None
    evaluations: tuple[ParameterEvaluation, ...]


@dataclass(frozen=True)
class ArtifactRecord:
    name: str
    path: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class ResearchArtifactManifest:
    config_hash: str
    generated_at: str
    strategy_family: str
    asset_symbol: str
    dataset_snapshot_id: str | None
    start_date: str
    end_date: str
    best_parameter_set_hash: str | None
    files: tuple[ArtifactRecord, ...]
    manifest_path: str


def write_research_artifacts(
    output_dir: Path,
    artifact_input: ResearchArtifactInput,
) -> ResearchArtifactManifest:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "parameter_grid_results.csv"
    md_path = output_dir / "parameter_grid_summary.md"
    manifest_path = output_dir / "manifest.json"
    _write_csv(csv_path, artifact_input.evaluations)
    _write_summary(md_path, artifact_input)
    files = (
        _record_file(csv_path),
        _record_file(md_path),
        *_write_plots(output_dir, artifact_input.evaluations),
    )
    manifest = ResearchArtifactManifest(
        config_hash=artifact_input.config_hash,
        generated_at=artifact_input.generated_at,
        strategy_family=artifact_input.config.strategy_family,
        asset_symbol=artifact_input.config.asset_symbol,
        dataset_snapshot_id=artifact_input.config.dataset_snapshot_id,
        start_date=artifact_input.config.start_date,
        end_date=artifact_input.config.end_date,
        best_parameter_set_hash=artifact_input.best_parameter_set_hash,
        files=files,
        manifest_path=str(manifest_path),
    )
    manifest_path.write_text(
        json.dumps(_manifest_payload(manifest), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return manifest


def _write_csv(path: Path, evaluations: tuple[ParameterEvaluation, ...]) -> None:
    fieldnames = [
        "parameter_set_id",
        "parameter_set_hash",
        "strategy_family",
        "trade_count",
        "winning_trades",
        "win_rate",
        "total_return_pct",
        "mean_return_pct",
        "median_return_pct",
        "volatility_pct",
        "max_drawdown_pct",
        "sharpe_like_score",
        "parameters_json",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for evaluation in sorted(evaluations, key=lambda item: item.parameter_set.parameter_set_hash):
            writer.writerow(_csv_row(evaluation))


def _csv_row(evaluation: ParameterEvaluation) -> dict[str, Any]:
    metrics = evaluation.metrics
    return {
        "parameter_set_id": evaluation.parameter_set.parameter_set_id,
        "parameter_set_hash": evaluation.parameter_set.parameter_set_hash,
        "strategy_family": evaluation.parameter_set.strategy_family,
        "trade_count": metrics.trade_count,
        "winning_trades": metrics.winning_trades,
        "win_rate": metrics.win_rate,
        "total_return_pct": metrics.total_return_pct,
        "mean_return_pct": metrics.mean_return_pct,
        "median_return_pct": metrics.median_return_pct,
        "volatility_pct": metrics.volatility_pct,
        "max_drawdown_pct": metrics.max_drawdown_pct,
        "sharpe_like_score": metrics.sharpe_like_score,
        "parameters_json": json.dumps(dict(evaluation.parameter_set.parameters), sort_keys=True),
    }


def _write_summary(path: Path, artifact_input: ResearchArtifactInput) -> None:
    lines = [
        f"# {artifact_input.config.strategy_family}",
        "",
        f"- asset_symbol: {artifact_input.config.asset_symbol}",
        f"- start_date: {artifact_input.config.start_date}",
        f"- end_date: {artifact_input.config.end_date}",
        f"- dataset_snapshot_id: {artifact_input.config.dataset_snapshot_id or 'n/a'}",
        f"- config_hash: {artifact_input.config_hash}",
        f"- best_parameter_set_hash: {artifact_input.best_parameter_set_hash or 'n/a'}",
        f"- evaluations: {len(artifact_input.evaluations)}",
        "",
        "| parameter_set_hash | trade_count | win_rate | total_return_pct | max_drawdown_pct | sharpe_like_score |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for evaluation in sorted(artifact_input.evaluations, key=_summary_sort_key, reverse=True):
        metrics = evaluation.metrics
        lines.append(
            "| "
            f"{evaluation.parameter_set.parameter_set_hash} | "
            f"{metrics.trade_count} | "
            f"{metrics.win_rate:.4f} | "
            f"{metrics.total_return_pct:.4f} | "
            f"{metrics.max_drawdown_pct:.4f} | "
            f"{metrics.sharpe_like_score:.4f} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_plots(
    output_dir: Path,
    evaluations: tuple[ParameterEvaluation, ...],
) -> tuple[ArtifactRecord, ...]:
    plt = _load_pyplot()
    if plt is None:
        return ()
    plotters = (
        ("equity_curve.png", _plot_equity_curve),
        ("drawdown_curve.png", _plot_drawdown_curve),
        ("parameter_comparison.png", _plot_parameter_comparison),
        ("trade_pnl_distribution.png", _plot_trade_distribution),
    )
    records: list[ArtifactRecord] = []
    for name, plotter in plotters:
        path = output_dir / name
        plotter(plt, path, evaluations)
        records.append(_record_file(path))
    return tuple(records)


def _load_pyplot() -> Any | None:
    try:
        import matplotlib  # type: ignore[import-not-found]

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt  # type: ignore[import-not-found]
    except Exception:
        return None
    return plt


def _plot_equity_curve(plt: Any, path: Path, evaluations: tuple[ParameterEvaluation, ...]) -> None:
    fig, ax = plt.subplots(figsize=(8, 4))
    best = _best_evaluation(evaluations)
    if best is None:
        ax.text(0.5, 0.5, "No evaluations available", ha="center", va="center")
    else:
        ax.plot(best.equity_curve_pct, color="#1f77b4", linewidth=2)
        ax.set_title(f"Equity Curve: {best.parameter_set.parameter_set_hash[:12]}")
    ax.set_xlabel("Trade")
    ax.set_ylabel("Cumulative Return %")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _plot_drawdown_curve(plt: Any, path: Path, evaluations: tuple[ParameterEvaluation, ...]) -> None:
    fig, ax = plt.subplots(figsize=(8, 4))
    best = _best_evaluation(evaluations)
    if best is None:
        ax.text(0.5, 0.5, "No evaluations available", ha="center", va="center")
    else:
        ax.plot(_drawdown_curve(best.equity_curve_pct), color="#d62728", linewidth=2)
        ax.set_title(f"Drawdown: {best.parameter_set.parameter_set_hash[:12]}")
    ax.set_xlabel("Trade")
    ax.set_ylabel("Drawdown %")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _plot_parameter_comparison(
    plt: Any,
    path: Path,
    evaluations: tuple[ParameterEvaluation, ...],
) -> None:
    fig, ax = plt.subplots(figsize=(8, 4))
    if not evaluations:
        ax.text(0.5, 0.5, "No evaluations available", ha="center", va="center")
    else:
        x_values = [item.metrics.max_drawdown_pct for item in evaluations]
        y_values = [item.metrics.total_return_pct for item in evaluations]
        colors = [item.metrics.sharpe_like_score for item in evaluations]
        scatter = ax.scatter(x_values, y_values, c=colors, cmap="viridis", s=50)
        fig.colorbar(scatter, ax=ax, label="Sharpe-like score")
        for evaluation in sorted(evaluations, key=lambda item: item.parameter_set.parameter_set_hash):
            ax.annotate(
                evaluation.parameter_set.parameter_set_hash[:8],
                (evaluation.metrics.max_drawdown_pct, evaluation.metrics.total_return_pct),
                fontsize=7,
                xytext=(4, 4),
                textcoords="offset points",
            )
    ax.set_xlabel("Max Drawdown %")
    ax.set_ylabel("Total Return %")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _plot_trade_distribution(
    plt: Any,
    path: Path,
    evaluations: tuple[ParameterEvaluation, ...],
) -> None:
    fig, ax = plt.subplots(figsize=(8, 4))
    returns = _trade_returns(evaluations)
    if not returns:
        ax.text(0.5, 0.5, "No trades available", ha="center", va="center")
    else:
        ax.hist(returns, bins=min(10, max(3, len(returns))), color="#2ca02c", edgecolor="white")
    ax.set_xlabel("Trade Return %")
    ax.set_ylabel("Count")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _best_evaluation(
    evaluations: tuple[ParameterEvaluation, ...],
) -> ParameterEvaluation | None:
    if not evaluations:
        return None
    return max(evaluations, key=_summary_sort_key)


def _drawdown_curve(equity_curve_pct: tuple[float, ...]) -> list[float]:
    peak = 0.0
    curve: list[float] = []
    for value in equity_curve_pct:
        peak = max(peak, value)
        curve.append(peak - value)
    return curve


def _trade_returns(evaluations: tuple[ParameterEvaluation, ...]) -> list[float]:
    return [value for evaluation in evaluations for value in evaluation.trade_returns_pct]


def _summary_sort_key(evaluation: ParameterEvaluation) -> tuple[float, float, str]:
    metrics = evaluation.metrics
    return (metrics.total_return_pct, metrics.sharpe_like_score, evaluation.parameter_set.parameter_set_hash)


def _record_file(path: Path) -> ArtifactRecord:
    data = path.read_bytes()
    return ArtifactRecord(
        name=path.name,
        path=str(path),
        sha256=sha256(data).hexdigest(),
        size_bytes=len(data),
    )


def _manifest_payload(manifest: ResearchArtifactManifest) -> dict[str, Any]:
    return {
        "config_hash": manifest.config_hash,
        "generated_at": manifest.generated_at,
        "strategy_family": manifest.strategy_family,
        "asset_symbol": manifest.asset_symbol,
        "dataset_snapshot_id": manifest.dataset_snapshot_id,
        "start_date": manifest.start_date,
        "end_date": manifest.end_date,
        "best_parameter_set_hash": manifest.best_parameter_set_hash,
        "files": [
            {
                "name": record.name,
                "path": record.path,
                "sha256": record.sha256,
                "size_bytes": record.size_bytes,
            }
            for record in manifest.files
        ],
    }
