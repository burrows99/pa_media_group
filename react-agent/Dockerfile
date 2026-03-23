# ── base: uv + make ──────────────────────────────────────────────────────────
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS base

RUN apt-get update && \
    apt-get install -y --no-install-recommends make curl nodejs npm && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# ── dev: sync at runtime against mounted source, then test + hot reload ─────
FROM base AS dev

ENV UV_PROJECT_ENVIRONMENT=/app/.venv

CMD ["sh", "/app/entrypoint.sh", "dev"]

# ── prod: install only runtime deps then serve with langgraph up ─────────────
FROM base AS prod

ENV UV_PROJECT_ENVIRONMENT=/app/.venv
RUN uv sync --no-dev

CMD ["sh", "/app/entrypoint.sh", "prod"]
