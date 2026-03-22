# PA Media Group — Local AI Agent Stack

A local development stack combining a [LangGraph ReAct Agent](https://github.com/langchain-ai/react-agent) backend with an [Agent Chat UI](https://github.com/langchain-ai/agent-chat-ui) frontend, with [Cognee](https://github.com/topoteretes/cognee) for persistent knowledge-graph memory and [Ollama](https://ollama.com) support for local LLMs.

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (v4.x+)
- [Docker Compose](https://docs.docker.com/compose/) (included with Docker Desktop)
- [Ollama Desktop](https://ollama.com/download) running on your Mac

---

## Setup

### 1. Configure environment variables

Copy the example env file and fill in your keys:

```bash
cp .env.example .env   # if it exists, otherwise edit .env directly
```

Edit `.env` and set the following:

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | One of these | Anthropic Claude API key |
| `OPENAI_API_KEY` | One of these | OpenAI API key |
| `FIREWORKS_API_KEY` | One of these | Fireworks AI API key |
| `LANGSMITH_API_KEY` | Optional | For LangSmith tracing ([get one here](https://smith.langchain.com)) |
| `MODEL` | Optional | Model to use, e.g. `ollama/gpt-oss:120b-cloud` |
| `OLLAMA_BASE_URL` | If using Ollama | Defaults to `http://host.docker.internal:11434` |
| `OLLAMA_EMBEDDING_MODEL` | If using Ollama | Pulled automatically on startup, e.g. `nomic-embed-text:latest` |

### 2. Configure Cognee

Edit `.env.cognee` for Cognee-specific settings (LLM provider, vector/graph DB, etc.). By default it is configured to use **Ollama Desktop** on the host:

```env
LLM_PROVIDER=ollama
LLM_MODEL=gpt-oss:120b-cloud
LLM_ENDPOINT=http://host.docker.internal:11434/v1
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text:latest
EMBEDDING_ENDPOINT=http://host.docker.internal:11434/api/embed
```

---

## Running

### Development

Hot reload enabled for both frontend and backend. Unit tests run before the agent server starts.

```bash
docker-compose --profile dev up -d --build
```

| Service | URL |
|---|---|
| Agent Chat UI | http://localhost:3000 |
| LangGraph API | http://localhost:2024 |
| LangGraph API Docs | http://localhost:2024/docs |
| Cognee API | http://localhost:8000 |

### Production

Optimised builds, no source mounts, no dev tooling.

```bash
docker-compose --profile prod up -d --build
```

Same URLs apply.

---

## Using Ollama (local LLM)

This stack uses [Ollama Desktop](https://ollama.com/download) running on your Mac. The cloud LLM (`gpt-oss:120b-cloud`) is served remotely via Ollama and does **not** need pulling. The embedding model is pulled automatically by the react-agent entrypoint before the server starts.

Ollama Desktop exposes its API at `http://localhost:11434` on the host. Containers reach it via `host.docker.internal`. Set in `.env`:

```env
MODEL=ollama/gpt-oss:120b-cloud
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text:latest
```

---

## Cognee Memory Integration

The agent uses [cognee-integration-langgraph](https://docs.cognee.ai/integrations/langgraph-integration) — the official Cognee integration for LangGraph. Cognee runs **in-process** inside the react-agent container (not as an HTTP client to the Cognee REST service). Two tools are registered automatically at agent startup:

| Tool | Description |
|---|---|
| `add_memory` | Ingest text or documents into Cognee's knowledge graph |
| `search_memory` | Retrieve relevant information via semantic graph search |

The agent calls these tools during conversation to store and recall information across sessions. Configuration is read from `.env.cognee` (LLM provider, embedding model, DB paths).

The `cognee` Docker service (port 8000) provides a standalone REST API for interacting with the same knowledge graph from outside the agent (e.g. ingesting data separately). Both the agent container and the cognee container share the same `./cognee/data` volume so their knowledge graphs are in sync.

---

## Stopping

```bash
docker-compose --profile dev down    # or --profile prod
```

---

## Project Structure

```
pa_media_group/
├── docker-compose.yaml       # All services, dev + prod profiles
├── .env                      # Environment variables (not committed)
├── .env.cognee               # Cognee-specific config (LLM, DBs, storage)
├── react-agent/              # LangGraph ReAct Agent (Python)
│   ├── Dockerfile            # Multi-stage: dev (hot reload) + prod
│   ├── entrypoint.sh         # Pulls Ollama models then starts the server
│   ├── src/react_agent/      # Agent graph, tools, prompts
│   └── .venv/                # Python venv (auto-created, git-ignored)
└── agent-chat-ui/            # Next.js chat frontend
    ├── Dockerfile            # Multi-stage: dev (HMR) + prod
    └── src/                  # React components
```

---

## Development Notes

- **Backend hot reload** — `langgraph dev --allow-blocking` watches `src/` via `watchfiles`; save any `.py` file to trigger a reload
- **Frontend hot reload** — Next.js HMR updates the browser instantly on file save
- **Tests** — unit tests in `react-agent/tests/unit_tests/` run automatically on dev container start via `make test`
- **Caching** — Python `.venv` is persisted in `react-agent/.venv/` on the host between restarts
- **Cognee data** — persisted in `./cognee/data/` on the host (mounted into the container)
