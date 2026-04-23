# GrantPilot

GrantPilot is an AI-powered grant eligibility and application assistant for small nonprofits. It helps organizations analyze grant opportunities, identify missing requirements, match grant criteria to internal evidence, draft first-pass responses, and generate a downloadable readiness packet.

## Why It Matters

Small nonprofits often lack dedicated grant-writing staff. GrantPilot helps them understand whether they are ready to apply and what evidence they need to strengthen their application.

## Core Features

- Upload nonprofit documents
- Upload grant opportunity documents
- Extract grant requirements
- Match requirements to nonprofit evidence
- Score eligibility and readiness
- Identify missing documents
- Draft grant responses with citations
- Generate downloadable PDF packet

## Tech Stack

- Next.js 15 · TypeScript · Tailwind CSS
- FastAPI · Python 3.11+ · Postgres · pgvector
- PyMuPDF · Claude / OpenAI API
- MCP server (grant-context-mcp)

---

## Running the Frontend Locally

### Prerequisites

- Node.js 20+
- npm 10+

### Setup

```bash
cd frontend
npm install
npm run dev
```

The app will be available at **http://localhost:3000**.

It redirects automatically to `/dashboard`.

### Pages

| Route | Description |
|---|---|
| `/dashboard` | Overview of organizations and grant projects |
| `/organizations/new` | Create a nonprofit organization profile |
| `/projects/new` | Create a grant project and upload documents |
| `/projects/[id]` | Grant analysis dashboard — scores, requirements, draft answers, risk flags |

### Demo Data

Phase 1 uses mocked data for:

- **Organization:** BrightPath Youth Foundation (Columbus, Ohio)
- **Grant:** Community STEM Access Fund — Ohio Community Foundation
- **Eligibility score:** 82/100
- **Readiness score:** 74/100
- **10 grant requirements** with evidence citations
- **3 missing documents** (IRS letter, board list, matching funds letter)
- **4 risk flags** (2 high, 2 medium)
- **3 draft grant answers** with citations and missing evidence notes

All data lives in `frontend/lib/mock-data.ts`.

### Other Commands

```bash
npm run build       # Production build
npm run typecheck   # TypeScript check (no emit)
npm run lint        # ESLint
```

---

## Running the Backend Locally

### Prerequisites

- Python 3.11+
- pip

### Setup

```bash
cd backend
pip install fastapi "uvicorn[standard]" pydantic pydantic-settings python-multipart httpx anthropic
```

For running tests, also install:

```bash
pip install pytest pytest-asyncio httpx
```

### Start the API server

```bash
cd backend
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

The API will be available at **http://localhost:8000**.

Interactive docs (Swagger UI): **http://localhost:8000/docs**

### Environment variables

Copy `.env.example` to `.env` and fill in values as needed. In Phase 2 no external services are required — the server runs entirely in-memory.

```
ANTHROPIC_API_KEY=       # Required in Phase 4 (AI analysis)
DATABASE_URL=            # Required in Phase 3 (Postgres + pgvector)
```

### Run tests

```bash
cd backend
PYTHONPATH=. python -m pytest tests/ -v
```

All 25 tests should pass. Tests use `TestClient` (synchronous, no running server required).

### API routes (Phase 2)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/organizations` | Create a nonprofit organization |
| `GET` | `/organizations/{id}` | Get organization details |
| `POST` | `/projects` | Create a grant project |
| `GET` | `/projects/{id}` | Get project details |
| `POST` | `/documents/upload` | Upload a document (multipart/form-data) |
| `GET` | `/projects/{id}/documents` | List documents for a project |
| `POST` | `/projects/{id}/analyze` | Run grant analysis (mocked in Phase 2) |
| `GET` | `/projects/{id}/analysis` | Get analysis results |
| `GET` | `/projects/{id}/report` | Get report metadata and PDF URL |

---

## Project Structure

```
grantpilot/
├── frontend/          # Next.js app (Phase 1: mocked demo)
├── backend/           # FastAPI app (Phase 2+)
├── mcp/               # grant-context-mcp server (Phase 6)
├── docs/              # Architecture, product spec, data model, etc.
└── .claude/           # Agents, skills, hooks, slash commands
```

See `docs/MVP_ROADMAP.md` for the full phase plan.
