# GrantPilot Architecture

## Overview

GrantPilot is split into three main systems:

1. **Frontend web app** — Next.js (TypeScript, Tailwind) — user interaction, auth, file upload UI
2. **Backend API** — FastAPI (Python) — auth, document processing, AI pipeline, scoring, report generation
3. **MCP tool server** — optional — exposes backend capabilities to Claude agents via the Model Context Protocol

The frontend talks to the backend over HTTP with a Bearer JWT.
The MCP server imports backend service modules directly (no HTTP round-trip).
All three share the same Postgres/SQLite database.

---

## System Diagram

```
Browser
  |
  | HTTPS (Bearer JWT)
  v
Next.js Frontend  (port 3000)
  |
  | REST API calls
  v
FastAPI Backend   (port 8000)
  |
  |── Postgres / SQLite (pgvector in production)
  |── Local uploads/ directory (or S3/Supabase in production)
  |── Anthropic Claude API (requirement extraction, evidence matching, drafting)
  |── OpenAI API (optional — embeddings only)
  |── PyMuPDF (PDF parsing)
  |── fpdf2 (PDF report generation)
  |
  ^── (shared DB + service imports)
  |
grant-context-mcp  (optional, stdio)
  |
Claude Desktop / MCP Client
```

---

## Backend layers

```
app/api/          Route handlers — thin; delegate everything to services
app/services/     Business logic — keep focused and testable
  analysis_service.py    Orchestrates the full analysis pipeline
  grant_extractor.py     Extracts requirements from grant documents (Claude)
  evidence_matcher.py    Matches evidence chunks to requirements (Claude + RAG)
  readiness_scorer.py    Deterministic scoring — no LLM
  application_drafter.py Drafts narrative answers (Claude)
  report_generator.py    Generates PDF report (fpdf2)
  embedding_service.py   TF-IDF or OpenAI embeddings for RAG
  document_service.py    Upload, parse, chunk, delete documents
  storage_service.py     File persistence abstraction (local disk / swap for S3)
  seed.py                Demo data seeding on startup
app/models/       SQLAlchemy ORM models
app/schemas/      Pydantic request/response types
app/core/         Config, security, database, rate limiting, LLM client
```

---

## AI Pipeline

The analysis pipeline is staged and provenance-tracked:

```
1. embed_chunks_for_project()     TF-IDF (default) or OpenAI embeddings
2. extract_requirements()         Claude → structured JSON grant requirements
3. match_all_requirements()       Claude per-requirement evidence evaluation
4. compute_scores()               Deterministic weighted average — no LLM
5. generate_risk_flags()          Deterministic from match statuses
6. generate_missing_documents()   Deterministic from required_document reqs
7. draft_answers()                Claude per-narrative-question drafting
8. _upsert_report()               Persist to ReadinessReport with analysis_source
```

`analysis_source` on every result tells the caller (and the UI/MCP) whether results
came from `"real_pipeline"`, `"fallback_mock"`, or `"seeded_demo"`. The fallback path
returns deterministic BrightPath demo data when AI or upload conditions aren't met.

---

## MCP Server (optional)

The `grant-context-mcp` server exposes five tools to Claude agents:

| Tool | What it does |
|---|---|
| `parse_grant_requirements` | Returns extracted requirements for a project |
| `extract_nonprofit_profile` | Returns org profile + document inventory |
| `match_requirement_to_evidence` | Returns (or computes) evidence match for one requirement |
| `generate_readiness_checklist` | Returns scores, flags, missing docs, and provenance |
| `generate_packet` | Generates and returns the PDF report path |

**Key design decisions:**
- The MCP server imports backend service functions directly (no HTTP) — it shares the same process space as the backend when run locally
- It is entirely read-mostly; all mutations go through the backend (analysis is triggered via `POST /analyze`, not via MCP)
- All IDs are validated before any DB access — blocks path traversal and injection
- Outputs never include environment variables, API keys, or absolute file paths
- The server is **optional** — the web app works identically with or without it

**When to use the MCP layer:** for agent-driven workflows where Claude needs to autonomously inspect a project, evaluate specific requirements, and generate a report without a human clicking through the UI. The web app is the primary product; MCP is the advanced integration layer.

See `mcp/grant-context-mcp/README.md` for full tool docs, Claude Desktop config, and the example agent workflow.

---

## File Storage

Uploaded documents and generated PDFs are stored via `storage_service.py`, which abstracts the storage backend behind four functions:

| Function | Purpose |
|---|---|
| `save_file()` | Persist an uploaded document; returns storage_url |
| `save_report()` | Persist a generated PDF; returns storage_url |
| `get_file_path()` | Resolve storage_url → absolute Path (local only) |
| `file_exists()` | Check whether storage_url resolves to an existing file |

The current implementation uses local disk (`uploads/{project_id}/`). Swap all four functions to migrate to S3 or Supabase Storage without changing any other code.

---

## Auth

- JWT-based, signed with `JWT_SECRET`
- Bearer token required on all non-health routes
- Row-level ownership: every project/org/document query is scoped to the authenticated user
- Rate limiting on auth endpoints (in-memory; replace with Redis for multi-instance)

---

## Database

- **Dev:** SQLite (created by `create_all_tables()` on startup)
- **Production:** Postgres 16+ (schema managed by Alembic)
- Migration flow: `alembic upgrade head` runs in `entrypoint.sh` before uvicorn starts

Current migration history:
- `0001` — initial schema
- `0002` — user auth and project ownership
- `0003` — analysis summary fields
- `0004` — `analysis_source` and `fallback_reason` on `readiness_reports`
