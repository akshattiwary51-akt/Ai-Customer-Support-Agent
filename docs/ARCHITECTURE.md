# Architecture

ResolveAI separates deterministic business logic from AI-style routing.

## Backend

- `app/main.py`: FastAPI factory and router registration.
- `app/models.py`: normalized SQLAlchemy schema.
- `app/schemas.py`: Pydantic API contracts.
- `app/services/intent_service.py`: deterministic intent classification and entity extraction.
- `app/services/business_service.py`: order ownership, refund policy, cancellation, tickets, and tool logs.
- `app/services/knowledge_service.py`: upload extraction, chunking, lexical retrieval, and citations.
- `app/services/chat_service.py`: orchestration layer that persists messages and invokes allowlisted tools.
- `app/services/orchestration_service.py`: traceable LangGraph/LangChain-style flow that runs in the requested order: user input, state, orchestrator, routed node, LangChain blocks, retriever/vector store, LLM/tool actions, evaluator, and response/retry.

## Data Flow

1. A user authenticates through `/api/v1/auth/login`.
2. A chat request reaches `/api/v1/chat`.
3. The router classifies intent and extracts required entities.
4. Business tools validate authorization and execute deterministic logic.
5. The response is persisted with citations/tool metadata.
6. Analytics reads stored records rather than fabricated metrics.

## Ordered Agent Flow

The `/api/v1/orchestration/run` endpoint exposes the diagrammed flow as executable trace data and graph data for the frontend architecture view:

1. User request.
2. LangGraph state.
3. LangGraph orchestrator.
4. Billing, Technical, or General node selection.
5. LangChain building blocks.
6. Retriever.
7. Vector DB adapter.
8. LLM provider slot.
9. Authorized tools.
10. Evaluator quality gate.
11. Good response, safe failure, or retry loop.

Each run returns ordered `steps` plus clickable `graph_nodes` and `graph_edges`. The UI renders those nodes in the same shape as the reference architecture: LangGraph controls routing and retry, LangChain provides retriever/LLM/tool building blocks, and the evaluator chooses the response or retry path.

## Security Boundary

The browser never calls LLM providers or privileged business integrations directly. All private customer data is guarded by backend authorization and ownership checks.
