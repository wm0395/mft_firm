from __future__ import annotations

from argparse import Namespace
from dataclasses import asdict, is_dataclass
from pathlib import Path
import json
from typing import Any, cast

from project.cli_support import emit_error, emit_response
from project.data.repository import DataRepository
from project.research.config import load_research_config, load_research_run_config
from project.research.runner import run_research_batch


def create_research_project(repository: DataRepository, args: Namespace) -> int:
    kwargs = _research_project_kwargs(args)
    if not _has_name(args):
        emit_error("create-research-project", "missing required research project name")
        return 1
    return _emit_repository_result(
        repository,
        "create-research-project",
        "create_research_project",
        name=getattr(args, "name", None),
        description=getattr(args, "description", ""),
        **kwargs,
    )


def list_research_projects(repository: DataRepository) -> int:
    return _emit_repository_result(
        repository,
        "list-research-projects",
        "list_research_projects",
    )


def show_research_project(repository: DataRepository, args: Namespace) -> int:
    project_id = _resolve_identifier(
        getattr(args, "research_project_id", None),
        getattr(args, "project_id", None),
    )
    if project_id is None:
        emit_error("show-research-project", "missing research project identifier")
        return 1
    return _emit_repository_result(
        repository,
        "show-research-project",
        "show_research_project",
        research_project_id=project_id,
    )


def run_parameter_research(repository: DataRepository, args: Namespace) -> int:
    if _has_workflow_inputs(args):
        try:
            return _run_parameter_research_workflow(repository, args)
        except Exception as error:
            emit_error("run-parameter-research", error)
            return 1
    project_id = _resolve_identifier(
        getattr(args, "research_project_id", None),
        getattr(args, "project_id", None),
    )
    try:
        parameters = _parse_parameters(
            getattr(args, "parameters_json", None),
            getattr(args, "parameter", []),
        )
    except Exception as error:
        emit_error("run-parameter-research", error)
        return 1
    kwargs: dict[str, Any] = {"parameters": parameters}
    if project_id is not None:
        kwargs["research_project_id"] = project_id
    if getattr(args, "hypothesis_id", None) is not None:
        kwargs["hypothesis_id"] = args.hypothesis_id
    if getattr(args, "dataset_snapshot_id", None) is not None:
        kwargs["dataset_snapshot_id"] = args.dataset_snapshot_id
    kwargs["include_testing"] = bool(getattr(args, "include_testing", False))
    kwargs["include_draft"] = bool(getattr(args, "include_draft", False))
    return _emit_repository_result(
        repository,
        "run-parameter-research",
        "run_parameter_research",
        **kwargs,
    )


def list_research_runs(repository: DataRepository, args: Namespace) -> int:
    kwargs: dict[str, Any] = {}
    project_id = _resolve_identifier(
        getattr(args, "research_project_id", None),
        getattr(args, "project_id", None),
    )
    if project_id is not None:
        kwargs["research_project_id"] = project_id
    return _emit_repository_result(
        repository,
        "list-research-runs",
        "list_research_runs",
        **kwargs,
    )


def show_research_run(repository: DataRepository, args: Namespace) -> int:
    research_run_id = _resolve_identifier(
        getattr(args, "research_run_id", None),
        getattr(args, "run_id", None),
    )
    if research_run_id is None:
        emit_error("show-research-run", "missing research run identifier")
        return 1
    return _emit_repository_result(
        repository,
        "show-research-run",
        "show_research_run",
        research_run_id=research_run_id,
    )


def compare_research_runs(repository: DataRepository, args: Namespace) -> int:
    research_run_ids = _combine_run_ids(
        getattr(args, "research_run_ids", []),
        getattr(args, "research_run_id", []),
    )
    if len(research_run_ids) < 2:
        emit_error(
            "compare-research-runs",
            "compare-research-runs requires at least two research run identifiers",
        )
        return 1
    return _emit_repository_result(
        repository,
        "compare-research-runs",
        "compare_research_runs",
        research_run_ids=research_run_ids,
    )


def export_research_pack(repository: DataRepository, args: Namespace) -> int:
    project_id = _resolve_identifier(
        getattr(args, "research_project_id", None),
        getattr(args, "project_id", None),
    )
    if project_id is None:
        emit_error("export-research-pack", "missing research project identifier")
        return 1
    kwargs: dict[str, Any] = {"research_project_id": project_id}
    if getattr(args, "output_dir", None) is not None:
        kwargs["output_dir"] = args.output_dir
    return _emit_repository_result(
        repository,
        "export-research-pack",
        "export_research_pack",
        **kwargs,
    )


def promote_strategy_candidate(repository: DataRepository, args: Namespace) -> int:
    candidate_id = _resolve_identifier(
        getattr(args, "strategy_candidate_id", None),
        getattr(args, "candidate_id", None),
    )
    if candidate_id is None:
        emit_error(
            "promote-strategy-candidate", "missing strategy candidate identifier"
        )
        return 1
    return _emit_repository_result(
        repository,
        "promote-strategy-candidate",
        "promote_strategy_candidate",
        strategy_candidate_id=candidate_id,
        to_status=getattr(args, "to", None),
        force=bool(getattr(args, "force", False)),
    )


