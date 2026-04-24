"""
Auth route tests: register, login, /me, protected routes, ownership enforcement.
"""
from fastapi.testclient import TestClient


_USER = {"email": "authtest@example.com", "password": "strongpass123"}
_OTHER = {"email": "other@example.com", "password": "otherpass123"}


def _register(client: TestClient, email: str, password: str) -> str:
    resp = client.post("/auth/register", json={"email": email, "password": password})
    assert resp.status_code == 201, resp.text
    return resp.json()["access_token"]


def _login(client: TestClient, email: str, password: str) -> str:
    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

def test_register_returns_token(client: TestClient) -> None:
    resp = client.post(
        "/auth/register", json={"email": "newuser@example.com", "password": "password123"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_register_duplicate_email_returns_409(client: TestClient) -> None:
    client.post("/auth/register", json={"email": "dup@example.com", "password": "pass1234"})
    resp = client.post("/auth/register", json={"email": "dup@example.com", "password": "pass1234"})
    assert resp.status_code == 409


def test_register_short_password_rejected(client: TestClient) -> None:
    resp = client.post("/auth/register", json={"email": "short@example.com", "password": "abc"})
    assert resp.status_code == 422


def test_register_invalid_email_rejected(client: TestClient) -> None:
    resp = client.post(
        "/auth/register", json={"email": "not-an-email", "password": "password123"}
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def test_login_returns_token(client: TestClient) -> None:
    client.post("/auth/register", json={"email": "login@example.com", "password": "pass1234!"})
    resp = client.post("/auth/login", json={"email": "login@example.com", "password": "pass1234!"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password_returns_401(client: TestClient) -> None:
    client.post("/auth/register", json={"email": "pw@example.com", "password": "rightpass1"})
    resp = client.post("/auth/login", json={"email": "pw@example.com", "password": "wrongpass"})
    assert resp.status_code == 401


def test_login_unknown_email_returns_401(client: TestClient) -> None:
    resp = client.post(
        "/auth/login", json={"email": "nobody@example.com", "password": "somepass"}
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# /auth/me
# ---------------------------------------------------------------------------

def test_me_returns_user(client: TestClient) -> None:
    token = _register(client, "me@example.com", "password123")
    resp = client.get("/auth/me", headers=_headers(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "me@example.com"
    assert "id" in body
    assert "created_at" in body


def test_me_without_token_returns_401(client: TestClient) -> None:
    with _strip_auth(client) as c:
        resp = c.get("/auth/me")
    assert resp.status_code == 401


def test_me_with_bad_token_returns_401(client: TestClient) -> None:
    resp = client.get("/auth/me", headers={"Authorization": "Bearer not.a.real.token"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Protected routes
# ---------------------------------------------------------------------------

def _strip_auth(client: TestClient):
    """Context manager that temporarily removes the Authorization header."""
    import contextlib

    @contextlib.contextmanager
    def _ctx():
        saved = client.headers.get("authorization")
        if saved:
            del client.headers["authorization"]
        try:
            yield client
        finally:
            if saved:
                client.headers["Authorization"] = saved

    return _ctx()


def test_org_create_requires_auth(client: TestClient) -> None:
    with _strip_auth(client) as c:
        resp = c.post(
            "/organizations",
            json={
                "name": "Test",
                "mission": "Test.",
                "location": "X",
                "nonprofit_type": "501(c)(3)",
                "annual_budget": 1000,
                "population_served": "X",
            },
        )
    assert resp.status_code == 401


def test_org_get_requires_auth(client: TestClient) -> None:
    with _strip_auth(client) as c:
        resp = c.get("/organizations/org_brightpath")
    assert resp.status_code == 401


def test_project_create_requires_auth(client: TestClient) -> None:
    with _strip_auth(client) as c:
        resp = c.post("/projects", json={"organization_id": "x", "grant_name": "X"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Ownership enforcement
# ---------------------------------------------------------------------------

def test_org_owned_by_creator(client: TestClient) -> None:
    """User A can access their own org."""
    resp = client.post(
        "/organizations",
        json={
            "name": "Mine",
            "mission": "Test mission.",
            "location": "Columbus",
            "nonprofit_type": "501(c)(3)",
            "annual_budget": 50000,
            "population_served": "Youth",
        },
    )
    assert resp.status_code == 201
    org_id = resp.json()["id"]
    get = client.get(f"/organizations/{org_id}")
    assert get.status_code == 200


def test_org_forbidden_for_other_user(client: TestClient) -> None:
    """User A's org returns 403 for user B."""
    # User A (the fixture client) creates org
    resp = client.post(
        "/organizations",
        json={
            "name": "A Org",
            "mission": "A mission.",
            "location": "Columbus",
            "nonprofit_type": "501(c)(3)",
            "annual_budget": 50000,
            "population_served": "Youth",
        },
    )
    org_id = resp.json()["id"]

    # User B registers and tries to access it
    token_b = _register(client, "userb@example.com", "password123")
    resp_b = client.get(f"/organizations/{org_id}", headers=_headers(token_b))
    assert resp_b.status_code == 403


def test_project_forbidden_for_other_user(client: TestClient) -> None:
    """User B cannot access User A's project."""
    # A creates org + project
    org = client.post(
        "/organizations",
        json={
            "name": "A Org2",
            "mission": "A mission.",
            "location": "Columbus",
            "nonprofit_type": "501(c)(3)",
            "annual_budget": 50000,
            "population_served": "Youth",
        },
    ).json()
    proj = client.post(
        "/projects",
        json={"organization_id": org["id"], "grant_name": "Grant"},
    ).json()

    # B tries to access
    token_b = _register(client, "userb2@example.com", "password123")
    resp = client.get(f"/projects/{proj['id']}", headers=_headers(token_b))
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Demo seed user
# ---------------------------------------------------------------------------

def test_demo_seed_user_can_login(client: TestClient) -> None:
    """The seeded demo account should be login-ready."""
    resp = client.post(
        "/auth/login",
        json={"email": "demo@grantpilot.local", "password": "DemoGrantPilot123!"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_demo_user_can_access_demo_project(client: TestClient) -> None:
    """The demo user can read org_brightpath and proj_stem_2026."""
    token = _login(client, "demo@grantpilot.local", "DemoGrantPilot123!")
    h = _headers(token)

    org_resp = client.get("/organizations/org_brightpath", headers=h)
    assert org_resp.status_code == 200
    assert org_resp.json()["name"] == "BrightPath Youth Foundation"

    proj_resp = client.get("/projects/proj_stem_2026", headers=h)
    assert proj_resp.status_code == 200
    assert proj_resp.json()["grant_name"] == "Community STEM Access Fund"
