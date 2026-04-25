# GrantPilot

AI-powered grant eligibility and application assistant for small nonprofits. Upload your nonprofit documents and a grant opportunity — GrantPilot extracts requirements, matches evidence, scores readiness, drafts application answers, and generates a downloadable PDF report.

## Core Features

- JWT-authenticated multi-user accounts
- Organization and grant project management
- PDF document upload, parsing, and chunking
- AI-powered grant requirement extraction (Claude)
- Evidence matching with citations and confidence scores
- Deterministic eligibility and readiness scoring
- Draft answer generation for narrative questions
- Downloadable PDF grant readiness report
- MCP server for agent-driven grant analysis workflows

## Tech Stack

- **Frontend:** Next.js 15 · TypeScript · Tailwind CSS
- **Backend:** FastAPI · Python 3.11+ · SQLAlchemy · Alembic · Postgres / SQLite
- **AI:** Anthropic Claude (analysis) · OpenAI optional (embeddings)
- **PDF:** PyMuPDF (parsing) · fpdf2 (report generation)
- **MCP:** grant-context-mcp server
- **Tests:** Pytest · Playwright

---

## Quick Start — Docker Compose

The fastest way to run the full stack locally.

### 1. Copy and fill the root env template

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

```
JWT_SECRET=<run: python -c "import secrets; print(secrets.token_hex(32))">
ANTHROPIC_API_KEY=<your key>   # optional — enables real AI analysis
```

### 2. Build and start

```bash
docker compose up --build
```

On first boot this will:
- Start Postgres and wait for it to be ready
- Run all Alembic migrations (`alembic upgrade head`)
- Seed the demo account and BrightPath demo project
- Serve the API on **http://localhost:8000**
- Serve the frontend on **http://localhost:3000**

### 3. Sign in

Open **http://localhost:3000** and use the pre-filled demo credentials:

| Field | Value |
|-------|-------|
| Email | `demo@grantpilot.local` |
| Password | `DemoGrantPilot123!` |

---

## Local Development (without Docker)

### Backend

**Prerequisites:** Python 3.11+, pip

```bash
cd backend
cp .env.example .env      # fill in JWT_SECRET at minimum
pip install -e ".[dev]"   # installs all deps from pyproject.toml
```

Start the API server (SQLite used by default):

```bash
PYTHONPATH=. python -m uvicorn app.main:app --reload --port 8000
```

- API: **http://localhost:8000**
- Swagger docs: **http://localhost:8000/docs**

Run tests:

```bash
PYTHONPATH=. python -m pytest tests/ -v
```

### Frontend

**Prerequisites:** Node.js 20+, npm

```bash
cd frontend
cp .env.local.example .env.local    # NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev
```

- App: **http://localhost:3000**

Other commands:

```bash
npm run build       # Production build
npm run typecheck   # TypeScript check
npx playwright test # E2E tests (requires both servers running)
```

---

## Environment Files

### What to create

| File | Copy from | Purpose |
|------|-----------|---------|
| `.env` | `.env.example` | Docker Compose secrets (JWT, Postgres, API keys) |
| `backend/.env` | `backend/.env.example` | Local backend dev without Docker |
| `frontend/.env.local` | `frontend/.env.local.example` | Frontend API base URL |
| `mcp/grant-context-mcp/.env` | `mcp/grant-context-mcp/.env.example` | MCP server config |

### What is gitignored

All actual secret files are gitignored and **never committed**:

```
.env                          # root docker-compose secrets
backend/.env                  # backend local dev
frontend/.env.local           # frontend local dev
frontend/.env.production
mcp/grant-context-mcp/.env
```

Only the `.example` templates are tracked in git — they contain no real secrets.

### Key variables

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `JWT_SECRET` | **Yes** | dev default | Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DATABASE_URL` | No | SQLite (local) | Set to Postgres URL in production |
| `ANTHROPIC_API_KEY` | No | — | Required for real AI grant analysis |
| `OPENAI_API_KEY` | No | — | Optional; enables OpenAI embeddings |
| `ALLOWED_ORIGINS` | No | `http://localhost:3000` | Comma-separated frontend origins |
| `NEXT_PUBLIC_API_URL` | No | `http://localhost:8000` | Baked into frontend at build time |

---

## Pages

