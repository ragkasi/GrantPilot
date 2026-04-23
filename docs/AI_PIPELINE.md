# GrantPilot AI Pipeline

## Pipeline Overview

GrantPilot uses a multi-step AI workflow:

1. Parse nonprofit documents.
2. Parse grant opportunity.
3. Extract structured grant requirements.
4. Extract nonprofit profile.
5. Match grant requirements to nonprofit evidence.
6. Score eligibility and readiness.
7. Draft grant responses.
8. Generate final packet.

## Requirement Types

- Eligibility
- Required document
- Budget requirement
- Narrative question
- Impact metric
- Geographic restriction
- Population served
- Deadline
- Compliance requirement

## Evidence Match Fields

Each evidence match should include:

- requirement_id
- document_id
- document_name
- page_number
- quote_or_summary
- confidence
- explanation

## Risk Flag Types

- Missing required document
- Weak evidence
- Budget mismatch
- Mission mismatch
- Geography mismatch
- Deadline risk
- Matching funds not found
- Impact metrics not found
- Compliance uncertainty