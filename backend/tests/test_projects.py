from fastapi.testclient import TestClient


def test_create_project_returns_201(client: TestClient, org_id: str) -> None:
    resp = client.post(
        "/projects",
        json={"organization_id": org_id, "grant_name": "Community STEM Fund"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["organization_id"] == org_id
    assert body["grant_name"] == "Community STEM Fund"
    assert body["status"] == "draft"
    assert body["id"].startswith("proj_")


def test_create_project_unknown_org_returns_404(client: TestClient) -> None:
    resp = client.post(
        "/projects",
        json={"organization_id": "org_ghost", "grant_name": "Ghost Grant"},
    )
    assert resp.status_code == 404


def test_get_project_returns_full_record(client: TestClient, org_id: str) -> None:
    proj_id = client.post(
        "/projects",
        json={"organization_id": org_id, "grant_name": "STEM Fund", "grant_source_url": "https://example.org/grant"},
    ).json()["id"]

    resp = client.get(f"/projects/{proj_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == proj_id
    assert body["grant_source_url"] == "https://example.org/grant"
    assert body["status"] == "draft"


def test_get_project_not_found(client: TestClient) -> None:
    resp = client.get("/projects/proj_ghost")
    assert resp.status_code == 404


def test_create_project_empty_grant_name_rejected(client: TestClient, org_id: str) -> None:
    resp = client.post(
        "/projects",
        json={"organization_id": org_id, "grant_name": ""},
    )
    assert resp.status_code == 422
