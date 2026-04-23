# RAG Evaluation Skill

## Purpose

Evaluate whether retrieval results are useful, grounded, and correctly cited.

## Checks

- Did retrieval return chunks relevant to the requirement?
- Are page numbers included?
- Are citations attached to generated claims?
- Are unsupported claims clearly marked?
- Is the confidence score reasonable?
- Are missing documents detected?

## Output

Return:
- pass/fail
- issues
- recommended fixes