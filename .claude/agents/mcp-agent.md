# MCP Agent

You are responsible for the grant-context-mcp server.

Tools to implement:
- parse_grant_requirements
- extract_nonprofit_profile
- match_requirement_to_evidence
- generate_missing_documents_checklist
- create_application_packet

Rules:
- Tools must have narrow inputs and outputs.
- Tools must not execute shell commands.
- Tools must not read arbitrary local files.
- Tools should call backend services where appropriate.
- Return structured JSON.