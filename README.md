# PA Media Group — Local AI Agent Stack

A local development stack combining a [LangGraph ReAct Agent](https://github.com/langchain-ai/react-agent) backend with an [Agent Chat UI](https://github.com/langchain-ai/agent-chat-ui) frontend, with optional [Ollama](https://ollama.com) support for local LLMs.

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (v4.x+)
- [Docker Compose](https://docs.docker.com/compose/) (included with Docker Desktop)

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
| `TAVILY_API_KEY` | Yes | Search tool used by the agent ([get one here](https://app.tavily.com)) |
| `LANGSMITH_API_KEY` | Optional | For LangSmith tracing ([get one here](https://smith.langchain.com)) |
| `MODEL` | Optional | Model to use, e.g. `ollama/gpt-oss:120b-cloud` or `anthropic/claude-sonnet-4-5-20250929` |
| `OLLAMA_BASE_URL` | If using Ollama | Defaults to `http://ollama:11434` |

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

### Production

Optimised builds, no source mounts, no dev tooling.

```bash
docker-compose --profile prod up -d --build
```

Same URLs apply.

---

## Using Ollama (local LLM)

This stack uses [Ollama Desktop](https://ollama.com/download) running on your Mac. Make sure you are signed in and have the model pulled:

```bash
ollama pull gpt-oss:120b-cloud
```

Ollama Desktop exposes its API at `http://localhost:11434` on the host. The agent container reaches it via Docker's host gateway. Set in `.env`:

```env
MODEL=ollama/gpt-oss:120b-cloud
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

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
├── react-agent/              # LangGraph ReAct Agent (Python)
│   ├── Dockerfile            # Multi-stage: dev (hot reload) + prod
│   ├── src/react_agent/      # Agent graph, tools, prompts
│   └── .venv/                # Python venv (auto-created, git-ignored)
└── agent-chat-ui/            # Next.js chat frontend
    ├── Dockerfile            # Multi-stage: dev (HMR) + prod
    └── src/                  # React components
```

---

## Development Notes

- **Backend hot reload** — `langgraph dev` watches `src/` via `watchfiles`; save any `.py` file to trigger a reload
- **Frontend hot reload** — Next.js HMR updates the browser instantly on file save
- **Tests** — unit tests in `react-agent/tests/unit_tests/` run automatically on dev container start via `make test`
- **Caching** — Python `.venv` is persisted in `react-agent/.venv/` on the host between restarts
