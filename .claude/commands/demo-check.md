# Demo Check Command

Evaluate whether the app is ready for a portfolio demo.

## Checklist

### Core Flow

- User can sign in.
- User can create an organization.
- User can create a grant project.
- User can upload nonprofit documents.
- User can upload a grant opportunity.
- User can run analysis.
- User can view results.
- User can download a report.

### Analysis Output

- Eligibility score is visible.
- Readiness score is visible.
- Missing documents are visible.
- Risk flags are visible.
- Requirement checklist is visible.
- Evidence citations are visible.
- Draft answers are visible.

### UX Quality

- Loading states exist.
- Error states exist.
- Empty states exist.
- Results page is readable.
- Demo data is polished.
- UI does not look unfinished.

### Technical Quality

- Backend tests pass.
- Frontend lint passes.
- Typecheck passes.
- No API keys are exposed.
- Uploaded files are validated.
- AI outputs are structured.

## Output Format

Return:

- Demo readiness: Pass / Partial / Fail
- Blocking issues
- Nice-to-have fixes
- Recommended next 3 tasks