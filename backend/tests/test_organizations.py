from fastapi.testclient import TestClient

_PAYLOAD = {
    "name": "BrightPath Youth Foundation",
    "mission": "Provide STEM mentoring to low-income youth.",
    "location": "Columbus, Ohio",
    "nonprofit_type": "501(c)(3)",
    "annual_budget": 420000,
    "population_served": "Low-income middle school students",
}


def test_create_organization_returns_201(client: TestClient) -> None:
    resp = client.post("/organizations", json=_PAYLOAD)
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == _PAYLOAD["name"]
    assert body["id"].startswith("org_")
    assert "created_at" in body


def test_get_organization_returns_full_record(client: TestClient) -> None:
    org_id = client.post("/organizations", json=_PAYLOAD).json()["id"]
    resp = client.get(f"/organizations/{org_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == org_id
    assert body["mission"] == _PAYLOAD["mission"]
    assert body["annual_budget"] == _PAYLOAD["annual_budget"]


def test_get_organization_not_found(client: TestClient) -> None:
    resp = client.get("/organizations/org_doesnotexist")
    assert resp.status_code == 404


def test_create_organization_missing_required_field(client: TestClient) -> None:
    bad = {k: v for k, v in _PAYLOAD.items() if k != "name"}
    resp = client.post("/organizations", json=bad)
    assert resp.status_code == 422


def test_create_organization_negative_budget_rejected(client: TestClient) -> None:
    payload = {**_PAYLOAD, "annual_budget": -1}
    resp = client.post("/organizations", json=payload)
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Organization deletion
# ---------------------------------------------------------------------------

def test_delete_organization_returns_204(client: TestClient) -> None:
    org_id = client.post("/organizations", json=_PAYLOAD).json()["id"]
    resp = client.delete(f"/organizations/{org_id}")
    assert resp.status_code == 204


def test_deleted_organization_not_found(client: TestClient) -> None:
    org_id = client.post("/organizations", json=_PAYLOAD).json()["id"]
    client.delete(f"/organizations/{org_id}")
    resp = client.get(f"/organizations/{org_id}")
    assert resp.status_code in (403, 404)


def test_delete_unknown_org_returns_404(client: TestClient) -> None:
    resp = client.delete("/organizations/org_ghost_does_not_exist")
    assert resp.status_code == 404


def test_delete_org_requires_auth(client: TestClient) -> None:
    org_id = client.post("/organizations", json=_PAYLOAD).json()["id"]
    saved = client.headers.get("authorization")
    del client.headers["authorization"]
    try:
        resp = client.delete(f"/organizations/{org_id}")
        assert resp.status_code == 401
    finally:
        if saved:
            client.headers["Authorization"] = saved


def test_delete_other_users_org_returns_403(client: TestClient) -> None:
    org_id = client.post("/organizations", json=_PAYLOAD).json()["id"]
    token_b = client.post(
        "/auth/register",
        json={"email": "orgdelete_b@test.com", "password": "pass12345"},
    ).json()["access_token"]
    resp = client.delete(
        f"/organizations/{org_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 403


def test_delete_org_cascades_projects(client: TestClient, org_id: str, project_id: str) -> None:
    """Deleting an org must also delete its projects."""
    # Verify project exists
    assert client.get(f"/projects/{project_id}").status_code == 200
    # Delete the org
    resp = client.delete(f"/organizations/{org_id}")
    assert resp.status_code == 204
    # Project should now be gone
    assert client.get(f"/projects/{project_id}").status_code in (403, 404)


def test_delete_org_removed_from_list(client: TestClient) -> None:
    org_id = client.post("/organizations", json=_PAYLOAD).json()["id"]
    client.delete(f"/organizations/{org_id}")
    orgs = client.get("/organizations").json()
    assert not any(o["id"] == org_id for o in orgs)


# ---------------------------------------------------------------------------
# Demo account password restriction
# ---------------------------------------------------------------------------

def test_demo_account_cannot_change_password(client: TestClient) -> None:
    token = client.post(
        "/auth/login",
        json={"email": "demo@grantpilot.local", "password": "DemoGrantPilot123!"},
    ).json()["access_token"]
    resp = client.post(
        "/auth/change-password",
        json={"current_password": "DemoGrantPilot123!", "new_password": "NewPass9999!"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
    assert "demo" in resp.json()["detail"].lower()


def test_normal_user_can_change_password(client: TestClient) -> None:
    reg = client.post(
        "/auth/register",
        json={"email": "canchange@test.com", "password": "oldpass123"},
    )
    token = reg.json()["access_token"]
    resp = client.post(
        "/auth/change-password",
        json={"current_password": "oldpass123", "new_password": "newpass456"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204


def test_get_me_includes_is_demo_false_for_normal_user(client: TestClient) -> None:
    me = client.get("/auth/me").json()
    assert "is_demo" in me
    assert me["is_demo"] is False


def test_get_me_includes_is_demo_true_for_demo_user(client: TestClient) -> None:
    token = client.post(
        "/auth/login",
        json={"email": "demo@grantpilot.local", "password": "DemoGrantPilot123!"},
    ).json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
    assert me["is_demo"] is True
