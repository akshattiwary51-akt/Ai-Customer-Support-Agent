# Final Report

## Implemented

- FastAPI backend with versioned API routes, Swagger docs, health/readiness endpoints, and CORS.
- Local JWT authentication with seeded CUSTOMER, SUPPORT_AGENT, and ADMIN accounts.
- SQLAlchemy data model for users, conversations, messages, documents, chunks, orders, items, payments, refunds, tickets, ticket events, tool logs, feedback, and evaluation runs.
- Alembic migration scaffold with an initial schema migration.
- Seeded fictional development data and demo credentials.
- Server-side authorization and customer ownership checks.
- Deterministic intent routing for order status, payment, refunds, cancellation, human escalation, and knowledge search.
- Traceable orchestration endpoint matching the requested diagram order: User, LangGraph state/orchestrator/nodes, LangChain blocks, retriever/vector DB, LLM/tools, evaluator, response or retry.
- Architecture graph response with clickable node metadata and solid/dashed edges for normal flow and retry loops.
- Allowlisted backend tools for order lookup, payment status, refund eligibility, refund requests, cancellation, ticket creation, and knowledge search.
- Refund workflow with deterministic eligibility, confirmation requirement, status records, and idempotency keys.
- Ticket workflow with creation, agent updates, notes, escalation reason, and customer/agent scoped access.
- Knowledge document ingestion for TXT/Markdown and optional PDF/DOCX extraction dependencies.
- Lexical retrieval with citations and unsupported-answer abstention.
- Persistent conversations, messages, citations, feedback, tool execution logs, and analytics.
- React/Vite frontend with a polished support console, working demo login/analytics actions, a live backend-connected customer journey panel, and a diagram-style orchestration view aligned to the supplied reference.
- Docker Compose, `.env.example`, GitHub Actions, README, architecture/security/API/evaluation docs, and feature checklist.

## Verification Run

- `pytest` in `backend`: 11 passed.
- `ruff check .` in `backend`: passed.
- `npm run lint`: passed.
- `npm run build`: passed.
- Live API smoke test:
  - Customer login succeeded.
  - `/api/v1/orders` returned 2 customer-owned orders.
- `/api/v1/chat` answered `ORD-1001` using the database-backed order tool.
- Agent analytics returned computed backlog/tool-success metrics.
- Expanded acceptance tests cover cancellation confirmation, unsupported-answer abstention, prompt-injection ownership denial, and knowledge-upload RBAC.

## Known Limitations

- True token streaming is not yet implemented; `/chat/stream` currently returns the same safe response contract as `/chat`.
- RAG uses deterministic lexical retrieval locally; pgvector/embedding-provider integration remains a planned production hardening step.
- Redis-backed rate limiting and full correlation-ID tracing are not yet wired.
- Supabase Auth, live LLM providers, payment gateways, and MCP are optional future adapters, not enabled by default.
- The frontend includes one live backend workflow panel plus the support console shell; the remaining pages can now be connected to the API surface.
