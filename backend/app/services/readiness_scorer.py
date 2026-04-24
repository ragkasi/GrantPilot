"""Deterministic scoring — no LLM involvement.

All scores are computed from evidence match statuses using fixed weights.
The LLM never decides a score; it only evaluates individual evidence matches.
This ensures scores are reproducible and auditable.
"""
from app.models.analysis import EvidenceMatch, GrantRequirement
from app.schemas.analysis import Citation, MissingDocument, RiskFlag

# ---------------------------------------------------------------------------
# Score weights per status
# ---------------------------------------------------------------------------

_STATUS_WEIGHT: dict[str, float] = {
    "satisfied": 1.0,
    "partially_satisfied": 0.5,
    "unclear": 0.25,
    "not_satisfied": 0.0,
}

# Eligibility-relevant requirement types (used for the eligibility sub-score)
_ELIGIBILITY_TYPES = {"eligibility", "required_document"}


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def compute_scores(
    requirements: list[GrantRequirement],
    matches: dict[str, EvidenceMatch],
) -> tuple[int, int]:
    """Return (eligibility_score, readiness_score) as integers in [0, 100].

    eligibility_score — weighted average over required eligibility + required_document reqs
    readiness_score  — weighted average over ALL required requirements
    """
    required = [r for r in requirements if r.importance == "required"]

    eligibility_reqs = [r for r in required if r.requirement_type in _ELIGIBILITY_TYPES]
    eligibility_score = _weighted_score(eligibility_reqs, matches) if eligibility_reqs else _weighted_score(required, matches)
    readiness_score = _weighted_score(required, matches)

    return eligibility_score, readiness_score


def generate_risk_flags(
    requirements: list[GrantRequirement],
    matches: dict[str, EvidenceMatch],
) -> list[RiskFlag]:
    """Produce risk flags deterministically from match statuses."""
    flags: list[RiskFlag] = []

    for req in requirements:
        if req.importance != "required":
            continue
        match = matches.get(req.id)
        if match is None:
            continue

        short_text = req.requirement_text[:80] + ("…" if len(req.requirement_text) > 80 else "")
        explanation = (match.explanation or "")[:200]

        if match.status == "not_satisfied":
            flags.append(
                RiskFlag(
                    severity="high",
                    title=_flag_title(req.requirement_type, "not satisfied"),
                    description=explanation or f"No evidence found for: {short_text}",
                )
            )
        elif match.status == "partially_satisfied":
            flags.append(
                RiskFlag(
                    severity="medium",
                    title=_flag_title(req.requirement_type, "partially satisfied"),
                    description=explanation or f"Incomplete evidence for: {short_text}",
                )
            )
        elif match.status == "unclear":
            flags.append(
                RiskFlag(
                    severity="medium",
                    title=_flag_title(req.requirement_type, "unclear evidence"),
                    description=explanation or f"Evidence is ambiguous for: {short_text}",
                )
            )

    return flags


def generate_missing_documents(
    requirements: list[GrantRequirement],
    matches: dict[str, EvidenceMatch],
) -> list[MissingDocument]:
    """Identify required_document requirements that are not satisfied."""
    missing: list[MissingDocument] = []

    for req in requirements:
        if req.requirement_type != "required_document":
            continue
        match = matches.get(req.id)
        if match is None or match.status in ("not_satisfied", "unclear"):
            # Strip the "Applicant must provide: " prefix added during extraction
            doc_name = req.requirement_text.removeprefix("Applicant must provide: ").strip()
            explanation = (match.explanation if match else "Document not found in uploaded materials.")[:300]
            missing.append(
                MissingDocument(
                    name=doc_name,
                    required=req.importance == "required",
                    description=explanation,
                )
            )

    return missing


def build_requirement_results(
    requirements: list[GrantRequirement],
    match_results: dict[str, tuple[EvidenceMatch, list[Citation]]],
) -> list[dict]:
    """Build the list[RequirementResult] dicts for storage in ReadinessReport.requirements."""
    results = []
    for req in requirements:
        ev_match, citations = match_results.get(req.id, (None, []))
        results.append(
            {
                "id": req.id,
                "text": req.requirement_text,
                "type": req.requirement_type,
                "importance": req.importance,
                "status": ev_match.status if ev_match else "unclear",
                "confidence": round(ev_match.match_score if ev_match else 0.0, 4),
                "evidence": [c.model_dump() for c in citations],
            }
        )
    return results


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _weighted_score(reqs: list[GrantRequirement], matches: dict[str, EvidenceMatch]) -> int:
    if not reqs:
        return 50  # neutral default when no requirements of that type exist
    total = sum(_STATUS_WEIGHT.get(matches[r.id].status, 0.0) for r in reqs if r.id in matches)
    unmatched = sum(1 for r in reqs if r.id not in matches)
    denominator = len(reqs)
    # Unmatched requirements count as 0 (no evidence = worst case)
    return round(100 * total / denominator)


_TYPE_LABELS: dict[str, str] = {
    "eligibility": "Eligibility requirement",
    "required_document": "Required document",
    "budget": "Budget requirement",
    "narrative": "Narrative question",
    "impact": "Impact requirement",
    "geography": "Geographic requirement",
    "population": "Population requirement",
    "compliance": "Compliance requirement",
    "deadline": "Deadline requirement",
}


def _flag_title(req_type: str, status_phrase: str) -> str:
    label = _TYPE_LABELS.get(req_type, req_type.replace("_", " ").title())
    return f"{label} {status_phrase}"
