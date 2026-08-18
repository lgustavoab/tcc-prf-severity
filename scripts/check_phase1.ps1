$ErrorActionPreference = "Stop"

uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest
uv run prf-audit
uv run prf-build-interim
uv run prf-verify-interim
