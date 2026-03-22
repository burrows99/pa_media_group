#!/bin/sh
# entrypoint.sh – pull required Ollama models from the host before starting the server.
#
# The LLM (gpt-oss:120b-cloud) is a cloud model served via Ollama and does not
# need pulling. Only the local embedding model needs to be downloaded first.
#
# Environment variables (all have sensible defaults):
#   OLLAMA_BASE_URL      – Ollama host reachable from this container
#   OLLAMA_EMBEDDING_MODEL – embedding model to pull before starting

set -e

OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://host.docker.internal:11434}"
OLLAMA_EMBEDDING_MODEL="${OLLAMA_EMBEDDING_MODEL:-nomic-embed-text:latest}"

echo "==> Waiting for Ollama at ${OLLAMA_BASE_URL} ..."
until curl -sf "${OLLAMA_BASE_URL}/api/tags" > /dev/null 2>&1; do
  sleep 2
done
echo "==> Ollama is reachable."

echo "==> Pulling embedding model: ${OLLAMA_EMBEDDING_MODEL}"
curl -sf -X POST "${OLLAMA_BASE_URL}/api/pull" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"${OLLAMA_EMBEDDING_MODEL}\"}" | tail -1
echo "==> Model ready."

# ── launch the appropriate server mode ───────────────────────────────────────
MODE="${1:-prod}"

if [ "$MODE" = "dev" ]; then
  echo "==> Starting LangGraph dev server..."
  uv sync --group dev
  uv run make test
  exec uv run langgraph dev --host 0.0.0.0 --port 2024 --no-browser --allow-blocking
else
  echo "==> Starting LangGraph prod server..."
  exec uv run langgraph up --port 2024
fi
