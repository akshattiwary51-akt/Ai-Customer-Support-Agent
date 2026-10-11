# Project Audit

## Repository State

The repository started empty except for a `.git` directory. A frontend prototype was added first and is preserved as the initial React/Vite support console. The full-stack implementation now adds a FastAPI backend under `backend/`, documentation under `docs/`, CI, Docker Compose, and environment examples.

## Current Stack

- Frontend: React, Vite, TypeScript, Lucide React, CSS design tokens.
- Backend: Python 3.11, FastAPI, Pydantic v2, pydantic-settings, SQLAlchemy 2, PyJWT.
- Database: SQLite by default for local development; PostgreSQL supported via `DATABASE_URL`.
- Testing: Pytest, FastAPI TestClient, deterministic local providers.
- Infrastructure: Docker Compose with PostgreSQL, backend, and frontend services.

## Feature Completion Matrix

| Area | Status | Notes |
| --- | --- | --- |
| Repository audit docs | Complete | This file records the baseline and implementation status. |
| Auth/RBAC | Implemented | Local JWT auth, seeded roles, protected routes. |
| Orders/payments | Implemented | Database-backed seeded orders and payments. |
| Refund workflow | Implemented | Eligibility, confirmation, idempotency, status states. |
| Cancellation | Partial | Backend service exists through chat route; direct API endpoint remains to add. |
| Ticket workflow | Implemented | Creation, listing, updates, notes, escalation linkage. |
| Knowledge/RAG | Partial | TXT/MD indexing and lexical retrieval work; PDF/DOCX require optional deps. |
| Chat/memory | Implemented | Persistent conversations/messages and deterministic routing. |
| Streaming chat | Partial | Contract exists; true token streaming remains future work. |
| Analytics | Implemented | Metrics are computed from stored records. |
| Observability | Partial | Tool logs and health endpoints exist; full tracing remains future work. |
| Frontend integration | Partial | Polished console exists; full backend-connected pages remain future work. |
| Tests | Implemented | Core acceptance journeys covered. |
| Docker/CI | Implemented | Compose and GitHub Actions provided. |

## Critical Risks

- `AUTO_CREATE_TABLES=true` is a development shortcut and should be disabled in production once Alembic migrations are finalized.
- Live LLM, embedding, Supabase, Redis, pgvector, and MCP integrations are not enabled by default.
- The frontend currently demonstrates the support console and needs deeper API wiring for every required page.
- Rate limiting is configured but not yet enforced with Redis or middleware.

## Proposed Phases

1. Backend foundation and seeded data.
2. Business workflows and authorization tests.
3. RAG, chat routing, and tool registry.
4. Frontend API integration across all pages.
5. External-provider adapters, pgvector, Redis rate limiting, and MCP.
6. Full observability and evaluation harness.
