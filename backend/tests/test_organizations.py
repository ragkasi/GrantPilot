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
