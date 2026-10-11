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

- Live LLM, embedding, pgvector, Supabase Auth, Redis rate limiting, and MCP are adapter-ready but not wired to external services.
- Streaming endpoint currently returns the same safe response contract as synchronous chat.
- Alembic migration files are scaffolded; local development uses `AUTO_CREATE_TABLES=true`.
