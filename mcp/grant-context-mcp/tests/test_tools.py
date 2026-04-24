"""
Integration tests for grant-context-mcp tools.

Strategy: each test calls the tool function directly (not via MCP protocol)
with a real SQLite test database. This tests the business logic in isolation
while keeping tests fast and dependency-free (no running MCP server needed).

The MCP protocol layer (JSON-RPC over stdio) is provided by the SDK and does
not need re-testing here.
"""
import json
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ---------------------------------------------------------------------------
# Path bootstrap: backend must be importable
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[3]
_BACKEND_DIR = _REPO_ROOT / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.models import analysis, chunk, document, organization, project  # noqa: F401
from app.models.base import Base


# ---------------------------------------------------------------------------
# Module-scoped DB engine (one DB per test run, tables created once)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def db_engine(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("mcp_test")
    engine = create_engine(
        f"sqlite:///{tmp}/test.db",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def db(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------

def _patch_db(monkeypatch, db, tmp_path):
    """Redirect server._get_db() to use the test session factory."""
    import app.core.database as db_module
    from sqlalchemy.orm import sessionmaker as sm
    TestSession = sm(bind=db.bind)
    monkeypatch.setattr(db_module, "SessionLocal", TestSession)
    monkeypatch.setattr(db_module, "engine", db.bind)

    from app.core.config import settings
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))


def _seed_project(db, project_id: str = "proj_mcp01", org_id: str = "org_mcp01"):
    """Insert demo rows if they don't already exist (idempotent)."""
    from app.models.analysis import ReadinessReport
    from app.models.organization import Organization
    from app.models.project import Project

    if db.get(Organization, org_id) is None:
        db.add(Organization(
            id=org_id,
            name="BrightPath Youth Foundation",
            mission="Provide STEM mentoring to low-income youth.",
            location="Columbus, Ohio",
            nonprofit_type="501(c)(3)",
            annual_budget=420_000,
            population_served="Low-income middle school students",
        ))

    if db.get(Project, project_id) is None:
        db.add(Project(
            id=project_id,
            organization_id=org_id,
            grant_name="Community STEM Access Fund",
            funder_name="Ohio Community Foundation",
            deadline="May 15, 2026",
            grant_amount="$50,000",
            status="analyzed",
        ))

    existing_report = (
        db.query(ReadinessReport)
        .filter(ReadinessReport.project_id == project_id)
        .first()
    )
    if existing_report is None:
        db.add(ReadinessReport(
            id=f"report_{project_id}",
            project_id=project_id,
            eligibility_score=82,
            readiness_score=74,
            requirements=[
                {
                    "id": "req_001",
                    "text": "Applicant must be a 501(c)(3) nonprofit.",
                    "type": "eligibility",
                    "importance": "required",
                    "status": "satisfied",
                    "confidence": 0.95,
                    "evidence": [],
                },
                {
                    "id": "req_002",
                    "text": "Applicant must provide IRS determination letter.",
                    "type": "required_document",
                    "importance": "required",
                    "status": "not_satisfied",
                    "confidence": 0.0,
                    "evidence": [],
                },
            ],
            missing_items=[
                {
                    "name": "IRS Determination Letter",
                    "required": True,
                    "description": "Required for eligibility verification.",
                }
            ],
            risk_flags=[
                {
                    "severity": "high",
                    "title": "IRS letter not uploaded",
                    "description": "Hard eligibility requirement.",
                }
            ],
            draft_answers=[],
        ))
    db.commit()


# ---------------------------------------------------------------------------
# Tests: ID validation (_validate_id)
# ---------------------------------------------------------------------------

class TestValidateId:
    def test_valid_ids_pass(self):
        import server as srv
        assert srv._validate_id("proj_abc123", "project_id") == "proj_abc123"
        assert srv._validate_id("org-brightpath", "org_id") == "org-brightpath"
        assert srv._validate_id("req_12345678abcd", "req_id") == "req_12345678abcd"

    def test_path_traversal_blocked(self):
        import server as srv
        with pytest.raises(ValueError):
            srv._validate_id("../../etc/passwd", "project_id")

    def test_shell_injection_blocked(self):
        import server as srv
        with pytest.raises(ValueError):
            srv._validate_id("proj; rm -rf /", "project_id")

    def test_empty_string_blocked(self):
        import server as srv
        with pytest.raises(ValueError):
            srv._validate_id("", "project_id")

    def test_too_long_blocked(self):
        import server as srv
        with pytest.raises(ValueError):
            srv._validate_id("a" * 61, "project_id")

    def test_spaces_blocked(self):
        import server as srv
        with pytest.raises(ValueError):
            srv._validate_id("proj test", "project_id")


