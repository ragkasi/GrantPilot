# GrantPilot Product Spec

## Product Summary

GrantPilot is an AI-powered grant eligibility and application assistant for small nonprofits. Users upload nonprofit documents and a grant opportunity. The system extracts requirements, checks eligibility, matches evidence from uploaded documents, drafts first-pass answers, and generates a downloadable readiness report.

## Target User

Small nonprofit administrators, founders, program managers, and grant coordinators who do not have dedicated grant-writing staff.

## Core Problem

Small nonprofits often miss funding opportunities because grant applications are long, confusing, and difficult to match against their mission, programs, budget, and impact data.

## MVP Goal

The MVP should help a nonprofit answer one question:

"Are we ready to apply for this grant, and what do we still need?"

## MVP User Flow

1. User signs in.
2. User creates or selects a nonprofit organization.
3. User uploads organization documents.
4. User uploads one grant opportunity.
5. User starts analysis.
6. System extracts grant requirements.
7. System matches nonprofit evidence against each requirement.
8. System generates scores, missing items, risk flags, and draft answers.
9. User downloads a readiness report PDF.

## MVP Features

### Organization Profile

Users can create an organization profile with:

- Organization name
- Mission
- Location
- Main programs
- Population served
- Annual budget
- Contact information

### Document Upload

Users can upload:

- Mission statement
- Annual report
- Budget
- Program description
- IRS determination letter
- Past application
- Grant opportunity document

### Grant Analysis

The system should produce:

- Grant summary
- Eligibility score
- Readiness score
- Requirement checklist
- Missing document checklist
- Risk flags
- Evidence matches
- Draft application answers

### Report Download

The user can download a PDF packet containing the analysis and draft responses.

## Non-Goals for MVP

Do not build these in the first version:

- Public grant search engine
- Automatic grant submission
- Collaboration features
- Payment system
- Advanced CRM
- Real-time grant deadline tracking
- Multi-grant comparison

## Success Criteria

The demo is successful if a user can:

- Upload nonprofit documents
- Upload a grant description
- Run analysis
- View evidence-backed eligibility results
- See missing documents
- Read draft answers
- Download a useful report