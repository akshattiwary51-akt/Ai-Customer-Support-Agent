# Evaluation

The backend includes deterministic tests for representative customer-support scenarios:

- Authenticated order lookup.
- Unauthorized cross-customer order lookup denial.
- Chat route using the order-status tool.
- Ordered LangGraph/LangChain-style orchestration trace.
- Refund eligibility, confirmation requirement, and idempotency.
- Cancellation confirmation and status update.
- Knowledge question with citation.
- Unsupported question abstention.
- Human escalation creating a ticket.
- Prompt-injection attempt blocked by ownership checks.
- Customer denial for admin-only knowledge upload.
- Analytics from stored application records.

Tests do not require live LLM, embedding, payment, Supabase, Redis, or MCP credentials.

Future evaluation work:

- Add a JSONL scenario dataset for regression testing.
- Score groundedness by verifying cited chunks contain key answer claims.
- Add prompt-injection fixtures for uploaded documents and user messages.
- Track tool-selection precision and escalation correctness.
- Add optional live-model evals behind explicit environment flags.
