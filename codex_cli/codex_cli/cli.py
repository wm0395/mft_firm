from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from .launch_policy import default_execution_target, default_review_target

if TYPE_CHECKING:
    from .memory_store import MemoryStore
    from .paths import ProjectPaths
    from .scratchpad import ScratchpadStore
    from .tasks import TaskStore

DEFAULT_CONSTRAINTS = (
    "No upward imports",
    "No layer skipping",
    "No DB access outside project/data/",
)
DEFAULT_DONE_CONDITIONS = (
    "pytest passes",
    "ruff passes",
    "typing passes",
    "no architecture violations",
)
DEFAULT_REQUIRED_REVIEWERS = (
    "architecture_reviewer",
    "complexity_reviewer",
    "determinism_auditor",
    "financial_logic_auditor",
    "test_failure_reviewer",
)
DEFAULT_EXEC_BUDGET = 1200
DEFAULT_REVIEW_BUDGET = 900
LAUNCH_PROVIDERS = ("codex", "opencode")
INTERACTIVE = "interactive"
ONESHOT = "oneshot"


def _architecture_tools():
    from .architecture import check_architecture, detect_drift, self_heal

    return check_architecture, detect_drift, self_heal


def _cache_tools():
    from .cache import build_index, cache_status, retrieve_context

    return build_index, cache_status, retrieve_context


def _launcher_tools():
    from .launcher import build_launch_command, launch_task

    return build_launch_command, launch_task


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ai_code")
    subcommands = parser.add_subparsers(dest="command", required=True)
    _add_task_parser(subcommands, "run", "Create task, context, packets, and summary")
    _add_task_parser(subcommands, "plan", "Create a planning artifact")
    exec_parser = subcommands.add_parser("exec", help="Build execution packet for a task")
    exec_parser.add_argument("task_id")
    exec_parser.add_argument("--provider", choices=("codex", "gemini", "opencode"))
    exec_parser.add_argument("--budget", type=int, default=DEFAULT_EXEC_BUDGET)
    execute_parser = subcommands.add_parser("execute", help="Launch a task in Codex CLI or OpenCode")
    execute_parser.add_argument("task_id")
    execute_parser.add_argument("--provider", choices=LAUNCH_PROVIDERS)
    execute_parser.add_argument("--mode", choices=(INTERACTIVE, ONESHOT), default=INTERACTIVE)
    execute_parser.add_argument("--budget", type=int, default=DEFAULT_EXEC_BUDGET)
    execute_parser.add_argument("--json", action="store_true")
    execute_parser.add_argument("--model")
    execute_parser.add_argument("--dry-run", action="store_true")
    run_task_parser = subcommands.add_parser("run-task", help="Run a task through the managed oneshot workflow")
    run_task_parser.add_argument("task_id")
    run_task_parser.add_argument("--provider", choices=LAUNCH_PROVIDERS)
    run_task_parser.add_argument("--budget", type=int, default=DEFAULT_EXEC_BUDGET)
    run_task_parser.add_argument("--json", action="store_true")
    run_task_parser.add_argument("--model")
    run_task_parser.add_argument("--resume", action="store_true")
    run_task_parser.add_argument("--no-review", action="store_true")
    run_task_parser.add_argument("--no-checks", action="store_true")
    run_task_parser.add_argument("--dry-run", action="store_true")
    run_fix_parser = subcommands.add_parser("run-fix", help="Re-run implementation for a task after review changes are requested")
    run_fix_parser.add_argument("task_id")
    run_fix_parser.add_argument("--provider", choices=LAUNCH_PROVIDERS)
    run_fix_parser.add_argument("--budget", type=int, default=DEFAULT_EXEC_BUDGET)
    run_fix_parser.add_argument("--json", action="store_true")
    run_fix_parser.add_argument("--model")
    run_fix_parser.add_argument("--no-review", action="store_true")
    run_fix_parser.add_argument("--no-checks", action="store_true")
    run_fix_parser.add_argument("--dry-run", action="store_true")
    run_review_parser = subcommands.add_parser("run-review", help="Run the review step for an implemented or fix-ready task")
    run_review_parser.add_argument("task_id")
    run_review_parser.add_argument("--provider", choices=LAUNCH_PROVIDERS)
    run_review_parser.add_argument("--budget", type=int, default=DEFAULT_REVIEW_BUDGET)
    run_review_parser.add_argument("--json", action="store_true")
    run_review_parser.add_argument("--model")
    run_review_parser.add_argument("--persona")
    queue_parser = subcommands.add_parser("run-queue", help="Run active tasks sequentially with OpenCode rate-limit handling")
    queue_parser.add_argument("--provider", choices=LAUNCH_PROVIDERS)
    queue_parser.add_argument("--budget", type=int, default=DEFAULT_EXEC_BUDGET)
    queue_parser.add_argument("--json", action="store_true")
    queue_parser.add_argument("--model")
    queue_parser.add_argument("--resume", action="store_true")
    queue_parser.add_argument("--no-review", action="store_true")
    queue_parser.add_argument("--no-checks", action="store_true")
    queue_parser.add_argument("--cooldown-hours", type=float, default=5.0)
    review_parser = subcommands.add_parser("review", help="Build review packet for a task")
    review_parser.add_argument("task_id")
    review_parser.add_argument("--provider", choices=("codex", "gemini", "opencode"))
    review_parser.add_argument("--persona")
    review_parser.add_argument("--budget", type=int, default=DEFAULT_REVIEW_BUDGET)
    scratch_parser = subcommands.add_parser("scratch", help="Show or create a task scratchpad")
    scratch_parser.add_argument("task_id")
    complete_parser = subcommands.add_parser("complete", help="Mark a task completed")
    complete_parser.add_argument("task_id")
    diagnose_parser = subcommands.add_parser("diagnose", help="Diagnose a task architecture violation")
    diagnose_parser.add_argument("task_id")
    fix_parser = subcommands.add_parser("fix", help="Build an architecture-only fix prompt")
    fix_parser.add_argument("task_id")
    heal_parser = subcommands.add_parser("heal", help="Run the explicit self-healing loop for a task")
    heal_parser.add_argument("task_id")
    check_parser = subcommands.add_parser("check", help="Run enforcement checks")
    check_subcommands = check_parser.add_subparsers(dest="check_command", required=True)
    check_subcommands.add_parser("architecture", help="Run layer-lint and architecture tests")
    check_subcommands.add_parser("drift", help="Detect architecture prompt and memory drift")
    cache_parser = subcommands.add_parser("cache", help="Manage index and token caches")
    cache_subcommands = cache_parser.add_subparsers(dest="cache_command", required=True)
    cache_subcommands.add_parser("build", help="Build local index and token cache metadata")
    cache_subcommands.add_parser("status", help="Show cache status")
    subcommands.add_parser("list", help="List active tasks")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    from .memory_store import MemoryStore
    from .paths import ProjectPaths
    from .scratchpad import ScratchpadStore
    from .tasks import TaskStore

    paths = ProjectPaths()
    tasks = TaskStore(paths)
    scratchpads = ScratchpadStore(paths)
    memory = MemoryStore(paths)
    try:
        return _dispatch(args, paths, tasks, scratchpads, memory)
    except FileNotFoundError as error:
        print(str(error), file=sys.stderr)
        return 1
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2


