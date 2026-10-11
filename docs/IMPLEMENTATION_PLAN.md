# Implementation Plan

## Phase 1: Audit and Boundaries

Acceptance criteria:

- Document existing repository state.
- Define backend/frontend boundaries.
- Preserve useful existing UI work.

Status: complete.

## Phase 2: Backend Foundation

Acceptance criteria:

- FastAPI app starts with `/docs`, `/health`, and `/ready`.
- Settings load from environment variables.
- SQLAlchemy models cover users, conversations, messages, documents, orders, payments, refunds, tickets, tool logs, feedback, and evaluations.
- Seed data provides working demo users.

Status: complete.

## Phase 3: Business Workflows

Acceptance criteria:

- Authenticated customers can only read their own orders.
- Refund eligibility is deterministic.
- Refund execution requires confirmation and idempotency.
- Tickets can be created, reviewed, updated, and annotated by support roles.

Status: complete for the local workflow.

## Phase 4: RAG and AI Routing

Acceptance criteria:

- Documents can be indexed into chunks.
- Retrieval returns citations.
- Chat routes intents to allowlisted tools.
- Unsupported questions abstain or escalate.

Status: implemented with deterministic local retrieval and router.

## Phase 5: Frontend Integration

Acceptance criteria:

- Login/register connect to backend auth.
- Customer chat sends all messages through backend.
- Orders, refunds, tickets, knowledge, analytics, and settings pages use real API data.

Status: partial. The UI shell exists; API wiring remains the next phase.

## Phase 6: Advanced Production Hardening

Acceptance criteria:

- Alembic migrations replace development `create_all`.
- Redis-backed rate limiting is enforced.
- pgvector or provider-backed embeddings are available.
- Optional MCP adapter has strict schemas and authorization.
- Observability includes correlation IDs and structured traces.

Status: planned.
