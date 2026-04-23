# GrantPilot Data Model

## Core Entities

GrantPilot uses the following main entities:

- User
- Organization
- Project
- Document
- DocumentChunk
- GrantRequirement
- EvidenceMatch
- ReadinessReport

## User

Represents an authenticated user.

Fields:

- id
- email
- created_at

## Organization

Represents a nonprofit organization.

Fields:

- id
- user_id
- name
- mission
- location
- nonprofit_type
- annual_budget
- population_served
- created_at
- updated_at

## Project

Represents one grant application workflow.

Fields:

- id
- organization_id
- grant_name
- grant_source_url
- status
- created_at
- updated_at

Possible statuses:

- draft
- documents_uploaded
- analyzing
- analyzed
- report_generated
- error

## Document

Represents an uploaded document.

Fields:

- id
- organization_id
- project_id
- type
- filename
- storage_url
- parsed_text
- page_count
- created_at

Document types:

- mission_statement
- budget
- annual_report
- program_description
- irs_letter
- past_application
- grant_opportunity
- other

## DocumentChunk

Represents a searchable chunk of a document.

Fields:

- id
- document_id
- chunk_text
- page_number
- chunk_index
- embedding
- metadata
- created_at

## GrantRequirement

Represents a requirement extracted from a grant document.

Fields:

- id
- project_id
- requirement_type
- requirement_text
- importance
- source_document_id
- source_page_number
- created_at

Requirement types:

- eligibility
- required_document
- budget
- narrative
- impact
- geography
- population
- compliance
- deadline

Importance values:

- required
- preferred
- optional
- unknown

## EvidenceMatch

Represents evidence from nonprofit documents that supports or fails to support a requirement.

Fields:

- id
- requirement_id
- document_chunk_id
- status
- match_score
- explanation
- created_at

Status values:

- satisfied
- partially_satisfied
- not_satisfied
- unclear

## ReadinessReport

Represents the generated analysis report.

Fields:

- id
- project_id
- eligibility_score
- readiness_score
- missing_items
- risk_flags
- draft_answers
- report_pdf_url
- created_at

## Citation Format

Every citation should include:

- document_id
- document_name
- page_number
- chunk_id
- short_summary

Example:

```json
{
  "document_name": "Program Description.pdf",
  "page_number": 2,
  "summary": "Describes STEM mentoring program for low-income middle school students."
}