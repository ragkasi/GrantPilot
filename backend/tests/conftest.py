"""
Shared test fixtures.

Each test gets:
  - A fresh SQLite file DB (tmp_path/test.db) with all tables created.
  - A DB session override via FastAPI dependency injection.
  - An isolated upload directory (tmp_path/uploads).
  - An authenticated client with a test user's JWT.

The engine and SessionLocal in app.core.database are monkey-patched so that
the lifespan's create_all_tables() and seed_demo() both use the test DB.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.core.database as db_module

# Import every model module so SQLAlchemy registers them all with Base.metadata
# before any test calls create_all().
from app.models import analysis, chunk, document, organization, project, user  # noqa: F401
from app.models.base import Base


@pytest.fixture()
def test_engine(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def db_session(test_engine, monkeypatch):
    """Patches the module-level engine + SessionLocal so all app code uses the test DB."""
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    monkeypatch.setattr(db_module, "engine", test_engine)
    monkeypatch.setattr(db_module, "SessionLocal", TestSession)

    session = TestSession()
    yield session
    session.rollback()
    session.close()


@pytest.fixture()
def client(db_session, tmp_path, monkeypatch):
    """
    Authenticated TestClient:
      - DB dependency overridden to the test session
      - upload_dir pointed at tmp_path/uploads
      - A test user is registered and their JWT is attached to all requests
    """
    from app.core.config import settings
    from app.core.database import get_db
    from app.main import app

    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app, raise_server_exceptions=True) as c:
        # Register + login a test user, attach token to all future requests
        reg = c.post("/auth/register", json={"email": "test@example.com", "password": "testpassword123"})
        assert reg.status_code == 201, reg.text
        token = reg.json()["access_token"]
        c.headers.update({"Authorization": f"Bearer {token}"})
        yield c

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Convenience fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def org_id(client: TestClient) -> str:
    resp = client.post(
        "/organizations",
        json={
            "name": "Test Nonprofit",
            "mission": "Serve the community.",
            "location": "Columbus, OH",
            "nonprofit_type": "501(c)(3)",
            "annual_budget": 100000,
            "population_served": "Low-income youth",
        },
    )
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest.fixture()
def project_id(client: TestClient, org_id: str) -> str:
    resp = client.post(
        "/projects",
        json={
            "organization_id": org_id,
            "grant_name": "STEM Access Fund",
            "grant_source_url": None,
        },
    )
    assert resp.status_code == 201
    return resp.json()["id"]
