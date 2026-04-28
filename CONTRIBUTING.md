# Contributing to GrantPilot

## Project Overview

GrantPilot is a monorepo with three main parts:

```
backend/   FastAPI Python app (API, business logic, database, AI pipeline)
frontend/  Next.js TypeScript app (web UI, auth, API client)
mcp/       grant-context-mcp MCP server (agent tools, local-only)
```

Each is independently runnable. They share no code — the frontend talks to the
backend over HTTP, and the MCP server talks to the database directly.

---

## Local Development Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- npm 10+

### Backend

```bash
cd backend
cp .env.example .env       # fill in JWT_SECRET at minimum
pip install -e ".[dev]"    # installs all deps from pyproject.toml
PYTHONPATH=. python -m uvicorn app.main:app --reload --port 8000
```

The backend uses SQLite by default (`grantpilot.db`). The demo seed runs on
startup automatically — no manual DB setup needed.

### Frontend

```bash
cd frontend
cp .env.local.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev
```

Open **http://localhost:3000**. The app redirects to `/login`.

Demo account: `demo@grantpilot.local` / `DemoGrantPilot123!`

---

## Project Structure

### Backend (`backend/app/`)

```
api/         Route handlers — thin, delegate to services
core/        Config, database, security, rate limiting
models/      SQLAlchemy ORM models
schemas/     Pydantic request/response types
services/    Business logic — keep this layer focused and testable
alembic/     Database migrations
tests/       Pytest test suite
```

**Key principle:** routes call services, services own logic. Never put SQL or
AI calls directly in route handlers.

### Frontend (`frontend/`)

```
app/           Next.js App Router pages
components/    Shared UI components
lib/           API client (api.ts), auth helpers, hooks
types/         TypeScript interface definitions
e2e/           Playwright end-to-end tests
```

**Key principle:** all backend calls go through `lib/api.ts`. Components never
call `fetch` directly. Types in `types/index.ts` must stay in sync with the
backend Pydantic schemas.

---

## Adding a New Feature

### Backend

1. **Add a Pydantic schema** in `app/schemas/` for request and response types.
2. **Add a service function** in `app/services/` with the business logic.
3. **Add a route** in `app/api/` that calls the service and returns the schema.
4. **Wire ownership checks** using `require_project_access` or `require_org_access`
   from `app/api/deps.py` on every protected route.
5. **Add a migration** if the DB schema changed:
   ```bash
   cd backend
   PYTHONPATH=. alembic revision --autogenerate -m "description"
   PYTHONPATH=. alembic upgrade head
   ```
6. **Write tests** in `tests/`. Every new endpoint should have at minimum:
   - Happy path (correct data, correct user)
   - Auth required (401 without token)
   - Ownership enforced (403 for other user)
   - 404 for missing resource

### Frontend

1. **Add the API function** to `lib/api.ts` using `apiFetch`.
2. **Add the TypeScript type** to `types/index.ts` matching the backend schema.
3. **Build the UI** in `app/` or `components/`. Use `useDocumentTitle` for page
   titles and `useEffect` + `useState` for data fetching.
4. **Run the typecheck** before committing: `npm run typecheck`

---

## Testing

### Backend tests

```bash
cd backend
PYTHONPATH=. python -m pytest tests/ -v
```

**203 tests** covering auth, organizations (create/delete/ownership), projects,
document upload and parsing (PDF + TXT), the full AI pipeline (embedding, extraction,
evidence matching, scoring), analysis provenance, re-analysis, report generation,
demo account restrictions, and Phase 13–19 features.

Tests use a fresh SQLite in-memory database per test (via the `test_engine`
fixture in `conftest.py`). Rate limiting is disabled automatically during tests.

Key fixtures in `conftest.py`:
- `client` — authenticated `TestClient` with a test user's JWT pre-attached
- `org_id` — creates a test organization, returns its ID
- `project_id` — creates a test project under `org_id`, returns its ID

### Frontend typecheck

```bash
cd frontend
npm run typecheck
```

### E2E tests (Playwright)

Requires both backend and frontend running:

```bash
# Terminal 1: backend
cd backend && PYTHONPATH=. python -m uvicorn app.main:app --port 8000

# Terminal 2: frontend
cd frontend && npm run dev

# Terminal 3: tests
cd frontend && npx playwright test
```

First time: `npx playwright install chromium`

**22 E2E tests** covering login, dashboard, project detail, analysis tabs, report download,
provenance banners, document upload/delete, project creation, and edit form.

---

## Database Migrations

GrantPilot uses Alembic for schema migrations. Migration files live in
`backend/alembic/versions/`.

```bash
# Apply all pending migrations
cd backend && PYTHONPATH=. alembic upgrade head

# Generate a new migration after changing a model
PYTHONPATH=. alembic revision --autogenerate -m "add_field_to_table"

# Check current revision
PYTHONPATH=. alembic current
```

In **local dev** (SQLite), `create_all_tables()` runs on startup and handles
schema creation automatically — no need to run Alembic manually.

In **production** (Postgres / Docker), the `entrypoint.sh` runs
`alembic upgrade head` before starting uvicorn. Set `RUN_MIGRATIONS=true` in
the environment to trigger this.

---

## Environment Files

Never commit `.env` files. See the `*.example` templates:

| Template | Copy to | Used by |
|----------|---------|---------|
| `.env.example` | `.env` | Docker Compose |
| `backend/.env.example` | `backend/.env` | Local backend dev |
| `frontend/.env.local.example` | `frontend/.env.local` | Local frontend dev |

---

## Code Conventions

### Backend
- Use Pydantic schemas for all request/response types — never return raw dicts from routes
- Use `synchronize_session="fetch"` on bulk SQLAlchemy deletes
- Delete child rows before parent rows (Postgres enforces FK constraints)
- Rate limiting is in `app/core/rate_limit.py` — apply to public endpoints
- Passwords: use `bcrypt` via `app/core/security.py`

### Frontend
- `"use client"` pages that use `useSearchParams` must be wrapped in `<Suspense>`
  by a parent server component (Next.js 15 requirement)
- Use `useDocumentTitle(title)` from `lib/use-document-title.ts` on every page
- Error messages from `ApiError` are shown directly in the UI; status `0` means
  network unreachable (show a specific "backend unreachable" message)
- `NEXT_PUBLIC_*` variables are baked at build time — changing them requires a rebuild

---

## CI

GitHub Actions runs on every push to `main` and on PRs:

- `backend-tests` — pytest (all branches)
- `frontend-checks` — typecheck + production build (all branches)
- `e2e-tests` — Playwright against production build (main branch only)

See `.github/workflows/ci.yml` for the full config.
