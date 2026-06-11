# Suggested commands
- Install runtime deps: `pip install -r project/requirements.txt`
- Install dev deps: `pip install -r project/requirements-dev.txt`
- Install developer tooling: `pip install -e ./codex_cli`
- Run the Streamlit cockpit: `streamlit run project/ui/app.py`
- Operator commands: `mft status`, `mft next`, `mft guide`
- Full local check: `./scripts/check.sh`
- Individual checks when needed: `python -m pytest`, `python -m ruff check .`, `python -m mypy`, `mft check architecture`, `mft check drift`
- Use the compatibility entrypoint only when a legacy path is required: `python project/main.py ...`