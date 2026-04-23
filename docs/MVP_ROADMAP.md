# GrantPilot MVP Roadmap

## Phase 0: Project Setup

- Create monorepo structure
- Set up frontend
- Set up backend
- Set up database
- Add Docker Compose
- Add environment variable templates
- Add basic README

## Phase 1: Mocked Frontend Demo

Goal:

Create a polished UI using mocked data.

Tasks:

- Login page
- Dashboard page
- Organization page
- Project creation page
- Analysis results page
- Mock eligibility score
- Mock readiness score
- Mock checklist
- Mock draft answers
- Mock PDF download button

Success:

A reviewer can understand the product before the backend is complete.

## Phase 2: Backend Core

Goal:

Create backend APIs and database models.

Tasks:

- Organization CRUD
- Project CRUD
- Document upload route
- Document metadata storage
- Project analysis route placeholder
- Report retrieval route placeholder

Success:

Frontend can talk to backend with real data.

## Phase 3: Document Processing

Goal:

Parse and store uploaded documents.

Tasks:

- PDF parsing
- Text extraction
- Chunking
- Page number tracking
- Embedding generation
- pgvector storage

Success:

Uploaded documents become searchable evidence.

## Phase 4: Grant Analysis

Goal:

Extract grant requirements and match evidence.

Tasks:

- Grant requirement extraction
- Nonprofit profile extraction
- Requirement-to-evidence retrieval
- Evidence satisfaction evaluation
- Missing document checklist
- Risk flag generation

Success:

The app can produce real analysis from uploaded documents.

## Phase 5: Drafting and Report

Goal:

Generate useful final outputs.

Tasks:

- Draft application answers
- Add citations
- Generate report data
- Render PDF
- Add download flow

Success:

User can download a complete readiness packet.

## Phase 6: MCP Integration

Goal:

Expose grant workflow tools through MCP.

Tasks:

- Set up grant-context-mcp
- Add parse_grant_requirements
- Add extract_nonprofit_profile
- Add match_requirement_to_evidence
- Add checklist generation
- Add packet generation

Success:

The project demonstrates an advanced agent/tooling architecture.