# ── base: uv + make ──────────────────────────────────────────────────────────
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends make && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# ── dev: sync at runtime against mounted source, then test + hot reload ─────
FROM base AS dev

ENV UV_PROJECT_ENVIRONMENT=/app/.venv

CMD ["sh", "-c", "uv sync --group dev && uv run make test && uv run langgraph dev --host 0.0.0.0 --port 2024 --no-browser"]

# ── prod: install only runtime deps then serve with langgraph up ─────────────
FROM base AS prod

ENV UV_PROJECT_ENVIRONMENT=/app/.venv
RUN uv sync --no-dev

CMD ["uv", "run", "langgraph", "up", "--port", "2024"]
