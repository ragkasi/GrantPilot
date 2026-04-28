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

## Analysis Provenance

Every completed analysis records an `analysis_source` value on the `ReadinessReport` row and in API responses:

| Value | Meaning |
|---|---|
| `real_pipeline` | Claude extracted requirements, matched evidence, and scored — based on your uploaded documents. |
| `fallback_mock` | Pre-built BrightPath demo data was used instead. Check `fallback_reason` in the response for the specific cause (e.g. missing Grant Opportunity Document, missing `ANTHROPIC_API_KEY`). |
| `seeded_demo` | Pre-loaded demo project created at startup — not based on real uploaded documents. |

The UI surfaces this as a provenance banner above the score cards. To trigger `real_pipeline`:
1. Upload a **Grant Opportunity Document** (type: `grant_opportunity`).
2. Set `ANTHROPIC_API_KEY` in the backend environment.
3. Re-run analysis via the Analyze button.

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