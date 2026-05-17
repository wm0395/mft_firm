from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from project.data.repository import DataRepository
from project.research.artifacts import (
    ResearchArtifactInput,
    ResearchArtifactManifest,
    write_research_artifacts,
)
from project.research.config import ResearchConfig, research_config_hash
from project.research.models import ParameterEvaluation, WorkbenchSeries
from project.research.parameter_grid import expand_parameter_sets
from project.research.promotion import PromotionValidation, candidate_from_evaluation, validate_promotion
from project.research.strategies import simulate_parameter_set
from project.research.workbench import load_workbench_series, load_workbench_series_for_snapshot


@dataclass(frozen=True)
class ResearchRunRequest:
    config: ResearchConfig
    output_dir: Path


@dataclass(frozen=True)
class ResearchRunResult:
    config: ResearchConfig
    config_hash: str
    generated_at: str
    workbench: WorkbenchSeries
    evaluations: tuple[ParameterEvaluation, ...]
    best_evaluation: ParameterEvaluation | None
    artifact_manifest: ResearchArtifactManifest
    promotion_validation: PromotionValidation | None


@dataclass(frozen=True)
class ResearchBatchResult:
    output_dir: Path
    results: tuple[ResearchRunResult, ...]


@dataclass(frozen=True)
class ResearchService:
    repository: DataRepository
    output_dir: Path

    def run(self, request: ResearchRunRequest) -> ResearchRunResult:
        series = self._series(request.config)
        evaluations = tuple(
            simulate_parameter_set(request.config, series, parameter_set)
            for parameter_set in expand_parameter_sets(
                request.config.strategy_family,
                request.config.parameter_axes,
            )
        )
        best = _best_evaluation(evaluations)
        generated_at = _generated_at()
        config_hash = research_config_hash(request.config)
        artifact_manifest = write_research_artifacts(
            request.output_dir,
            ResearchArtifactInput(
                config=request.config,
                config_hash=config_hash,
                generated_at=generated_at,
                best_parameter_set_hash=best.parameter_set.parameter_set_hash if best else None,
                evaluations=evaluations,
            ),
        )
        promotion_validation = self._promotion_validation(request.config, best)
        return ResearchRunResult(
            config=request.config,
            config_hash=config_hash,
            generated_at=generated_at,
            workbench=series,
            evaluations=evaluations,
            best_evaluation=best,
            artifact_manifest=artifact_manifest,
            promotion_validation=promotion_validation,
        )

    def _series(self, config: ResearchConfig) -> WorkbenchSeries:
        if config.dataset_snapshot_id:
            return load_workbench_series_for_snapshot(
                self.repository,
                config.dataset_snapshot_id,
                config.asset_symbol,
            )
        return load_workbench_series(
            self.repository,
            config.asset_symbol,
            config.start_date,
            config.end_date,
        )

    def _promotion_validation(
        self,
        config: ResearchConfig,
        best: ParameterEvaluation | None,
    ) -> PromotionValidation | None:
        if config.promotion_rules is None:
            return None
        candidate = candidate_from_evaluation(config.strategy_family, best) if best else None
        return validate_promotion(candidate, config.promotion_rules)


def run_research(
    repository: DataRepository,
    config_or_request: ResearchConfig | ResearchRunRequest,
    output_dir: Path | None = None,
) -> ResearchRunResult:
    request = _request(config_or_request, output_dir)
    service = ResearchService(repository=repository, output_dir=request.output_dir)
    return service.run(request)


def run_research_batch(
    repository: DataRepository,
    configs: tuple[ResearchConfig, ...],
    output_dir: Path,
) -> ResearchBatchResult:
    results = tuple(
        run_research(repository, config, output_dir / _run_directory_name(config))
        for config in configs
    )
    return ResearchBatchResult(output_dir=output_dir, results=results)


def _request(
    config_or_request: ResearchConfig | ResearchRunRequest,
    output_dir: Path | None,
) -> ResearchRunRequest:
    if isinstance(config_or_request, ResearchRunRequest):
        return config_or_request
    if output_dir is None:
        raise ValueError("output_dir is required when passing a ResearchConfig")
    return ResearchRunRequest(config=config_or_request, output_dir=Path(output_dir))


def _best_evaluation(
    evaluations: tuple[ParameterEvaluation, ...],
) -> ParameterEvaluation | None:
    if not evaluations:
        return None
    return max(evaluations, key=_evaluation_key)


def _evaluation_key(evaluation: ParameterEvaluation) -> tuple[float, float, float, float, str]:
    metrics = evaluation.metrics
    return (
        metrics.total_return_pct,
        metrics.sharpe_like_score,
        metrics.win_rate,
        -metrics.max_drawdown_pct,
        evaluation.parameter_set.parameter_set_hash,
    )


def _generated_at() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _run_directory_name(config: ResearchConfig) -> str:
    return f"{config.strategy_family}:{research_config_hash(config)[:12]}"
