# API Summary

Swagger documentation is available at `/docs` when the backend is running.

Implemented endpoints:

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/chat`
- `POST /api/v1/chat/stream`
- `POST /api/v1/orchestration/run`
- `GET /api/v1/conversations`
- `GET /api/v1/conversations/{id}`
- `DELETE /api/v1/conversations/{id}`
- `POST /api/v1/feedback`
- `GET /api/v1/orders`
- `GET /api/v1/orders/{order_number}`
- `GET /api/v1/orders/{order_number}/payment`
- `POST /api/v1/orders/{order_number}/refund-eligibility`
- `POST /api/v1/orders/{order_number}/refund-requests`
- `POST /api/v1/tickets`
- `GET /api/v1/tickets`
- `GET /api/v1/tickets/{id}`
- `PATCH /api/v1/tickets/{id}`
- `POST /api/v1/tickets/{id}/notes`
- `POST /api/v1/knowledge/documents`
- `GET /api/v1/knowledge/documents`
- `DELETE /api/v1/knowledge/documents/{id}`
- `POST /api/v1/knowledge/documents/{id}/reindex`
- `POST /api/v1/knowledge/search`
- `GET /api/v1/analytics/overview`
- `GET /health`
- `GET /ready`
