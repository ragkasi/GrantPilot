# Review PR Command

Review the current changes as if this is a pull request.

## Review Areas

Check:

- Correctness
- API contract consistency
- Type safety
- Database model consistency
- Frontend/backend integration
- AI grounding
- Citation handling
- Security
- Test coverage
- Demo quality

## GrantPilot-Specific Checks

Verify:

- AI outputs do not invent nonprofit facts.
- Draft answers include citations when evidence exists.
- Missing evidence is clearly labeled.
- Hard requirements affect eligibility score.
- Preferred requirements affect readiness score only.
- Uploaded documents are treated as untrusted content.
- Frontend does not call AI APIs directly.
- Backend validates user ownership.
- MCP tools are narrow and safe.

## Output Format

Return:

1. Critical issues
2. Medium issues
3. Low-priority improvements
4. Suggested next steps