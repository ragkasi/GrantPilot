# grant-context-mcp

MCP server that exposes GrantPilot's grant-analysis capabilities as structured tools
for Claude agents. The server reads directly from the GrantPilot database and reuses
the existing backend service layer — it does not duplicate any logic.

## What it does

An agent connected to this server can:

- Read extracted grant requirements for any analyzed project
- Get a full nonprofit profile and document inventory
- Match a single requirement against uploaded evidence
- Get a complete readiness checklist with scores, flags, and missing docs
- Generate and retrieve the grant readiness PDF packet

## Tools

### `parse_grant_requirements(project_id)`

Returns the structured grant requirements already extracted for a project.

**Input**: `project_id` — GrantPilot project ID (e.g. `proj_stem_2026`)

**Output**:
```json
{
  "project_id": "proj_stem_2026",
  "grant_name": "Community STEM Access Fund",
  "requirement_count": 10,
  "requirements": [
    {
      "id": "req_xxx",
      "text": "Applicant must be a registered 501(c)(3) nonprofit.",
      "type": "eligibility",
      "importance": "required"
    }
  ],
  "hint": ""
}
```

> Run `POST /projects/{id}/analyze` in the backend first to populate requirements.

---

### `extract_nonprofit_profile(project_id)`

Returns the organization profile and uploaded document inventory for a project.

**Input**: `project_id`

**Output**:
```json
{
  "project_id": "proj_stem_2026",
  "organization": {
    "id": "org_brightpath",
    "name": "BrightPath Youth Foundation",
    "mission": "...",
    "location": "Columbus, Ohio",
    "nonprofit_type": "501(c)(3)",
    "annual_budget": 420000,
    "population_served": "..."
  },
  "project": {
    "grant_name": "Community STEM Access Fund",
    "funder_name": "Ohio Community Foundation",
    "deadline": "May 15, 2026",
    "status": "analyzed"
  },
  "documents": [
    {"id": "doc_xxx", "filename": "mission.pdf", "type": "mission_statement", "status": "parsed", "page_count": 2}
  ],
  "document_type_summary": {"mission_statement": 1, "annual_report": 1}
}
```

---

### `match_requirement_to_evidence(project_id, requirement_id)`

Retrieves or computes the evidence match for one grant requirement.

Returns a cached `EvidenceMatch` row if one exists from a prior analysis run.
If none exists, runs live evidence matching (requires `ANTHROPIC_API_KEY`).

**Input**: `project_id`, `requirement_id` (from `parse_grant_requirements`)

**Output**:
```json
{
  "requirement_id": "req_xxx",
  "requirement_text": "Applicant must be a registered 501(c)(3) nonprofit.",
  "status": "satisfied",
  "confidence": 0.88,
  "explanation": "The mission statement document confirms 501(c)(3) status.",
  "citations": [
    {"document_name": "mission.pdf", "page_number": 1, "summary": "..."}
  ],
  "missing_evidence": [],
  "source": "cached"
}
```

---

### `generate_readiness_checklist(project_id)`

Returns the full readiness checklist from the stored analysis.

**Input**: `project_id`

**Output**:
```json
{
  "project_id": "proj_stem_2026",
  "grant_name": "Community STEM Access Fund",
  "eligibility_score": 82,
  "readiness_score": 74,
  "requirements_summary": {
    "total": 10,
    "satisfied": 7,
    "partial": 1,
    "not_met": 2,
    "unclear": 0
  },
  "missing_documents": [...],
  "risk_flags": [...],
  "requirements": [...]
}
```

---

### `generate_packet(project_id)`

Generates the PDF grant readiness report (or returns the cached file).

**Input**: `project_id`

**Output**:
```json
{
  "project_id": "proj_stem_2026",
  "report_pdf_url": "proj_stem_2026/report.pdf",
  "file_size_bytes": 42048,
  "download_endpoint": "/projects/proj_stem_2026/report/download",
  "summary": {
    "eligibility_score": 82,
    "readiness_score": 74,
    "missing_doc_count": 2,
    "high_risk_count": 1
  }
}
```

> The `download_endpoint` is served by the backend API at `http://localhost:8000`.

---

## Running locally

### Prerequisites

- Python 3.11+
- GrantPilot backend installed (the MCP server imports from `backend/app/`)
- Backend DB seeded (run the FastAPI backend at least once to trigger `seed_demo()`)

### Install

```bash
cd mcp/grant-context-mcp
pip install mcp[cli] sqlalchemy pydantic-settings anthropic pymupdf fpdf2
```

### Start the MCP server

```bash
cd mcp/grant-context-mcp
python server.py
```

The server runs over **stdio** (standard for Claude Desktop and MCP clients).

### Environment variables

Set these before starting (or use a `.env` file in `backend/`):

```
ANTHROPIC_API_KEY=sk-...          # Required for live evidence matching and drafting
DATABASE_URL=sqlite:///./grantpilot.db  # Defaults to SQLite dev DB in backend/
```

---

## Claude Desktop configuration

Add this to `~/Library/Application Support/Claude/claude_desktop_config.json`
(macOS) or `%APPDATA%/Claude/claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "grant-context": {
      "command": "python",
      "args": ["/absolute/path/to/grantpilot/mcp/grant-context-mcp/server.py"],
      "env": {
        "ANTHROPIC_API_KEY": "your-key-here",
        "DATABASE_URL": "sqlite:////absolute/path/to/grantpilot/backend/grantpilot.db"
      }
    }
  }
}
```

See `claude_desktop_config.json` in this directory for a template.

---

## Running tests

```bash
cd mcp/grant-context-mcp
PYTHONPATH=. python -m pytest tests/ -v
```

Tests call tool functions directly (not via MCP protocol) with an in-memory SQLite DB.
This tests all business logic without requiring a live MCP client.

---

## Architecture

```
Claude Desktop / MCP Client
        |
        | stdio (JSON-RPC)
        v
grant-context-mcp/server.py
        |
        | direct Python import
        v
backend/app/services/
  grant_extractor.py
  evidence_matcher.py
  readiness_scorer.py
  report_generator.py
  analysis_service.py
        |
        v
backend/app/models/ (SQLAlchemy)
        |
        v
SQLite / Postgres DB
```

## Security

- All IDs validated with `_validate_id()` — blocks path traversal, shell injection, spaces, and oversized values before any DB call
- No file paths accepted as inputs — only `project_id` and `requirement_id` strings
- Storage URLs in outputs are always relative (never absolute paths)
- Environment variables and secrets are never included in tool responses
- Document content is treated as data, not instructions (enforced in backend prompts)
- The server never executes shell commands

## How it fits into GrantPilot

The MCP server is an **advanced layer** on top of the existing backend. The FastAPI backend is the primary product; the MCP server enables agent-driven workflows where Claude can autonomously:

1. Inspect what documents a nonprofit has uploaded
2. Check which grant requirements are satisfied
3. Match specific requirements to evidence
4. Generate a grant readiness report

This is the Phase 6 of the GrantPilot MVP roadmap.
