$ErrorActionPreference = "Stop"

uv lock
uv sync --locked
uv run ruff format .
uv run ruff check .
uv run pyright
uv run pytest
uv run prf-audit
