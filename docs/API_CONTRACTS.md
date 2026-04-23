# GrantPilot API Contracts

## Organization Routes

### POST /organizations

Creates an organization.

Request:

{
  "name": "BrightPath Youth Foundation",
  "mission": "Provide after-school STEM mentoring.",
  "location": "Columbus, Ohio",
  "nonprofit_type": "501c3",
  "annual_budget": 420000,
  "population_served": "Low-income middle school students"
}

Response:

{
  "id": "org_123",
  "name": "BrightPath Youth Foundation",
  "created_at": "2026-01-01T00:00:00Z"
}

## Project Routes
### POST /projects

Creates a grant project.

Request:

{
  "organization_id": "org_123",
  "grant_name": "Community STEM Access Fund",
  "grant_source_url": "https://example.org/grants/stem"
}

Response:

{
  "id": "project_123",
  "organization_id": "org_123",
  "grant_name": "Community STEM Access Fund",
  "status": "draft"
}

## Document Routes

### POST /documents/upload

Uploads a document.

Form data:

organization_id
project_id
document_type
file

Response:

{
  "id": "doc_123",
  "filename": "program-description.pdf",
  "document_type": "program_description",
  "status": "uploaded"
}

## Analysis Routes
### POST /projects/{project_id}/analyze

Starts grant analysis.

Response:

{
  "project_id": "project_123",
  "status": "analyzing"
}
GET /projects/{project_id}/analysis

Returns grant analysis results.

Response:

{
  "project_id": "project_123",
  "eligibility_score": 82,
  "readiness_score": 74,
  "missing_documents": [
    "IRS determination letter",
    "Board list"
  ],
  "risk_flags": [
    "Matching funds not found in uploaded budget."
  ],
  "requirements": [
    {
      "id": "req_123",
      "text": "Applicant must serve low-income youth in Ohio.",
      "status": "satisfied",
      "confidence": 0.87,
      "evidence": [
        {
          "document_name": "Program Description.pdf",
          "page_number": 2,
          "summary": "Program serves low-income middle school students in Columbus, Ohio."
        }
      ]
    }
  ]
}

## Report Routes

### GET /projects/{project_id}/report

Returns the report metadata and download URL.

Response:

{
  "project_id": "project_123",
  "report_pdf_url": "https://example.com/report.pdf"
}