def _dispatch(args, paths: ProjectPaths, tasks: TaskStore, scratchpads: ScratchpadStore, memory: MemoryStore) -> int:
    from .diagnosis import build_fix_prompt, diagnose_task

    if args.command in {"run", "plan"}:
        return _run_or_plan(args, paths, tasks, scratchpads, memory)
    if args.command == "exec":
        return _print_json({"status": "ready", "execution": _execution_payload(args, tasks, scratchpads, paths)})
    if args.command == "execute":
        return _execute_command(args, paths, tasks, scratchpads)
    if args.command == "run-task":
        return _run_task(args, paths, tasks, scratchpads, memory)
    if args.command == "run-fix":
        return _run_fix(args, paths, tasks, scratchpads, memory)
    if args.command == "run-review":
        return _run_review(args, paths, tasks, scratchpads, memory)
    if args.command == "run-queue":
        return _run_queue(args, paths, tasks, scratchpads, memory)
    if args.command == "review":
        return _print_json({"status": "ready", "review": _review_payload(args, tasks, scratchpads, paths)})
    if args.command == "scratch":
        return _print_scratch(args.task_id, tasks, scratchpads)
    if args.command == "complete":
        return _complete_task(args.task_id, tasks, scratchpads)
    if args.command == "check":
        return _check_command(args, paths)
    if args.command == "diagnose":
        return _print_json({"status": "ready", "diagnosis": diagnose_task(tasks.get(args.task_id), paths)})
    if args.command == "fix":
        task = tasks.get(args.task_id)
        return _print_json(build_fix_prompt(task, diagnose_task(task, paths)))
    if args.command == "heal":
        return _print_json(_heal_payload(args.task_id, tasks, scratchpads, paths))
    if args.command == "cache":
        return _cache_command(args, paths)
    return _print_json({"status": "ready", "tasks": [task.to_dict() for task in tasks.list_active()]})


