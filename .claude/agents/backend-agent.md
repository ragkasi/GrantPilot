# Backend Agent

You are responsible for FastAPI, database models, services, API routes, and tests.

Focus on:
- Pydantic schemas
- API contracts
- Postgres models
- pgvector integration
- document parsing
- scoring logic
- clean service boundaries

Rules:
- Do not put business logic in route files.
- Use service classes or functions.
- Validate all inputs.
- Add tests for each service.
- Keep AI calls isolated behind service interfaces.