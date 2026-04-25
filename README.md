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

Copy `backend/.env.example` to `backend/.env` and fill in values:

```
JWT_SECRET=change-me-to-a-strong-random-secret   # required
DATABASE_URL=sqlite:///./grantpilot.db            # default SQLite
ANTHROPIC_API_KEY=                                # required for real AI analysis
OPENAI_API_KEY=                                   # optional: enables OpenAI embeddings
UPLOAD_DIR=uploads
JWT_EXPIRE_DAYS=7
```

### Demo login

The backend seeds a demo account on startup:

- **Email:** `demo@grantpilot.local`
- **Password:** `DemoGrantPilot123!`

### Run tests

```bash
cd backend
PYTHONPATH=. python -m pytest tests/ -v
```

### API routes

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/auth/register` | Register a new user |
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
| `POST` | `/documents/upload` | Upload a document (multipart) |
| `DELETE` | `/documents/{id}` | Delete a document (owner only) |
| `GET` | `/projects/{id}/documents` | List project documents |
| `POST` | `/projects/{id}/analyze` | Run grant analysis |
| `GET` | `/projects/{id}/analysis` | Get analysis results |
| `GET` | `/projects/{id}/report` | Get report metadata |
| `GET` | `/projects/{id}/report/download` | Download PDF report (auth required) |

---

## Running Playwright E2E Tests

Playwright tests cover the full authenticated happy path.

### Prerequisites

Both backend and frontend must be running:

```bash
# Terminal 1 — backend
cd backend
PYTHONPATH=. python -m uvicorn app.main:app --port 8000

# Terminal 2 — frontend
cd frontend
npm run dev
```

### Install browsers (first time only)

```bash
cd frontend
npx playwright install chromium
```

### Run E2E tests

```bash
cd frontend
npx playwright test
```

Tests cover: login, dashboard, project detail scores, tab switching, edit form,
report download, project creation, document upload, and delete confirmation.

---

## Key User Flows

### Report Download

After running analysis on a project, clicking **Download Report** fetches the PDF
from the backend with the Bearer token via an authenticated `fetch()` call, then
triggers a browser download via a synthetic anchor click. No `window.open()` is
used, so authentication is preserved.

### Document Deletion

In the project Upload panel, each uploaded document has a delete button (trash icon).
Clicking it shows an inline confirmation ("Delete? Yes / No"). Clicking Yes sends
`DELETE /documents/{id}` and removes the document, its parsed chunks, and its file
from local storage.

### Project Editing

The pencil icon in the project page header opens an inline edit form for grant name,
funder, deadline, grant amount, and source URL. Saving sends `PATCH /projects/{id}`
with only the changed fields. Analysis results are preserved across edits.

---

## Project Structure

```
grantpilot/
├── frontend/          # Next.js 15 app
│   ├── app/           # App Router pages
│   ├── components/    # Shared components
│   ├── lib/           # API client, auth helpers
│   ├── types/         # TypeScript types
│   └── e2e/           # Playwright E2E tests
├── backend/           # FastAPI app (Python 3.11+)
│   ├── app/           # Application code
│   ├── alembic/       # Database migrations
│   └── tests/         # Pytest test suite
├── mcp/               # grant-context-mcp MCP server
├── docs/              # Architecture, product spec, data model, etc.
└── .claude/           # Agents, skills, hooks, slash commands
```

See `docs/MVP_ROADMAP.md` for the full phase plan.