def _run_or_plan(args, paths: ProjectPaths, tasks: TaskStore, scratchpads: ScratchpadStore, memory: MemoryStore) -> int:
    build_index, _, retrieve_context = _cache_tools()
    from .planner import plan_task
    from .workflow import next_required_reviewer

    task = _create_task(tasks, args.task)
    scratchpad = scratchpads.create(task)
    build_index(paths)
    context = retrieve_context(paths, task.objective)
    plan = None
    planned_task = task
    if task.route == "planner" or args.command == "plan":
        planned_task, plan = plan_task(task)
        planned_task = planned_task.with_workflow_stage("planned")
        tasks.save(planned_task)
    execution = _build_packet(planned_task, paths, scratchpad, context, planned_task.recommended_provider, DEFAULT_EXEC_BUDGET)
    review = _build_review(
        planned_task,
        paths,
        scratchpad,
        context,
        "opencode",
        next_required_reviewer(planned_task),
        DEFAULT_REVIEW_BUDGET,
    )
    summary = memory.create_summary(planned_task, planned_task.objective, f"Prepared {planned_task.route} workflow.", ("task", planned_task.route))
    persisted = planned_task.with_packet(execution).with_memory_ref(summary.ref)
    tasks.save(persisted)
    return _print_json(
        {
            "status": "ready",
            "task": persisted.to_dict(),
            "plan": plan,
            "execution": execution,
            "review": review,
            "memory": {"summary": summary.to_dict()},
        }
    )


def _create_task(tasks: TaskStore, objective: str):
    from .router import recommend_provider, route

    route_name = route(objective)
    provider = recommend_provider(objective, route_name)
    files = _infer_files(objective)
    return tasks.create(
        objective=objective,
        files=files,
        constraints=DEFAULT_CONSTRAINTS,
        done_conditions=DEFAULT_DONE_CONDITIONS,
        risk_level="medium",
        allowed_change_set=files,
        required_checks=DEFAULT_DONE_CONDITIONS,
        required_reviewers=DEFAULT_REQUIRED_REVIEWERS,
        route=route_name,
        provider=provider,
    )


def _execution_payload(args, tasks: TaskStore, scratchpads: ScratchpadStore, paths: ProjectPaths) -> dict[str, object]:
    _, _, retrieve_context = _cache_tools()
    task = tasks.get(args.task_id)
    scratchpad = scratchpads.read(task.id)
    provider = args.provider or "opencode"
    context = retrieve_context(paths, task.objective)
    return _build_packet(task, paths, scratchpad, context, provider, args.budget)


def _review_payload(args, tasks: TaskStore, scratchpads: ScratchpadStore, paths: ProjectPaths) -> dict[str, object]:
    _, _, retrieve_context = _cache_tools()
    from .workflow import next_required_reviewer

    task = tasks.get(args.task_id)
    scratchpad = scratchpads.read(task.id)
    persona = args.persona or next_required_reviewer(task)
    provider = args.provider or "opencode"
    if provider in {"codex", "opencode"}:
        target = default_review_target(persona, provider, args.model)
        provider = target.provider
    context = retrieve_context(paths, task.objective)
    return _build_review(task, paths, scratchpad, context, provider, persona, args.budget)


