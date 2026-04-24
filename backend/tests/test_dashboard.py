"""
Tests for dashboard list endpoints:
  GET /organizations
  GET /organizations/{id}/projects
  GET /projects
"""
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# GET /organizations
# ---------------------------------------------------------------------------

def test_list_organizations_empty_for_new_user(client: TestClient) -> None:
    """A brand-new user has no organizations."""
    # The fixture creates a test user; demo orgs belong to user_demo, not test@example.com
    resp = client.get("/organizations")
    assert resp.status_code == 200
    # user only sees their own orgs — demo org does not appear
    ids = [o["id"] for o in resp.json()]
    assert "org_brightpath" not in ids


def test_list_organizations_returns_created_orgs(client: TestClient, org_id: str) -> None:
    """After creating an org it appears in the list."""
    resp = client.get("/organizations")
    assert resp.status_code == 200
    ids = [o["id"] for o in resp.json()]
    assert org_id in ids


def test_list_organizations_multiple(client: TestClient) -> None:
    """Creating two orgs returns both."""
    _ORG = {
        "mission": "Test.", "location": "X",
        "nonprofit_type": "501(c)(3)", "annual_budget": 1000, "population_served": "X",
    }
    id1 = client.post("/organizations", json={**_ORG, "name": "Alpha"}).json()["id"]
    id2 = client.post("/organizations", json={**_ORG, "name": "Beta"}).json()["id"]

    resp = client.get("/organizations")
    ids = [o["id"] for o in resp.json()]
    assert id1 in ids
    assert id2 in ids


def test_list_organizations_requires_auth(client: TestClient) -> None:
    saved = client.headers.get("authorization")
    del client.headers["authorization"]
    try:
        resp = client.get("/organizations")
        assert resp.status_code == 401
    finally:
        if saved:
            client.headers["Authorization"] = saved


def test_list_organizations_returns_full_org_fields(client: TestClient, org_id: str) -> None:
    resp = client.get("/organizations")
    assert resp.status_code == 200
    org = next(o for o in resp.json() if o["id"] == org_id)
    assert "name" in org
    assert "mission" in org
    assert "location" in org
    assert "annual_budget" in org


# ---------------------------------------------------------------------------
# GET /organizations/{id}/projects
# ---------------------------------------------------------------------------

def test_list_org_projects_empty(client: TestClient, org_id: str) -> None:
    resp = client.get(f"/organizations/{org_id}/projects")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_org_projects_returns_projects(
    client: TestClient, org_id: str, project_id: str
) -> None:
    resp = client.get(f"/organizations/{org_id}/projects")
    assert resp.status_code == 200
    ids = [p["id"] for p in resp.json()]
    assert project_id in ids


def test_list_org_projects_other_user_returns_403(client: TestClient) -> None:
    """User B cannot list projects in user A's org."""
    # User A (fixture) creates org
    resp = client.post(
        "/organizations",
        json={
            "name": "A Org", "mission": "X.", "location": "X",
            "nonprofit_type": "501(c)(3)", "annual_budget": 1000, "population_served": "X",
        },
    )
    org_id = resp.json()["id"]

    # User B registers
    token_b = client.post(
        "/auth/register", json={"email": "b_proj@example.com", "password": "password123"}
    ).json()["access_token"]
    resp_b = client.get(
        f"/organizations/{org_id}/projects",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp_b.status_code == 403


# ---------------------------------------------------------------------------
# GET /projects
# ---------------------------------------------------------------------------

def test_list_projects_empty_for_new_user(client: TestClient) -> None:
    resp = client.get("/projects")
    assert resp.status_code == 200
    # test user has no projects; demo project belongs to user_demo
    ids = [p["id"] for p in resp.json()]
    assert "proj_stem_2026" not in ids


def test_list_projects_returns_created_projects(
    client: TestClient, org_id: str, project_id: str
) -> None:
    resp = client.get("/projects")
    assert resp.status_code == 200
    ids = [p["id"] for p in resp.json()]
    assert project_id in ids


def test_list_projects_spans_multiple_orgs(client: TestClient) -> None:
    """Projects from two different owned orgs both appear in the list."""
    _ORG = {
        "mission": "Test.", "location": "X",
        "nonprofit_type": "501(c)(3)", "annual_budget": 1000, "population_served": "X",
    }
    org1 = client.post("/organizations", json={**_ORG, "name": "OrgA"}).json()["id"]
    org2 = client.post("/organizations", json={**_ORG, "name": "OrgB"}).json()["id"]

    p1 = client.post("/projects", json={"organization_id": org1, "grant_name": "G1"}).json()["id"]
    p2 = client.post("/projects", json={"organization_id": org2, "grant_name": "G2"}).json()["id"]

    resp = client.get("/projects")
    ids = [p["id"] for p in resp.json()]
    assert p1 in ids
    assert p2 in ids


def test_list_projects_requires_auth(client: TestClient) -> None:
    saved = client.headers.get("authorization")
    del client.headers["authorization"]
    try:
        resp = client.get("/projects")
        assert resp.status_code == 401
    finally:
        if saved:
            client.headers["Authorization"] = saved


def test_list_projects_full_fields(client: TestClient, org_id: str, project_id: str) -> None:
    resp = client.get("/projects")
    proj = next(p for p in resp.json() if p["id"] == project_id)
    assert "grant_name" in proj
    assert "status" in proj
    assert "organization_id" in proj


def test_demo_user_sees_demo_project(client: TestClient) -> None:
    """The seeded demo user can list their demo project."""
    token = client.post(
        "/auth/login",
        json={"email": "demo@grantpilot.local", "password": "DemoGrantPilot123!"},
    ).json()["access_token"]
    resp = client.get("/projects", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    ids = [p["id"] for p in resp.json()]
    assert "proj_stem_2026" in ids
