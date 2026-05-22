from __future__ import annotations

from project.cli.app import app


def main(argv: list[str] | None = None) -> int:
    from project.cli.legacy import main as legacy_main

    return legacy_main(argv)

__all__ = ["app", "main"]