def _execute_command(args, paths: ProjectPaths, tasks: TaskStore, scratchpads: ScratchpadStore) -> int:
    _, _, retrieve_context = _cache_tools()
    build_launch_command, launch_task = _launcher_tools()
    task = tasks.get(args.task_id)
    scratchpad = scratchpads.read(task.id)
    provider = args.provider or "opencode"
    if provider == "gemini":
        raise ValueError(f"Unsupported launch provider: {provider}")
    target = default_execution_target(task.objective, task.route, provider, args.model)
    target_provider = target.provider
    target_model = target.model
    context = retrieve_context(paths, task.objective)
    execution = _build_packet(task, paths, scratchpad, context, target_provider, args.budget)
    if args.dry_run:
        command = build_launch_command(
            target_provider,
            args.mode,
            str(execution["prompt"]),
            paths.workspace_root,
            target_model,
            args.json,
        )
        return _print_json(
            {
                "status": "ready",
                "launch": {
                    "provider": target_provider,
                    "mode": args.mode,
                    "budget": args.budget,
                    "json_output": args.json,
                    "model": target_model,
                    "command": command,
                    "token_estimate": execution["token_estimate"],
                },
            }
        )
    started_at = _timestamp()
    launch = launch_task(
        target_provider,
        args.mode,
        str(execution["prompt"]),
        paths.workspace_root,
        target_model,
        args.json,
    )
    finished_at = _timestamp()
    record = {
        "kind": "launch",
        "task_id": task.id,
        "provider": target_provider,
        "mode": args.mode,
        "command": list(launch.command),
        "budget": args.budget,
        "model": target_model,
        "json_output": args.json,
        "exit_code": launch.exit_code,
        "started_at": started_at,
        "finished_at": finished_at,
    }
    tasks.save(task.with_launch(record))
    payload = {
        "status": "ready" if launch.exit_code == 0 else "failed",
        "launch": {**record, "stdout": launch.stdout, "stderr": launch.stderr},
    }
    if args.mode == ONESHOT:
        _print_json(payload)
    return launch.exit_code


def _build_packet(task, paths, scratchpad, context, provider: str, budget: int) -> dict[str, object]:
    from .executor import execute_task

    return execute_task(task, paths, scratchpad, context, provider, budget).to_dict()


def _build_review(task, paths, scratchpad, context, provider: str, persona: str, budget: int) -> dict[str, object]:
    from .reviewer import review_task

    return review_task(task, paths, scratchpad, context, provider, persona, budget).to_dict()


def _run_task(
    args,
    paths: ProjectPaths,
    tasks: TaskStore,
    scratchpads: ScratchpadStore,
    memory: MemoryStore,
) -> int:
    from .managed_runner import RunTaskOptions, run_task_command

    payload = run_task_command(
        args.task_id,
        RunTaskOptions(
            provider=args.provider,
            budget=args.budget,
            json_output=args.json,
            model=args.model,
            resume=args.resume,
            review_enabled=not args.no_review,
            checks_enabled=not args.no_checks,
            dry_run=args.dry_run,
        ),
        paths,
        tasks,
        scratchpads,
        memory,
        DEFAULT_REVIEW_BUDGET,
    )
    _print_json(payload)
    if args.dry_run:
        return 0
    return _run_task_exit_code(payload)


def _run_fix(
    args,
    paths: ProjectPaths,
    tasks: TaskStore,
    scratchpads: ScratchpadStore,
    memory: MemoryStore,
) -> int:
    from .managed_runner import RunTaskOptions, run_task_command

    task = tasks.get(args.task_id)
    if task.workflow_stage != "fix_ready":
        raise ValueError("run-fix requires a task in fix_ready stage")
    payload = run_task_command(
        args.task_id,
        RunTaskOptions(
            provider=args.provider,
            budget=args.budget,
            json_output=args.json,
            model=args.model,
            resume=True,
            review_enabled=not args.no_review,
            checks_enabled=not args.no_checks,
            dry_run=args.dry_run,
        ),
        paths,
        tasks,
        scratchpads,
        memory,
        DEFAULT_REVIEW_BUDGET,
    )
    _print_json(payload)
    if args.dry_run:
        return 0
    return _run_task_exit_code(payload)


def _run_review(
    args,
    paths: ProjectPaths,
    tasks: TaskStore,
    scratchpads: ScratchpadStore,
    memory: MemoryStore,
) -> int:
    from .review_runner import RunReviewOptions, run_review_command

    task = tasks.get(args.task_id)
    if task.workflow_stage not in {"implemented", "reviewed", "fix_ready"}:
        raise ValueError("run-review requires a task in implemented, reviewed, or fix_ready stage")
    payload = run_review_command(
        args.task_id,
        RunReviewOptions(
            provider=args.provider,
            budget=args.budget,
            model=args.model,
            json_output=args.json,
            persona=args.persona,
        ),
        paths,
        tasks,
        scratchpads,
        memory,
    )
    _print_json(payload)
    return 0 if payload["status"] in {"active", "completed"} else 1


