# GrantPilot

AI-powered grant eligibility and application assistant for small nonprofits. Upload your nonprofit documents and a grant opportunity — GrantPilot extracts requirements, matches evidence, scores readiness, drafts application answers, and generates a downloadable PDF report.

**Live demo:** [grantpilot.click](https://grantpilot.click) · credentials: `demo@grantpilot.local` / `DemoGrantPilot123!`

## How it works

1. **Upload nonprofit documents** — mission statement, budget, IRS letter, annual report, program description (PDF or TXT)
2. **Upload the grant opportunity** — the RFP or announcement as a Grant Opportunity Document
3. **Run analysis** — Claude extracts grant requirements, matches each one to evidence chunks from your uploaded files, and scores eligibility and readiness
4. **Review results** — requirements table with citations, draft answers for narrative questions, missing documents checklist, risk flags
5. **Download a PDF report** — a shareable readiness packet your team or grant writer can use before submitting

Analysis is transparent: a provenance banner indicates whether results came from the real AI pipeline (`real_pipeline`), a pre-loaded demo (`seeded_demo`), or a fallback when conditions aren't met (`fallback_mock`).

---

## Core Features

- JWT-authenticated multi-user accounts
- Organization and grant project management
- PDF and TXT document upload, parsing, and chunking
- AI-powered grant requirement extraction (Claude Haiku)
- RAG evidence matching with page-level citations and confidence scores
- Deterministic eligibility and readiness scoring (no LLM guessing)
- Draft answer generation for narrative questions, grounded in uploaded documents
- Downloadable PDF grant readiness report (fpdf2)
- Analysis provenance transparency (real\_pipeline / fallback\_mock / seeded\_demo)
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
| `DELETE` | `/organizations/{id}` | Delete org and all its projects (owner only) |
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
edit form, report download, project creation, document upload, delete confirmation,
provenance banner display.

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
│   ├── tests/                 # Pytest test suite (192 tests)
│   ├── .env.example           # Backend env template
│   ├── entrypoint.sh          # Docker entrypoint (runs migrations, starts uvicorn)
│   └── Dockerfile
├── mcp/
│   └── grant-context-mcp/     # MCP server exposing 5 grant-analysis tools
├── demo-assets/               # Sample grant and nonprofit docs for live demos
├── scripts/                   # Demo check and utility scripts
├── docs/                      # Architecture, data model, API contracts, deployment
└── .github/
    └── workflows/ci.yml       # GitHub Actions: backend tests + frontend build + E2E
```

---

## Demo walkthrough

For a quick evaluation:

1. Open the app (local or hosted) — the landing page explains the product
2. Click **Sign in with demo account** or use `demo@grantpilot.local` / `DemoGrantPilot123!`
3. The **dashboard** shows the pre-loaded BrightPath Youth Foundation project (analyzed)
4. Open the project — the indigo provenance banner explains this is pre-loaded demo data
5. Switch tabs: **Requirements · Draft Answers · Missing Docs & Risks**
6. Click **Download Report** to generate and download the PDF readiness packet
7. To test the real AI pipeline: create a new project → upload `demo-assets/sample-grant-opportunity.txt` as Grant Opportunity Document + `demo-assets/sample-mission-statement.txt` as Mission Statement → click **Run Analysis** (requires `ANTHROPIC_API_KEY`)

---

## Testing

Backend: **203 pytest tests** covering auth, organizations (create/delete/ownership), projects, document upload and parsing (PDF + TXT), pipeline stages (embedding, extraction, evidence matching, scoring), analysis provenance, re-analysis, report generation, demo account restrictions, and organization deletion cascade.

Frontend: **22 Playwright E2E tests** covering login, dashboard, project detail, analysis tabs, report download, provenance banner, document upload, and project creation.

```bash
# Backend
cd backend && PYTHONPATH=. python -m pytest tests/ -v

# Frontend typecheck
cd frontend && npm run typecheck

# E2E (both servers must be running)
cd frontend && npx playwright test
```

---

## Readiness check

Verify a local or hosted deployment:

```bash
# Local
python scripts/demo_check.py

# Hosted
python scripts/demo_check.py --api-url https://your-backend.up.railway.app
```

---

## Reset demo data

```bash
cd backend && python scripts/reset_demo.py
```


---

## What I'd build differently in v2

Honest retrospective — written after shipping the full MVP.

**1. Use a real vector database from day one.**
The current TF-IDF embedding fallback works for demos but cosine similarity over 256-dim hash vectors misses semantic matches that pgvector with real embeddings would catch. I'd wire Anthropic or OpenAI embeddings behind the `embed_text()` interface early rather than using the hash fallback as a crutch.

**2. Async analysis instead of synchronous.**
Analysis runs synchronously in the HTTP request cycle. On real documents with many requirements this can take 30+ seconds and risks a timeout. A proper job queue (Celery + Redis, or a simple background task table with polling) would let the UI show genuine live progress and let the server scale independently.

**3. Multi-tenant isolation from the start.**
The user → org → project ownership chain is correct, but the DB schema has no row-level security at the Postgres level. Adding RLS policies would make tenant isolation auditable without relying solely on application-layer checks.

**4. Structured output via tool use instead of JSON-in-text.**
All LLM calls use `call_claude_json()` which extracts JSON from free-text responses. Claude's tool use / structured output feature would make parsing deterministic and eliminate the regex fallback entirely.

**5. Richer citation model.**
Citations are currently stored as flat JSON (document_name, page_number, summary). A proper `Citation` table with FK to `DocumentChunk` would enable citation deduplication, citation re-ranking, and let the UI link directly to the relevant chunk text.

**6. E2E tests against a seeded Postgres (not SQLite).**
CI runs E2E tests against SQLite via the backend's dev path. Some Postgres-specific behavior (FK enforcement, JSON column querying, concurrent writes) is only exercised in production. A test-Postgres service in GitHub Actions would catch more.
