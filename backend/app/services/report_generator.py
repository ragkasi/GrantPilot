"""
Grant Readiness Report PDF generator.

Uses fpdf2 (pure Python, no system dependencies). The output is a clean,
portfolio-demo-ready PDF packet a nonprofit can share with their team or
hand to a grant writer.

Report structure:
  1. Cover — org name, grant, funder, scores, date
  2. Missing documents checklist
  3. Risk flags
  4. Requirements table with evidence citations
  5. Draft answers with citations
  6. Recommended next steps

Security: internal prompts and raw model outputs are never included.
The PDF contains only analysis results and user-uploaded document citations.
"""
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fpdf import FPDF
from fpdf.enums import XPos, YPos
from sqlalchemy.orm import Session

from app.models.analysis import ReadinessReport
from app.models.organization import Organization
from app.models.project import Project
from app.services import storage_service

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Color palette (matches frontend indigo/violet theme)
# ---------------------------------------------------------------------------
C_INDIGO = (79, 70, 229)
C_INDIGO_LIGHT = (224, 231, 255)  # indigo-100
C_VIOLET = (124, 58, 237)
C_VIOLET_LIGHT = (237, 233, 254)  # violet-100
C_EMERALD = (5, 150, 105)         # green for satisfied
C_AMBER = (180, 113, 3)           # amber for partial
C_RED = (185, 28, 28)             # red for not satisfied
C_GRAY_DARK = (55, 65, 81)        # gray-700
C_GRAY_MID = (107, 114, 128)      # gray-500
C_GRAY_LIGHT = (229, 231, 235)    # gray-200
C_GRAY_BG = (249, 250, 251)       # gray-50
C_WHITE = (255, 255, 255)
C_BLACK = (17, 24, 39)            # gray-900

# Status → (text color, label)  — ASCII only; Helvetica built-in is Latin-1
STATUS_STYLES: dict[str, tuple[tuple[int, int, int], str]] = {
    "satisfied": (C_EMERALD, "[OK] Satisfied"),
    "partially_satisfied": (C_AMBER, "[~] Partial"),
    "not_satisfied": (C_RED, "[X] Not Met"),
    "unclear": (C_GRAY_MID, "[?] Unclear"),
}

SEVERITY_COLORS: dict[str, tuple[int, int, int]] = {
    "high": C_RED,
    "medium": C_AMBER,
    "low": C_EMERALD,
}

PAGE_W = 210  # A4 width mm
MARGIN = 14
CONTENT_W = PAGE_W - 2 * MARGIN

# ---------------------------------------------------------------------------
# Latin-1 text sanitiser (built-in Helvetica only supports Latin-1)
# ---------------------------------------------------------------------------

_LATIN1_MAP = {
    "–": "-", "—": "-",    # en/em dash
    "‘": "'", "'": "'",    # curly single quotes
    "“": '"', "”": '"',    # curly double quotes
    "…": "...",                  # ellipsis
    "→": "->", "↳": ">>",  # arrows
    "✓": "[OK]", "✗": "[X]",
    "·": "-",                    # middle dot
    "•": "-",                    # bullet
}


def _safe(text: str) -> str:
    """Sanitise text for the built-in Latin-1 Helvetica font."""
    for src, dst in _LATIN1_MAP.items():
        text = text.replace(src, dst)
    return text.encode("latin-1", errors="replace").decode("latin-1")


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def generate_and_save(db: Session, project_id: str) -> str:
    """Generate the PDF, persist it under uploads/{project_id}/report.pdf,
    update ReadinessReport.report_pdf_url, and return the storage_url."""
    project = db.get(Project, project_id)
    if project is None:
        raise ValueError(f"Project {project_id} not found.")

    org = db.get(Organization, project.organization_id)
    if org is None:
        raise ValueError(f"Organization for project {project_id} not found.")

    report = (
        db.query(ReadinessReport)
        .filter(ReadinessReport.project_id == project_id)
        .first()
    )
    if report is None:
        raise ValueError(f"No analysis found for project {project_id}. Run /analyze first.")

    pdf_bytes = generate_pdf(project, org, report)

    # Persist under the project's upload directory
    storage_root = Path(storage_service._upload_root())
    project_dir = storage_root / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = project_dir / "report.pdf"
    pdf_path.write_bytes(pdf_bytes)

    # Storage URL is relative to upload_dir
    storage_url = f"{project_id}/report.pdf"
    report.report_pdf_url = storage_url
    db.flush()

    logger.info("Report generated for project %s → %s", project_id, storage_url)
    return storage_url


