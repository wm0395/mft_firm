# Tech stack
- Language: Python 3.12.
- Packaging/config: `pyproject.toml` for the main project; runtime pins in `project/requirements.txt`; dev deps in `project/requirements-dev.txt`.
- Main runtime deps: `click`, `pandas`, `plotly`, `rich`, `streamlit`, `streamlit-option-menu`, `typer`, `duckdb`, `yfinance`; optional Postgres via `psycopg[binary]`.
- Tooling: `pytest`, `ruff`, `mypy==2.0.0`.
- CLI entrypoint: `mft = project.cli:app`.
- Separate developer package: `codex_cli/`, installed with `pip install -e ./codex_cli`, command `ai_code`.
- Streamlit cockpit entrypoint: `streamlit run project/ui/app.py`.