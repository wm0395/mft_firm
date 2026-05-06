from __future__ import annotations

import argparse
import json
import sys

from .architecture import check_architecture, detect_drift, self_heal
from .diagnosis import build_fix_prompt, diagnose_task
from .executor import execute_task
from .paths import ProjectPaths
from .planner import plan_task
from .reviewer import review_task
from .router import route
from .scratchpad import ScratchpadStore
from .tasks import TaskStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mft")
    subcommands = parser.add_subparsers(dest="command", required=True)

    run_parser = subcommands.add_parser("run", help="Create, scratch, execute, and review a task")
    run_parser.add_argument("task", help="Task description")

    plan_parser = subcommands.add_parser("plan", help="Create a task plan")
    plan_parser.add_argument("task", help="Task description")

    exec_parser = subcommands.add_parser("exec", help="Build executor prompt for a task")
    exec_parser.add_argument("task_id")

    review_parser = subcommands.add_parser("review", help="Review a task")
    review_parser.add_argument("task_id")

    scratch_parser = subcommands.add_parser("scratch", help="Show or create a task scratchpad")
    scratch_parser.add_argument("task_id")

    complete_parser = subcommands.add_parser("complete", help="Mark a task completed")
    complete_parser.add_argument("task_id")

    check_parser = subcommands.add_parser("check", help="Run enforcement checks")
    check_subcommands = check_parser.add_subparsers(dest="check_command", required=True)
    check_subcommands.add_parser("architecture", help="Run layer-lint and architecture tests")
    check_subcommands.add_parser("drift", help="Detect architecture prompt and memory drift")

    diagnose_parser = subcommands.add_parser("diagnose", help="Diagnose a task architecture violation")
    diagnose_parser.add_argument("task_id")

    fix_parser = subcommands.add_parser("fix", help="Build an architecture-only fix prompt")
    fix_parser.add_argument("task_id")

    heal_parser = subcommands.add_parser("heal", help="Run the explicit self-healing loop for a task")
    heal_parser.add_argument("task_id")

    subcommands.add_parser("list", help="List active tasks")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = ProjectPaths()
    tasks = TaskStore(paths)
    scratchpads = ScratchpadStore(paths)

    try:
        if args.command == "run":
            task = tasks.create(args.task, route(args.task))
            scratchpad = scratchpads.create(task)
            plan = plan_task(task) if task.route == "planner" else None
            result = execute_task(task, scratchpad, _read_agents(paths))
            task.review = review_task(task)
            tasks.save(task)
            return _print_json({"task": task.to_dict(), "plan": plan, "execution": result, "review": task.review})

        if args.command == "plan":
            task = tasks.create(args.task, "planner")
            scratchpads.create(task)
            plan = plan_task(task)
            tasks.save(task)
            return _print_json({"task": task.to_dict(), "plan": plan})

        if args.command == "exec":
            task = tasks.get(args.task_id)
            scratchpad = scratchpads.read(task.id)
            return _print_json(execute_task(task, scratchpad, _read_agents(paths)))

        if args.command == "review":
            task = tasks.get(args.task_id)
            task.review = review_task(task)
            tasks.save(task)
            return _print_json(task.review)

        if args.command == "scratch":
            task = tasks.get(args.task_id)
            try:
                text = scratchpads.read(task.id)
            except FileNotFoundError:
                text = scratchpads.create(task)
            print(text, end="" if text.endswith("\n") else "\n")
            return 0

        if args.command == "complete":
            task = tasks.complete(args.task_id)
            return _print_json(task.to_dict())

        if args.command == "check":
            if args.check_command == "architecture":
                result = check_architecture()
                _print_json(result)
                return 0 if result["status"] == "pass" else 1

            if args.check_command == "drift":
                return _print_json(detect_drift(paths))

        if args.command == "diagnose":
            task = tasks.get(args.task_id)
            return _print_json(diagnose_task(task, paths))

        if args.command == "fix":
            task = tasks.get(args.task_id)
            diagnosis = diagnose_task(task, paths)
            return _print_json(build_fix_prompt(task, diagnosis))

        if args.command == "heal":
            task = tasks.get(args.task_id)
            scratchpad = scratchpads.read(task.id)

            def run_executor() -> dict[str, object]:
                return execute_task(task, scratchpad, _read_agents(paths))

            def architecture_passes() -> dict[str, object]:
                return check_architecture()

            def diagnose() -> dict[str, object]:
                return diagnose_task(task, paths)

            def fix(diagnosis: dict[str, object]) -> dict[str, object]:
                return build_fix_prompt(task, diagnosis)

            return _print_json(self_heal(task.id, run_executor, architecture_passes, diagnose, fix))

        if args.command == "list":
            return _print_json({"tasks": [task.to_dict() for task in tasks.list_active()]})
    except FileNotFoundError as error:
        print(str(error), file=sys.stderr)
        return 1
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2

    return 0


def _read_agents(paths: ProjectPaths) -> str:
    if not paths.agents_file.exists():
        return ""
    return paths.agents_file.read_text(encoding="utf-8")


def _print_json(data: object) -> int:
    print(json.dumps(data, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