def generate_pdf(project: Project, org: Organization, report: ReadinessReport) -> bytes:
    """Return raw PDF bytes for the readiness report."""
    pdf = _GrantReportPDF()
    pdf.set_margins(MARGIN, 14, MARGIN)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    _cover_section(pdf, project, org, report)
    _missing_docs_section(pdf, report.missing_items or [])
    _risk_flags_section(pdf, report.risk_flags or [])
    _requirements_section(pdf, report.requirements or [])
    _draft_answers_section(pdf, report.draft_answers or [])
    _next_steps_section(pdf, report.missing_items or [], report.risk_flags or [])

    return bytes(pdf.output())


# ---------------------------------------------------------------------------
# PDF class with header/footer
# ---------------------------------------------------------------------------

class _GrantReportPDF(FPDF):
    """FPDF subclass that auto-sanitises all text to Latin-1 before drawing.
    This prevents UnicodeEncodeError with the built-in Helvetica font."""

    def cell(self, w=0, h=0, text="", *args, **kwargs):  # type: ignore[override]
        return super().cell(w, h, _safe(str(text)), *args, **kwargs)

    def multi_cell(self, w, h=0, text="", *args, **kwargs):  # type: ignore[override]
        return super().multi_cell(w, h, _safe(str(text)), *args, **kwargs)

    def header(self):
        # Thin top rule + branding on every page except page 1
        if self.page_no() == 1:
            return
        self.set_draw_color(*C_GRAY_LIGHT)
        self.set_line_width(0.3)
        self.line(MARGIN, 10, PAGE_W - MARGIN, 10)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*C_INDIGO)
        self.set_y(6)
        self.cell(0, 5, "GrantPilot", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(3)

    def footer(self):
        self.set_y(-13)
        self.set_draw_color(*C_GRAY_LIGHT)
        self.set_line_width(0.3)
        self.line(MARGIN, self.get_y(), PAGE_W - MARGIN, self.get_y())
        self.ln(1)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*C_GRAY_MID)
        disclaimer = "Generated by GrantPilot  ·  Draft only — not a final grant submission"
        self.cell(CONTENT_W - 20, 5, disclaimer, new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.set_font("Helvetica", "", 7)
        self.cell(20, 5, f"Page {self.page_no()}", align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)


# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------

def _cover_section(pdf: FPDF, project: Project, org: Organization, report: ReadinessReport) -> None:
    # Indigo cover block
    pdf.set_fill_color(*C_INDIGO)
    pdf.rect(0, 0, PAGE_W, 52, "F")

    # Report title
    pdf.set_xy(MARGIN, 10)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*C_WHITE)
    pdf.cell(0, 10, "Grant Readiness Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Organization
    pdf.set_xy(MARGIN, 24)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 6, org.name, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Grant info
    pdf.set_xy(MARGIN, 31)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(199, 210, 254)  # indigo-200
    grant_line = project.grant_name
    if project.funder_name:
        grant_line += f"  ·  {project.funder_name}"
    if project.deadline:
        grant_line += f"  ·  Due {project.deadline}"
    pdf.cell(0, 5, grant_line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Date
    pdf.set_xy(MARGIN, 37)
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    pdf.cell(0, 5, f"Generated {today}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_y(56)

    # Score summary — two side-by-side score cards
    _score_card(pdf, MARGIN, 56, 86, report.eligibility_score, "Eligibility Score", C_INDIGO, C_INDIGO_LIGHT)
    _score_card(pdf, MARGIN + 92, 56, 86, report.readiness_score, "Readiness Score", C_VIOLET, C_VIOLET_LIGHT)

    pdf.set_y(100)

    # Quick stats row
    _draw_rule(pdf)
    pdf.ln(3)
    req_count = len(report.requirements or [])
    satisfied = sum(1 for r in (report.requirements or []) if r.get("status") == "satisfied")
    missing_count = len(report.missing_items or [])
    flag_count = len(report.risk_flags or [])

    col_w = CONTENT_W / 3
    stats = [
        (f"{satisfied} / {req_count}", "Requirements Met"),
        (str(missing_count), "Missing Documents"),
        (str(flag_count), "Risk Flags"),
    ]
    pdf.set_font("Helvetica", "B", 18)
    for i, (val, label) in enumerate(stats):
        x = MARGIN + i * col_w
        pdf.set_xy(x, pdf.get_y())
        if label == "Missing Documents" and missing_count > 0:
            pdf.set_text_color(*C_AMBER)
        elif label == "Risk Flags" and flag_count > 0:
            pdf.set_text_color(*C_RED)
        else:
            pdf.set_text_color(*C_BLACK)
        pdf.cell(col_w, 9, val, align="C", new_x=XPos.RIGHT, new_y=YPos.TOP)

    y_after = pdf.get_y() + 9
    pdf.set_y(y_after)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*C_GRAY_MID)
    for i, (_, label) in enumerate(stats):
        x = MARGIN + i * col_w
        pdf.set_xy(x, pdf.get_y())
        pdf.cell(col_w, 5, label, align="C", new_x=XPos.RIGHT, new_y=YPos.TOP)

    pdf.set_y(pdf.get_y() + 6)
    _draw_rule(pdf)
    pdf.ln(4)


def _score_card(pdf: FPDF, x: float, y: float, w: float, score: int, label: str,
                color: tuple, bg_color: tuple) -> None:
    h = 40
    # Card background
    pdf.set_fill_color(*bg_color)
    pdf.set_draw_color(*color)
    pdf.set_line_width(0.5)
    pdf.rect(x, y, w, h, "DF")

    # Score number
    pdf.set_xy(x, y + 5)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(*color)
    pdf.cell(w, 14, str(score), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # "/100" label
    pdf.set_xy(x, y + 18)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*color)
    pdf.cell(w, 5, "/ 100", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Score bar
    bar_x = x + 8
    bar_y = y + 26
    bar_w = w - 16
    bar_h = 5
    pdf.set_fill_color(*C_GRAY_LIGHT)
    pdf.rect(bar_x, bar_y, bar_w, bar_h, "F")
    filled_w = max(1, round(bar_w * score / 100))
    pdf.set_fill_color(*color)
    pdf.rect(bar_x, bar_y, filled_w, bar_h, "F")

    # Label
    pdf.set_xy(x, y + 33)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*color)
    pdf.cell(w, 5, label.upper(), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def _missing_docs_section(pdf: FPDF, missing_items: list[dict]) -> None:
    if not missing_items:
        return
    _section_header(pdf, "Missing Documents")

    col_w = [50, 22, CONTENT_W - 72]
    _table_header(pdf, ["Document", "Required", "Description"], col_w)

    for item in missing_items:
        required = "Yes" if item.get("required", False) else "Recommended"
        desc = item.get("description", "")[:120]
        name = item.get("name", "")

        row_h = _multiline_height(pdf, desc, col_w[2])
        _check_page_break(pdf, row_h + 2)

        pdf.set_fill_color(*C_GRAY_BG)
        pdf.set_text_color(*C_BLACK)
        pdf.set_font("Helvetica", "B", 9)
        y0 = pdf.get_y()
        pdf.set_xy(MARGIN, y0)
        pdf.cell(col_w[0], row_h, name, border="LBT", fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)

        pdf.set_font("Helvetica", "", 9)
        req_color = C_RED if item.get("required", False) else C_AMBER
        pdf.set_text_color(*req_color)
        pdf.cell(col_w[1], row_h, required, border="BT", fill=True, align="C", new_x=XPos.RIGHT, new_y=YPos.TOP)

        pdf.set_text_color(*C_GRAY_DARK)
        pdf.set_xy(MARGIN + col_w[0] + col_w[1], y0)
        pdf.multi_cell(col_w[2], 5, desc, border="RBT", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(3)


def _risk_flags_section(pdf: FPDF, risk_flags: list[dict]) -> None:
    if not risk_flags:
        return
    _section_header(pdf, "Risk Flags")

    for flag in risk_flags:
        severity = flag.get("severity", "medium")
        title = flag.get("title", "")
        description = flag.get("description", "")[:200]
        color = SEVERITY_COLORS.get(severity, C_GRAY_MID)

        _check_page_break(pdf, 18)

        x0 = MARGIN
        y0 = pdf.get_y()

        # Severity badge
        badge_w = 18
        pdf.set_fill_color(*color)
        pdf.rect(x0, y0, badge_w, 10, "F")
        pdf.set_xy(x0, y0 + 2)
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(*C_WHITE)
        pdf.cell(badge_w, 5, severity.upper(), align="C", new_x=XPos.RIGHT, new_y=YPos.TOP)

        # Title
        pdf.set_xy(x0 + badge_w + 3, y0 + 1)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*C_BLACK)
        pdf.cell(CONTENT_W - badge_w - 3, 6, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Description
        pdf.set_xy(x0 + badge_w + 3, y0 + 8)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*C_GRAY_DARK)
        pdf.multi_cell(CONTENT_W - badge_w - 3, 5, description, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(3)

    pdf.ln(1)


def _requirements_section(pdf: FPDF, requirements: list[dict]) -> None:
    if not requirements:
        return
    _section_header(pdf, "Requirements Checklist")

    for i, req in enumerate(requirements):
        text = req.get("text", "")[:200]
        req_type = req.get("type", "").replace("_", " ").title()
        importance = req.get("importance", "required")
        status = req.get("status", "unclear")
        confidence = req.get("confidence", 0.0)
        evidence = req.get("evidence", [])

        status_color, status_label = STATUS_STYLES.get(status, (C_GRAY_MID, status))

        _check_page_break(pdf, 22)
        y0 = pdf.get_y()

        # Row background
        fill_color = C_GRAY_BG if i % 2 == 0 else C_WHITE
        pdf.set_fill_color(*fill_color)

        # Index + status stripe
        stripe_w = 4
        pdf.set_fill_color(*status_color)
        pdf.rect(MARGIN, y0, stripe_w, 12, "F")

        # Requirement number
        pdf.set_xy(MARGIN + stripe_w + 2, y0 + 1)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*C_GRAY_MID)
        pdf.cell(8, 5, f"{i + 1}.", new_x=XPos.RIGHT, new_y=YPos.TOP)

        # Requirement text
        text_x = MARGIN + stripe_w + 12
        text_w = CONTENT_W - stripe_w - 70
        pdf.set_xy(text_x, y0 + 1)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*C_BLACK)
        # Use cell with truncation for row
        display_text = text[:110] + ("…" if len(text) > 110 else "")
        pdf.cell(text_w, 5, display_text, new_x=XPos.RIGHT, new_y=YPos.TOP)

        # Type badge
        type_x = MARGIN + stripe_w + 12 + text_w + 3
        pdf.set_xy(type_x, y0 + 1)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*C_GRAY_MID)
        pdf.cell(28, 5, req_type[:18], new_x=XPos.RIGHT, new_y=YPos.TOP)

        # Status badge
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*status_color)
        pdf.cell(28, 5, status_label, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Confidence + evidence citations (if available)
        if evidence:
            for ev in evidence[:2]:
                doc_name = ev.get("document_name", "")
                page = ev.get("page_number", "")
                summary = ev.get("summary", "")[:100]
                citation_line = f"  ↳ {doc_name} p.{page} — {summary}"
                _check_page_break(pdf, 6)
                pdf.set_xy(MARGIN + stripe_w + 14, pdf.get_y())
                pdf.set_font("Helvetica", "I", 7)
                pdf.set_text_color(*C_GRAY_MID)
                pdf.cell(CONTENT_W - stripe_w - 16, 5, citation_line[:120], new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.ln(2)

    pdf.ln(2)


def _draft_answers_section(pdf: FPDF, draft_answers: list[dict]) -> None:
    if not draft_answers:
        return
    _section_header(pdf, "Draft Application Answers")
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*C_GRAY_MID)
    pdf.cell(0, 5, "Review and edit before submitting. Citations indicate source documents.",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)

    for i, answer in enumerate(draft_answers):
        question = answer.get("question", "")[:200]
        draft_text = answer.get("draft_answer", "")
        citations = answer.get("citations", [])
        missing = answer.get("missing_evidence", [])
        confidence = answer.get("confidence", 0.0)

        _check_page_break(pdf, 30)

        # Question header
        pdf.set_fill_color(*C_INDIGO_LIGHT)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*C_INDIGO)
        pdf.set_x(MARGIN)
        q_text = f"Q{i + 1}. {question}"
        pdf.multi_cell(CONTENT_W, 6, q_text, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(1)

        # Draft answer text
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*C_GRAY_DARK)
        pdf.set_x(MARGIN + 4)
        # Indent slightly
        paragraphs = draft_text.split("\n\n")
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            _check_page_break(pdf, 10)
            pdf.set_x(MARGIN + 4)
            pdf.multi_cell(CONTENT_W - 4, 5, para, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(2)

        # Citations
        if citations:
            pdf.set_font("Helvetica", "B", 7)
            pdf.set_text_color(*C_GRAY_MID)
            pdf.set_x(MARGIN + 4)
            pdf.cell(0, 4, "Sources:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            for cit in citations[:4]:
                doc_name = cit.get("document_name", "")
                page = cit.get("page_number", "")
                summary = cit.get("summary", "")[:80]
                _check_page_break(pdf, 5)
                pdf.set_font("Helvetica", "I", 7)
                pdf.set_text_color(*C_GRAY_MID)
                pdf.set_x(MARGIN + 8)
                pdf.cell(0, 4, f"• {doc_name}, p.{page} — {summary}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Missing evidence notes
        if missing:
            _check_page_break(pdf, 8)
            pdf.ln(1)
            pdf.set_font("Helvetica", "B", 7)
            pdf.set_text_color(*C_AMBER)
            pdf.set_x(MARGIN + 4)
            pdf.cell(0, 4, "Note — missing evidence:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            for m in missing[:2]:
                pdf.set_font("Helvetica", "I", 7)
                pdf.set_text_color(*C_AMBER)
                pdf.set_x(MARGIN + 8)
                pdf.cell(0, 4, f"• {str(m)[:120]}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.ln(4)
        # Thin separator
        pdf.set_draw_color(*C_GRAY_LIGHT)
        pdf.set_line_width(0.2)
        pdf.line(MARGIN, pdf.get_y(), PAGE_W - MARGIN, pdf.get_y())
        pdf.ln(4)


def _next_steps_section(pdf: FPDF, missing_items: list[dict], risk_flags: list[dict]) -> None:
    _check_page_break(pdf, 40)
    _section_header(pdf, "Recommended Next Steps")

    steps: list[str] = []

    # Missing required documents first
    for item in missing_items:
        if item.get("required", False):
            name = item.get("name", "Unknown document")
            steps.append(f"Upload the {name} to satisfy a required eligibility check.")

    # High-severity flags
    for flag in risk_flags:
        if flag.get("severity") == "high":
            title = flag.get("title", "")
            steps.append(f"Resolve: {title}.")

    # Medium flags
    for flag in risk_flags:
        if flag.get("severity") == "medium":
            title = flag.get("title", "")
            steps.append(f"Review and address: {title}.")

    # Generic closing
    steps.append("Review all draft answers above and customize them with your organization's specific details.")
    steps.append("Have a grant writer or program officer review this packet before submitting.")

    for i, step in enumerate(steps, 1):
        _check_page_break(pdf, 10)
        pdf.set_fill_color(*C_INDIGO)
        pdf.set_xy(MARGIN, pdf.get_y())
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*C_WHITE)
        # Number circle (approximated as a small filled rect)
        pdf.rect(MARGIN, pdf.get_y() + 1, 7, 6, "F")
        pdf.set_xy(MARGIN, pdf.get_y() + 1)
        pdf.cell(7, 6, str(i), align="C", new_x=XPos.RIGHT, new_y=YPos.TOP)

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*C_GRAY_DARK)
        step_x = MARGIN + 10
        pdf.set_xy(step_x, pdf.get_y())
        pdf.multi_cell(CONTENT_W - 10, 5, step, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(2)

    pdf.ln(4)
    # Disclaimer box
    _check_page_break(pdf, 20)
    pdf.set_fill_color(*C_GRAY_BG)
    pdf.set_draw_color(*C_GRAY_LIGHT)
    box_y = pdf.get_y()
    pdf.rect(MARGIN, box_y, CONTENT_W, 16, "DF")
    pdf.set_xy(MARGIN + 4, box_y + 3)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*C_GRAY_DARK)
    pdf.cell(0, 5, "Important Disclaimer", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_xy(MARGIN + 4, box_y + 8)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(*C_GRAY_MID)
    pdf.cell(0, 5, "This report is generated by AI and is a draft only. It does not constitute legal, tax, or grant compliance advice.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)


# ---------------------------------------------------------------------------
# Shared drawing helpers
# ---------------------------------------------------------------------------

def _section_header(pdf: FPDF, title: str) -> None:
    _check_page_break(pdf, 16)
    pdf.set_fill_color(*C_INDIGO)
    pdf.set_xy(MARGIN, pdf.get_y())
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*C_WHITE)
    pdf.cell(CONTENT_W, 8, f"  {title}", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)


def _table_header(pdf: FPDF, headers: list[str], col_widths: list[float]) -> None:
    pdf.set_fill_color(*C_GRAY_DARK)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*C_WHITE)
    pdf.set_x(MARGIN)
    for header, w in zip(headers, col_widths):
        pdf.cell(w, 7, f"  {header}", fill=True, border=0, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.ln(7)


def _draw_rule(pdf: FPDF) -> None:
    pdf.set_draw_color(*C_GRAY_LIGHT)
    pdf.set_line_width(0.3)
    pdf.line(MARGIN, pdf.get_y(), PAGE_W - MARGIN, pdf.get_y())


def _multiline_height(pdf: FPDF, text: str, width: float, line_h: float = 5.0) -> float:
    """Estimate height needed for multi_cell text."""
    if not text:
        return line_h
    chars_per_line = max(1, int(width / 2.2))
    lines = max(1, len(text) / chars_per_line)
    return max(line_h, round(lines) * line_h)


def _check_page_break(pdf: FPDF, needed: float) -> None:
    """Add a new page if there isn't enough space for `needed` mm."""
    if pdf.get_y() + needed > pdf.page_break_trigger:
        pdf.add_page()
