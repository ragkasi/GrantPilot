# Grant Requirement Extraction Skill

## Purpose

Extract structured requirements from a grant opportunity document.

## When to Use

Use this skill when implementing or reviewing code that parses a grant description, RFP, NOFO, application form, or grant guideline document.

## Output Schema

The output should include:

- grant_name
- funder_name
- deadline
- eligibility_requirements
- required_documents
- budget_requirements
- narrative_questions
- evaluation_criteria
- compliance_requirements
- geographic_restrictions
- population_restrictions
- risk_flags

## Rules

- Separate hard requirements from preferences.
- Preserve original wording where useful.
- Mark uncertain requirements as uncertain.
- Do not infer deadlines unless stated.
- Return structured JSON.