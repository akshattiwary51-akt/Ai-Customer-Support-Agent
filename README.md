# ResolveAI Customer Support Agent

ResolveAI is a production-style AI customer support platform. The current implementation includes a FastAPI backend with local authentication, role checks, seeded customers/orders/payments/tickets, deterministic chat routing, knowledge-base retrieval with citations, refund/cancellation workflow rules, analytics, and a polished React support console.

## Demo Credentials

All seeded accounts use `Password123!`.

- Customer: `customer@example.com`
- Second customer for authorization tests: `ava@example.com`
- Support agent: `agent@example.com`
- Admin: `admin@example.com`

## Backend Setup

PowerShell:

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,documents]"
Copy-Item ..\.env.example .env
python -m app.db.seed
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Cross-platform:

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,documents]"
cp ../.env.example .env
python -m app.db.seed
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API docs are available at `http://127.0.0.1:8000/docs`.

## ReAct Agent (LLM tool calling)

`POST /api/v1/chat` runs a real reason -> tool call -> observe -> repeat loop when an Anthropic
key is configured. Without a key, or if the provider fails before any tool has run, it falls
back to the deterministic router, so local development and CI need no credentials.

```bash
python -m pip install -e ".[dev,documents,agent]"
export ANTHROPIC_API_KEY=sk-ant-...      # or put it in backend/.env
# optional: AGENT_MODEL (default claude-sonnet-5-5), AGENT_MAX_STEPS (default 6)
```

The response includes `engine` (`agent` or `deterministic`) and `agent_trace`, the per-step
thought, tool call and observation. Safety is enforced in code (`app/services/agent_service.py`),
not just the prompt: ownership checks on every order lookup, refunds and cancellations only
execute when the client sends `confirm_action=true`, a hard step cap, and prior turns are passed
to the model so follow-ups like "yes, go ahead" resolve correctly.

## Frontend Setup

```powershell
npm install
npm run dev -- --port 5173
```

The frontend runs at `http://127.0.0.1:5173`.

## Quality Commands

```powershell
cd backend
ruff check .
pytest
cd ..
npm run lint
npm run build
```

## Docker Compose

```powershell
docker compose up --build
```

The compose stack starts PostgreSQL, the FastAPI backend, and the Vite frontend. SQLite remains the default for quick local development without Docker.

## Current Status

Implemented:

- Local JWT auth and seeded demo roles.
- Server-side customer ownership checks.
- Orders, payments, refund eligibility, refund requests, tickets, knowledge documents, chat, feedback, health, and analytics endpoints.
- Deterministic local chat router and tool execution logs.
- Ordered orchestration trace endpoint and frontend panel following the LangGraph/LangChain/evaluator flow.
- Knowledge retrieval with citations from indexed chunks.
- Tests for core acceptance journeys.

Known limitations:

- The ReAct agent needs an Anthropic key and has only been tested against a scripted fake model and a stubbed SDK response, not the live API. The `/orchestration/run` trace panel is still the simulated pipeline and does not reflect the agent loop yet.
- Embeddings, pgvector, Supabase Auth, Redis rate limiting, and MCP are adapter-ready but not wired to external services.
- Streaming endpoint currently returns the same safe response contract as synchronous chat.
- Alembic migration files are scaffolded; local development uses `AUTO_CREATE_TABLES=true`.
