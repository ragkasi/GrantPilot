# Generate Tests Command

Generate practical tests for the current feature.

## Test Categories

Consider:

- Unit tests
- API route tests
- Service tests
- Parser tests
- Scoring tests
- AI output validation tests
- Frontend component tests if relevant

## Requirements

Tests should:

- Use realistic sample nonprofit and grant data.
- Cover happy paths.
- Cover edge cases.
- Avoid brittle implementation details.
- Validate structured outputs.
- Check that citations are preserved when relevant.

## Important GrantPilot Test Cases

Include tests for:

- Missing required documents
- Unsupported grant requirement
- Partial evidence match
- Invalid file upload
- Empty parsed document
- AI output with invalid JSON
- Requirement with no matching evidence
- Scoring when hard eligibility requirement fails

## Output Format

For each test file:

1. Explain what the test covers.
2. Add or update the test code.
3. Explain how to run the tests.