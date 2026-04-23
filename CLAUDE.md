# GrantPilot Claude Instructions

## Project Summary

GrantPilot is an AI grant eligibility and application assistant for small nonprofits. Users upload nonprofit documents and a grant opportunity. The system extracts requirements, checks eligibility, matches evidence from uploaded documents, drafts first-pass answers with citations, and generates a grant readiness packet PDF.

This is not a generic chatbot. All AI outputs must be grounded in uploaded documents or clearly labeled as assumptions.

## Core Product Goals

1. Help small nonprofits understand whether they are eligible for a grant.
2. Identify missing documents and weak application sections.
3. Generate evidence-backed draft grant answers.
4. Produce a downloadable grant readiness report.
5. Keep the MVP demo simple, reliable, and deployable.

## MVP Scope

Build the following first:

- User authentication
- Organization profile creation
- Document upload
- PDF parsing
- Grant requirement extraction
- Evidence matching using RAG
- Eligibility/readiness scoring
- Draft answer generation with citations
- Downloadable report PDF

Do not build public web grant scraping until the upload-based grant flow works.

## Tech Stack

Frontend:
- Next.js
- TypeScript
- Tailwind
- shadcn/ui if useful

Backend:
- FastAPI
- Python
- Postgres
- pgvector
- PyMuPDF
- Pydantic
- SQLAlchemy or SQLModel

AI:
- Claude or OpenAI API
- Structured JSON outputs wherever possible
- RAG over nonprofit documents and grant documents

MCP:
- Local MCP server named grant-context-mcp
- Expose narrow tools for grant requirement parsing, profile extraction, evidence matching, checklist generation, and packet creation

## Architecture Rules

- Keep frontend, backend, and MCP code separated.
- Backend owns business logic.
- Frontend should not call AI APIs directly.
- All generated answers must include citations to document chunks when possible.
- Store document chunks with page numbers and document metadata.
- Prefer deterministic functions for scoring instead of asking the LLM to invent a score.
- Use structured JSON schemas for AI outputs.
- Never silently hallucinate nonprofit facts.

## Coding Standards

- Use TypeScript types for all frontend API responses.
- Use Pydantic schemas for all backend request and response models.
- Add tests for parsers, scoring logic, and API routes.
- Keep service files small and focused.
- Prefer explicit names over clever abstractions.
- Add comments only where logic is non-obvious.

## AI Output Rules

When generating grant-related outputs:

- Cite source document name and page number.
- Use "Not found in uploaded documents" when evidence is missing.
- Separate hard eligibility requirements from nice-to-have preferences.
- Flag uncertainty.
- Do not claim legal, tax, or grant compliance certainty.
- Treat generated grant answers as drafts, not final submissions.

## Security Rules

- Validate uploaded file types.
- Limit file sizes.
- Do not execute uploaded content.
- Do not expose raw prompts or API keys.
- Do not allow the MCP server to access arbitrary files.
- Do not allow MCP tools to run shell commands.
- Use environment variables for secrets.
- Add rate limits where practical.

## Development Workflow

For each feature:

1. Read relevant docs in /docs.
2. Propose a short implementation plan.
3. Update backend schema/API if needed.
4. Update frontend types and UI.
5. Add or update tests.
6. Run lint/typecheck/tests.
7. Summarize what changed and what remains.

## Demo Priority

The demo should feel polished even if the backend is simple.

The core demo page should show:

- Grant name
- Eligibility score
- Readiness score
- Missing documents
- Requirement evidence table
- Draft answers
- Risk flags
- Download report button