def _run_queue(
    args,
    paths: ProjectPaths,
    tasks: TaskStore,
    scratchpads: ScratchpadStore,
    memory: MemoryStore,
) -> int:
    from .queue_runner import QueueRunOptions, run_task_queue

    cooldown_seconds = _cooldown_seconds(args.cooldown_hours)
    payload = run_task_queue(
        paths,
        tasks,
        scratchpads,
        memory,
        DEFAULT_REVIEW_BUDGET,
        QueueRunOptions(
            provider=args.provider,
            budget=args.budget,
            json_output=args.json,
            model=args.model,
            resume=args.resume,
            review_enabled=not args.no_review,
            checks_enabled=not args.no_checks,
            cooldown_seconds=cooldown_seconds,
        ),
    )
    _print_json(payload)
    return 0 if payload["status"] == "completed" else 1


def _print_scratch(task_id: str, tasks: TaskStore, scratchpads: ScratchpadStore) -> int:
    task = tasks.get(task_id)
    try:
        text = scratchpads.read(task.id)
    except FileNotFoundError:
        text = scratchpads.create(task)
    print(text, end="" if text.endswith("\n") else "\n")
    return 0


def _complete_task(task_id: str, tasks: TaskStore, scratchpads: ScratchpadStore) -> int:
    from .managed_state import build_completion_record
    from .workflow import can_complete

    task = tasks.get(task_id)
    if not can_complete(task):
        raise ValueError("task cannot be completed before verified implementation and approved review")
    completed = build_completion_record(task)
    tasks.save(completed)
    scratchpads.refresh(completed)
    return _print_json({"status": "ready", "task": completed.to_dict()})


def _run_task_exit_code(payload: dict[str, object]) -> int:
    run = payload["run"]
    if isinstance(run, dict) and int(run.get("exit_code", 0)) != 0:
        return int(run["exit_code"])
    if isinstance(run, dict) and str(run.get("status")) in {
        "no_changes",
        "preflight_blocked",
        "scope_violation",
        "diff_unavailable",
    }:
        return 1
    checks = payload.get("checks")
    if isinstance(checks, dict) and checks.get("status") == "fail":
        return 1
    return 0


def _check_command(args, paths: ProjectPaths) -> int:
    check_architecture, detect_drift, _ = _architecture_tools()
    if args.check_command == "architecture":
        result = check_architecture()
        _print_json({"status": result["status"], "checks": result["checks"]})
        return 0 if result["status"] == "pass" else 1
    return _print_json({"status": "ready", "checks": detect_drift(paths)})


def _heal_payload(task_id: str, tasks: TaskStore, scratchpads: ScratchpadStore, paths: ProjectPaths) -> dict[str, object]:
    check_architecture, _, self_heal = _architecture_tools()
    _, _, retrieve_context = _cache_tools()
    from .diagnosis import build_fix_prompt, diagnose_task

    task = tasks.get(task_id)
    scratchpad = scratchpads.read(task.id)
    context = retrieve_context(paths, task.objective)
    return self_heal(
        task.id,
        lambda: _build_packet(task, paths, scratchpad, context, "opencode", DEFAULT_EXEC_BUDGET),
        lambda: check_architecture(),
        lambda: diagnose_task(task, paths),
        lambda diagnosis: build_fix_prompt(task, diagnosis),
    )


def _cache_command(args, paths: ProjectPaths) -> int:
    build_index, cache_status, _ = _cache_tools()
    if args.cache_command == "build":
        return _print_json({"status": "ready", "cache": build_index(paths)})
    return _print_json({"status": "ready", "cache": cache_status(paths)})


def _add_task_parser(subcommands, name: str, help_text: str) -> None:
    parser = subcommands.add_parser(name, help=help_text)
    parser.add_argument("task", help="Task objective")


def _cooldown_seconds(hours: float) -> int:
    if hours <= 0:
        raise ValueError("cooldown hours must be positive")
    return int(hours * 3600)


def _infer_files(objective: str) -> tuple[str, ...]:
    text = objective.lower()
    if "signal" in text:
        return ("project/signals",)
    if "hypothesis" in text:
        return ("project/hypotheses",)
    if "decision" in text:
        return ("project/decision",)
    return ()


def _print_json(data: object) -> int:
    print(json.dumps(data, indent=2))
    return 0


def _timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


if __name__ == "__main__":
    raise SystemExit(main())
