# GrantPilot Development Process

## Default Feature Process

For every new feature:

1. Define the user-facing behavior.
2. Define the backend API contract.
3. Define the database changes.
4. Implement backend service logic.
5. Implement frontend UI.
6. Add tests.
7. Run validation.
8. Update documentation.

## AI Feature Process

For every AI feature:

1. Define the input schema.
2. Define the output schema.
3. Write the prompt.
4. Add a parser/validator for the output.
5. Add fallback behavior for invalid JSON.
6. Add tests using sample documents.
7. Add citations wherever evidence is used.

## RAG Process

1. Parse uploaded document.
2. Split into chunks.
3. Store chunk text, page number, document type, and embedding.
4. Retrieve top chunks for each grant requirement.
5. Ask the model to determine whether the chunks satisfy the requirement.
6. Store evidence matches.
7. Show citations in the UI.

## Report Generation Process

1. Gather project metadata.
2. Gather scores.
3. Gather requirements and evidence.
4. Gather missing items.
5. Gather risk flags.
6. Gather draft answers.
7. Render HTML or Markdown.
8. Convert to PDF.
9. Save PDF URL.