# ---------------------------------------------------------------------------
# Tests: parse_grant_requirements
# ---------------------------------------------------------------------------

class TestParseGrantRequirements:
    def test_valid_project_returns_schema(self, db, monkeypatch, tmp_path):
        _patch_db(monkeypatch, db, tmp_path)
        _seed_project(db)
        import server as srv
        result = json.loads(srv.parse_grant_requirements("proj_mcp01"))

        assert result["project_id"] == "proj_mcp01"
        assert result["grant_name"] == "Community STEM Access Fund"
        assert isinstance(result["requirements"], list)
        assert isinstance(result["requirement_count"], int)

    def test_unknown_project_returns_error(self, db, monkeypatch, tmp_path):
        _patch_db(monkeypatch, db, tmp_path)
        import server as srv
        result = json.loads(srv.parse_grant_requirements("proj_does_not_exist"))
        assert "error" in result

    def test_invalid_id_raises_validation_error(self):
        import server as srv
        with pytest.raises(ValueError):
            srv.parse_grant_requirements("../../etc/passwd")

    def test_empty_id_raises_validation_error(self):
        import server as srv
        with pytest.raises(ValueError):
            srv.parse_grant_requirements("")

    def test_returns_valid_json_string(self, db, monkeypatch, tmp_path):
        _patch_db(monkeypatch, db, tmp_path)
        _seed_project(db)
        import server as srv
        result_str = srv.parse_grant_requirements("proj_mcp01")
        parsed = json.loads(result_str)
        assert isinstance(parsed, dict)


# ---------------------------------------------------------------------------
# Tests: extract_nonprofit_profile
# ---------------------------------------------------------------------------

class TestExtractNonprofitProfile:
    def test_returns_org_and_project_info(self, db, monkeypatch, tmp_path):
        _patch_db(monkeypatch, db, tmp_path)
        _seed_project(db)
        import server as srv
        result = json.loads(srv.extract_nonprofit_profile("proj_mcp01"))

        assert result["project_id"] == "proj_mcp01"
        assert result["organization"]["name"] == "BrightPath Youth Foundation"
        assert result["organization"]["nonprofit_type"] == "501(c)(3)"
        assert result["project"]["grant_name"] == "Community STEM Access Fund"
        assert isinstance(result["documents"], list)
        assert isinstance(result["document_type_summary"], dict)

    def test_no_secrets_in_output(self, db, monkeypatch, tmp_path):
        _patch_db(monkeypatch, db, tmp_path)
        _seed_project(db)
        import server as srv
        result_str = srv.extract_nonprofit_profile("proj_mcp01")
        assert "API_KEY" not in result_str
        assert "password" not in result_str.lower()
        assert "secret" not in result_str.lower()

    def test_unknown_project_returns_error(self, db, monkeypatch, tmp_path):
        _patch_db(monkeypatch, db, tmp_path)
        import server as srv
        result = json.loads(srv.extract_nonprofit_profile("proj_ghost"))
        assert "error" in result

    def test_invalid_id_path_traversal_blocked(self):
        import server as srv
        with pytest.raises(ValueError):
            srv.extract_nonprofit_profile("../../../etc/shadow")


# ---------------------------------------------------------------------------
# Tests: generate_readiness_checklist
# ---------------------------------------------------------------------------

