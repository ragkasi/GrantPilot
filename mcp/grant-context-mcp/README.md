# grant-context-mcp

MCP server that exposes GrantPilot's grant-analysis capabilities as structured tools
for Claude agents. The server reads directly from the GrantPilot database and reuses
the existing backend service layer — it does not duplicate any logic.

## What it does

An agent connected to this server can:

- Read extracted grant requirements for any analyzed project
- Get a full nonprofit profile and document inventory
- Match a single requirement against uploaded evidence
- Get a complete readiness checklist with scores, flags, and provenance
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
    "grant_amount": "$50,000 - $150,000",
    "status": "analyzed"
  },
  "documents": [
    {
      "id": "doc_xxx",
      "filename": "mission.pdf",
      "type": "mission_statement",
      "status": "parsed",
      "page_count": 2
    }
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

`source` is `"cached"` when returning a stored match, `"live"` when matching runs fresh.

---

### `generate_readiness_checklist(project_id)`

Returns the full readiness checklist from the stored analysis, including provenance.

**Input**: `project_id`

**Output**:
```json
{
  "project_id": "proj_stem_2026",
  "grant_name": "Community STEM Access Fund",
  "funder_name": "Ohio Community Foundation",
  "deadline": "May 15, 2026",
  "eligibility_score": 82,
  "readiness_score": 74,
  "analysis_source": "seeded_demo",
  "fallback_reason": null,
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

`analysis_source` values:
- `"real_pipeline"` — Claude extracted requirements and matched evidence from uploaded docs
- `"fallback_mock"` — sample data shown; check `fallback_reason` for why
- `"seeded_demo"` — pre-loaded demo project data
- `null` — legacy row (created before provenance tracking was added)

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

`report_pdf_url` is always a relative path — never an absolute file-system path.
The `download_endpoint` is served by the backend API (authenticated).

---

## Example agent workflow

This shows what a Claude agent session looks like with this MCP server connected.
The agent can call tools in sequence to analyze a grant project autonomously.

**Prompt to Claude:**
> "Analyze the grant readiness for project proj_stem_2026 and tell me what's missing."

**Claude's tool calls (in order):**

1. `extract_nonprofit_profile("proj_stem_2026")`
   → returns org name, mission, uploaded documents, project status

2. `generate_readiness_checklist("proj_stem_2026")`
   → returns scores (82 eligibility, 74 readiness), missing docs, risk flags, analysis_source

3. `parse_grant_requirements("proj_stem_2026")`
   → returns list of extracted requirements with IDs

4. `match_requirement_to_evidence("proj_stem_2026", "req_xxx")`
   → returns status, explanation, and citations for a specific requirement

5. `generate_packet("proj_stem_2026")`
   → generates PDF and returns download path

**Example Claude response (grounded in tool outputs):**
> "BrightPath Youth Foundation has an eligibility score of 82/100 and a readiness score of 74/100 for the Community STEM Access Fund. The main gaps are:
> 1. IRS Determination Letter is missing (required document)
> 2. Board member list was not uploaded
> The analysis was generated from real AI extraction (analysis_source: real_pipeline). I've generated the readiness PDF at `proj_stem_2026/report.pdf` — download it via GET /projects/proj_stem_2026/report/download."

---

## Running locally

### Prerequisites

- Python 3.11+
- GrantPilot backend installed (the MCP server imports from `backend/app/`)
- Backend DB seeded (run the FastAPI backend at least once to trigger `seed_demo()`)

### Install

```bash
cd mcp/grant-context-mcp
pip install "mcp[cli]" sqlalchemy pydantic-settings anthropic pymupdf fpdf2
```

### Start the MCP server

```bash
cd mcp/grant-context-mcp
python server.py
```

The server runs over **stdio** (standard for Claude Desktop and MCP clients).

### Environment variables

Set these before starting, or create a `.env` file in `backend/`:

| Variable | Required | Default | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | For live matching | — | Required for `match_requirement_to_evidence` without cached results |
| `DATABASE_URL` | No | `sqlite:///./grantpilot.db` | Must point to the same DB as the backend |
| `UPLOAD_DIR` | No | `uploads` | Must match the backend's `UPLOAD_DIR` |

The `.env.example` in this directory has a ready-to-use template for local dev.

---

## Claude Desktop configuration

Add this block to your Claude Desktop config file.

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "grant-context": {
      "command": "python",
      "args": ["/absolute/path/to/grantpilot/mcp/grant-context-mcp/server.py"],
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-...",
        "DATABASE_URL": "sqlite:////absolute/path/to/grantpilot/backend/grantpilot.db",
        "UPLOAD_DIR": "/absolute/path/to/grantpilot/backend/uploads"
      }
    }
  }
}
```

> See `claude_desktop_config.json` in this directory for a copy-paste template.

**Windows paths** use forward slashes in the JSON value:
```
"DATABASE_URL": "sqlite:////C:/Users/YourName/grantpilot/backend/grantpilot.db"
```

After saving the config, restart Claude Desktop. You should see `grant-context` in
the tools panel (hammer icon). Ask Claude: *"Use the grant-context tools to analyze
project proj_stem_2026."*

---

## Running tests

```bash
cd mcp/grant-context-mcp
python -m pytest tests/ -v
```

Tests call tool functions directly (not via MCP protocol) with an in-memory SQLite DB.
This tests all business logic without requiring a live MCP client or Claude Desktop.

**Coverage:**
- ID validation (path traversal, shell injection, empty/oversized input)
- `parse_grant_requirements` — schema, error cases
- `extract_nonprofit_profile` — output fields, secrets not leaked
- `generate_readiness_checklist` — scores, flags, provenance fields
- `match_requirement_to_evidence` — cached path, wrong-project rejection, invalid IDs
- `generate_packet` — PDF generation, relative paths only, caching

---

## Architecture

```
Claude Desktop / MCP Client
        |
        | stdio (JSON-RPC 2.0)
        v
grant-context-mcp/server.py   (this server)
        |
        | direct Python import — no HTTP round-trip
        v
backend/app/services/
  analysis_service.py       read ReadinessReport
  evidence_matcher.py       live evidence matching
  report_generator.py       PDF generation
  storage_service.py        file path resolution
        |
        v
backend/app/models/           SQLAlchemy ORM
        |
        v
SQLite (local dev) / Postgres (production)
```

The MCP server is a **read-mostly** layer. It does not own any business logic —
it delegates entirely to the backend service layer. The FastAPI web app and the
MCP server share the same DB and the same service functions.

---

## Security

- All IDs validated with `_validate_id()` — blocks path traversal, shell injection, spaces, and oversized values before any DB call
- No file paths accepted as inputs — only `project_id` and `requirement_id` strings
- Storage URLs in outputs are always relative (never absolute paths)
- Environment variables and secrets are never included in tool responses
- Document content is treated as untrusted data (enforced by backend service prompts)
- The server never executes shell commands or reads arbitrary files

## How it fits into GrantPilot

The MCP server is an **optional advanced layer** on top of the main product. The FastAPI
web app is the primary interface; the MCP server enables agent-driven workflows where
Claude can autonomously inspect a project, evaluate evidence, and generate a report
without manual UI interaction.

It is intentionally minimal: five tools, no state of its own, no duplicated logic.
Everything an agent can do via MCP, a user can also do via the web app.
