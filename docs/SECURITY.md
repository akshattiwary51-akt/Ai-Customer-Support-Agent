# Security Notes

- Secrets are loaded from environment variables. `.env` files are ignored and must not be committed.
- Passwords use PBKDF2-HMAC-SHA256 with per-password salts.
- API access uses signed JWT bearer tokens.
- Protected routes validate the authenticated user on the server.
- Customers can only access their own orders, conversations, tickets, refunds, and feedback.
- Support-agent and admin routes use role checks.
- Refunds and cancellations are enforced by deterministic backend policy, not LLM text.
- Uploaded documents are treated as untrusted reference data.
- Tool execution logs store safe metadata only.
- Live provider keys, raw tokens, and private messages are not logged by default.

Production hardening still needed:

- Replace development table creation with Alembic migrations.
- Add Redis-backed rate limiting middleware.
- Add correlation IDs on all request logs.
- Enable PostgreSQL row-level safeguards where applicable.
- Run a dependency and container security scan in CI.