class TestGenerateReadinessChecklist:
    def test_returns_scores_and_flags(self, db, monkeypatch, tmp_path):
        _patch_db(monkeypatch, db, tmp_path)
        _seed_project(db)
        import server as srv
        result = json.loads(srv.generate_readiness_checklist("proj_mcp01"))

        assert result["eligibility_score"] == 82
        assert result["readiness_score"] == 74
        assert result["requirements_summary"]["total"] == 2
        assert result["requirements_summary"]["satisfied"] == 1
        assert result["requirements_summary"]["not_met"] == 1
        assert len(result["missing_documents"]) == 1
        assert len(result["risk_flags"]) == 1
        assert result["risk_flags"][0]["severity"] == "high"

    def test_requirements_have_correct_fields(self, db, monkeypatch, tmp_path):
        _patch_db(monkeypatch, db, tmp_path)
        _seed_project(db)
        import server as srv
        result = json.loads(srv.generate_readiness_checklist("proj_mcp01"))
        for req in result["requirements"]:
            assert "id" in req
            assert "text" in req
            assert "status" in req
            assert "confidence" in req

    def test_no_analysis_returns_error(self, db, monkeypatch, tmp_path):
        _patch_db(monkeypatch, db, tmp_path)
        # Seed a project with no analysis
        from app.models.organization import Organization
        from app.models.project import Project
        if db.get(Organization, "org_noanalysis") is None:
            db.add(Organization(id="org_noanalysis", name="No Analysis Org", mission="Test.",
                                 location="Test", nonprofit_type="501(c)(3)", annual_budget=10_000,
                                 population_served="Test"))
        if db.get(Project, "proj_noanalysis") is None:
            db.add(Project(id="proj_noanalysis", organization_id="org_noanalysis",
                           grant_name="Test Grant", status="draft"))
        db.commit()
        import server as srv
        result = json.loads(srv.generate_readiness_checklist("proj_noanalysis"))
        assert "error" in result

    def test_unknown_project_returns_error(self, db, monkeypatch, tmp_path):
        _patch_db(monkeypatch, db, tmp_path)
        import server as srv
        result = json.loads(srv.generate_readiness_checklist("proj_unknown"))
        assert "error" in result


# ---------------------------------------------------------------------------
# Tests: generate_packet
# ---------------------------------------------------------------------------

class TestGeneratePacket:
    def test_generates_pdf_and_returns_url(self, db, monkeypatch, tmp_path):
        _patch_db(monkeypatch, db, tmp_path)
        _seed_project(db)
        import server as srv
        result = json.loads(srv.generate_packet("proj_mcp01"))

        assert "report_pdf_url" in result
        assert result["project_id"] == "proj_mcp01"
        assert result["file_size_bytes"] > 0
        assert "download_endpoint" in result
        assert "/report/download" in result["download_endpoint"]

    def test_summary_contains_scores(self, db, monkeypatch, tmp_path):
        _patch_db(monkeypatch, db, tmp_path)
        _seed_project(db)
        import server as srv
        result = json.loads(srv.generate_packet("proj_mcp01"))
        assert result["summary"]["eligibility_score"] == 82
        assert result["summary"]["readiness_score"] == 74
        assert isinstance(result["summary"]["missing_doc_count"], int)
        assert isinstance(result["summary"]["high_risk_count"], int)

    def test_no_absolute_paths_in_output(self, db, monkeypatch, tmp_path):
        _patch_db(monkeypatch, db, tmp_path)
        _seed_project(db)
        import server as srv
        result_str = srv.generate_packet("proj_mcp01")
        parsed = json.loads(result_str)
        url = parsed.get("report_pdf_url", "")
        assert not url.startswith("/"), "Storage URL must be relative"
        assert "\\" not in url, "Storage URL must not contain backslashes"
        assert ".." not in url, "Storage URL must not contain path traversal"

    def test_second_call_reuses_cached_pdf(self, db, monkeypatch, tmp_path):
        _patch_db(monkeypatch, db, tmp_path)
        _seed_project(db)
        import server as srv
        r1 = json.loads(srv.generate_packet("proj_mcp01"))
        r2 = json.loads(srv.generate_packet("proj_mcp01"))
        assert r1["report_pdf_url"] == r2["report_pdf_url"]

    def test_unknown_project_returns_error(self, db, monkeypatch, tmp_path):
        _patch_db(monkeypatch, db, tmp_path)
        import server as srv
        result = json.loads(srv.generate_packet("proj_ghostproject"))
        assert "error" in result

    def test_invalid_id_raises(self):
        import server as srv
        with pytest.raises(ValueError):
            srv.generate_packet("../../../evil")
