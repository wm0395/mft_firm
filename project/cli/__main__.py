from __future__ import annotations

from click.exceptions import Exit

from project.cli.app import app


if __name__ == "__main__":
    try:
        result = app.main(args=None, prog_name="mft", standalone_mode=False)
    except Exit as error:
        raise SystemExit(int(error.exit_code or 0))
    raise SystemExit(0 if result is None else int(result))