| Route | Description |
|-------|-------------|
| `/login` | Sign in with email and password |
| `/dashboard` | All organizations and grant projects with analysis scores |
| `/account` | User profile, stats, and sign-out |
| `/organizations/new` | Create a nonprofit organization |
| `/projects/new` | Create a grant project |
| `/projects/[id]` | Upload documents, run analysis, view scores, download report |

---

## API Routes

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/auth/register` | Register and receive JWT |
| `POST` | `/auth/login` | Login and receive JWT |
| `GET` | `/auth/me` | Get current user |
| `GET` | `/organizations` | List user's organizations |
| `POST` | `/organizations` | Create an organization |
| `GET` | `/organizations/{id}` | Get organization (owner only) |
| `GET` | `/organizations/{id}/projects` | List org's projects |
| `GET` | `/projects` | List all user's projects |
| `POST` | `/projects` | Create a project |
| `GET` | `/projects/{id}` | Get project (owner only) |
| `PATCH` | `/projects/{id}` | Update project metadata |
| `DELETE` | `/projects/{id}` | Delete project and all data |
| `POST` | `/documents/upload` | Upload a document (multipart) |
| `DELETE` | `/documents/{id}` | Delete a document (owner only) |
| `GET` | `/projects/{id}/documents` | List project documents |
| `POST` | `/projects/{id}/analyze` | Run grant analysis |
| `GET` | `/projects/{id}/analysis` | Get analysis results |
| `GET` | `/projects/{id}/report` | Get report metadata |
| `GET` | `/projects/{id}/report/download` | Download PDF report (authenticated) |

---

## Playwright E2E Tests

Both backend and frontend must be running first:

```bash
# Terminal 1
cd backend && PYTHONPATH=. python -m uvicorn app.main:app --port 8000

# Terminal 2
cd frontend && npm run dev
```

Then in a third terminal:

```bash
cd frontend
npx playwright install chromium   # first time only
npx playwright test
```

Tests cover: login, sign-out, dashboard, project detail scores, tab switching,
edit form, report download, project creation, document upload, delete confirmation.

---

## Key User Flows

### Document Upload & Analysis

1. Create a project → opens the Upload panel
2. Upload nonprofit documents (mission statement, budget, annual report, etc.)
3. Upload the **Grant Opportunity Document** (enables AI extraction)
4. Click **Run Analysis** — extracts requirements, matches evidence, scores readiness
5. View requirements table, draft answers, risk flags, and missing documents

### Report Download

Clicking **Download Report** fetches the PDF via an authenticated `fetch()` request
(not `window.open`) so the Bearer token is sent correctly. The PDF is generated
lazily on first request and cached for subsequent downloads.

### Project Deletion

The **Delete** button in the project header shows an inline confirmation before
permanently removing the project, all uploaded documents, parsed chunks, analysis
results, and report files.

---

## Deployment

See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for full instructions covering:

- Docker Compose production stack with Postgres
- Alembic migration flow
- CORS and rate limiting configuration
- HTTPS / reverse proxy setup (Nginx example)
- GitHub Actions CI setup

---

## Project Structure

```
grantpilot/
├── .env.example               # Docker Compose env template (copy to .env)
├── docker-compose.yml         # Production-style stack: Postgres + backend + frontend
├── frontend/                  # Next.js 15 app
│   ├── app/                   # App Router pages
│   ├── components/            # Shared UI components
│   ├── lib/                   # API client, auth helpers, hooks
│   ├── types/                 # TypeScript type definitions
│   ├── e2e/                   # Playwright E2E tests
│   ├── .env.local.example     # Frontend env template
│   └── Dockerfile
├── backend/                   # FastAPI app (Python 3.11+)
│   ├── app/                   # Application code
│   │   ├── api/               # Route handlers
│   │   ├── core/              # Config, security, database, rate limiting
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   └── services/          # Business logic
│   ├── alembic/               # Database migrations
│   ├── tests/                 # Pytest test suite (162 tests)
│   ├── .env.example           # Backend env template
│   ├── entrypoint.sh          # Docker entrypoint (runs migrations, starts uvicorn)
│   └── Dockerfile
├── mcp/
│   └── grant-context-mcp/     # MCP server exposing 5 grant-analysis tools
├── docs/                      # Architecture, data model, API contracts, deployment
└── .github/
    └── workflows/ci.yml       # GitHub Actions: backend tests + frontend build + E2E
```