def _emit_repository_result(
    repository: DataRepository,
    command: str,
    method_name: str,
    **kwargs: Any,
) -> int:
    method = getattr(repository, method_name, None)
    if not callable(method):
        emit_error(command, f"{method_name} API is unavailable")
        return 1
    try:
        result = method(**kwargs)
    except Exception as error:
        emit_error(command, error)
        return 1
    emit_response(command, _json_safe(result))
    return 0


def _json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return {
            key: _json_safe(item)
            for key, item in asdict(cast(Any, value)).items()
        }
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def _parse_parameters(parameters_json: str | None, parameter_values: list[str]) -> dict[str, Any]:
    parameters: dict[str, Any] = {}
    if parameters_json:
        loaded = json.loads(parameters_json)
        if not isinstance(loaded, dict):
            raise ValueError("--parameters-json must decode to an object")
        parameters.update(loaded)
    for item in parameter_values:
        key, value = _split_parameter(item)
        parameters[key] = value
    return parameters


def _split_parameter(item: str) -> tuple[str, str]:
    if "=" not in item:
        raise ValueError("--parameter values must use key=value format")
    key, value = item.split("=", 1)
    if not key:
        raise ValueError("--parameter keys must not be empty")
    return key, value


def _combine_run_ids(
    positional_ids: list[str],
    flag_ids: list[str] | None,
) -> tuple[str, ...]:
    combined = [*positional_ids, *(flag_ids or [])]
    return tuple(combined)


def _resolve_identifier(*values: str | None) -> str | None:
    for value in values:
        if value is not None:
            return value
    return None


def _has_workflow_inputs(args: Namespace) -> bool:
    return bool(getattr(args, "research_run_config", None) or getattr(args, "strategy_grid", []))


def _run_parameter_research_workflow(repository: DataRepository, args: Namespace) -> int:
    workflow_config = _load_workflow_config(args)
    project_id = _resolve_identifier(
        getattr(args, "research_project_id", None),
        getattr(args, "project_id", None),
        workflow_config.research_project_id if workflow_config else None,
    )
    dataset_snapshot_id = _resolve_identifier(
        getattr(args, "dataset_snapshot_id", None),
        workflow_config.dataset_snapshot_id if workflow_config else None,
    )
    if project_id is None:
        raise ValueError("missing research project identifier")
    if dataset_snapshot_id is None:
        raise ValueError("missing dataset snapshot identifier")
    grid_paths = _strategy_grid_paths(args, workflow_config)
    if not grid_paths:
        raise ValueError("at least one strategy grid is required")
    export_root = Path(
        getattr(args, "export_dir", None)
        or (workflow_config.export_dir if workflow_config else "reports/research")
    )
    configs = tuple(
        _load_strategy_grid(path, dataset_snapshot_id) for path in grid_paths
    )
    batch = run_research_batch(repository, configs, export_root / project_id)
    runs = [
        {
            "research_run_id": Path(result.artifact_manifest.manifest_path).parent.name,
            "strategy_family": result.config.strategy_family,
            "config_hash": result.config_hash,
            "output_dir": str(Path(result.artifact_manifest.manifest_path).parent),
            "manifest_path": result.artifact_manifest.manifest_path,
            "best_parameter_set_hash": result.best_evaluation.parameter_set.parameter_set_hash if result.best_evaluation else None,
        }
        for result in batch.results
    ]
    emit_response(
        "run-parameter-research",
        {
            "research_project_id": project_id,
            "dataset_snapshot_id": dataset_snapshot_id,
            "export_root": str(batch.output_dir),
            "strategy_grid_count": len(configs),
            "runs": runs,
        },
    )
    return 0


def _load_workflow_config(args: Namespace):
    workflow_path = getattr(args, "research_run_config", None)
    if workflow_path is None:
        return None
    return load_research_run_config(Path(workflow_path))


def _strategy_grid_paths(args: Namespace, workflow_config: Any | None) -> tuple[Path, ...]:
    if workflow_config is not None:
        base = Path(getattr(args, "research_run_config")).resolve().parent
        return tuple((base / path).resolve() for path in workflow_config.strategy_grid_paths)
    return tuple(Path(path).resolve() for path in getattr(args, "strategy_grid", []))


def _load_strategy_grid(path: Path, dataset_snapshot_id: str):
    config = load_research_config(path)
    from dataclasses import replace

    return replace(config, dataset_snapshot_id=dataset_snapshot_id)


def _research_project_kwargs(args: Namespace) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    project_id = _resolve_identifier(
        getattr(args, "research_project_id", None),
        getattr(args, "project_id", None),
    )
    if project_id is not None:
        kwargs["research_project_id"] = project_id
    if getattr(args, "dataset_snapshot_id", None) is not None:
        kwargs["dataset_snapshot_id"] = args.dataset_snapshot_id
    return kwargs


def _has_name(args: Namespace) -> bool:
    return getattr(args, "name", None) is not None
