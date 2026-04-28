"""Tests for Phase 13 additions: password change and analysis summary."""
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Password change
# ---------------------------------------------------------------------------

class TestChangePassword:
    def test_change_password_returns_204(self, client: TestClient) -> None:
        # Register a fresh user
        reg = client.post(
            "/auth/register",
            json={"email": "chpwd_ok@test.com", "password": "oldpassword1"},
        )
        token = reg.json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}

        resp = client.post(
            "/auth/change-password",
            json={"current_password": "oldpassword1", "new_password": "newpassword2"},
            headers=h,
        )
        assert resp.status_code == 204

    def test_new_password_works_after_change(self, client: TestClient) -> None:
        reg = client.post(
            "/auth/register",
            json={"email": "chpwd_login@test.com", "password": "oldpassword1"},
        )
        token = reg.json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}

        client.post(
            "/auth/change-password",
            json={"current_password": "oldpassword1", "new_password": "newpassword2"},
            headers=h,
        )

        # Old password should no longer work
        old_login = client.post(
            "/auth/login",
            json={"email": "chpwd_login@test.com", "password": "oldpassword1"},
        )
        assert old_login.status_code == 401

        # New password should work
        new_login = client.post(
            "/auth/login",
            json={"email": "chpwd_login@test.com", "password": "newpassword2"},
        )
        assert new_login.status_code == 200

    def test_wrong_current_password_returns_400(self, client: TestClient) -> None:
        reg = client.post(
            "/auth/register",
            json={"email": "chpwd_bad@test.com", "password": "correctpassword"},
        )
        token = reg.json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}

        resp = client.post(
            "/auth/change-password",
            json={"current_password": "wrongpassword", "new_password": "newpassword2"},
            headers=h,
        )
        assert resp.status_code == 400
        assert "incorrect" in resp.json()["detail"].lower()

    def test_new_password_too_short_rejected(self, client: TestClient) -> None:
        reg = client.post(
            "/auth/register",
            json={"email": "chpwd_short@test.com", "password": "validpassword"},
        )
        token = reg.json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}

        resp = client.post(
            "/auth/change-password",
            json={"current_password": "validpassword", "new_password": "short"},
            headers=h,
        )
        assert resp.status_code == 422

    def test_change_password_requires_auth(self, client: TestClient) -> None:
        saved = client.headers.get("authorization")
        del client.headers["authorization"]
        try:
            resp = client.post(
                "/auth/change-password",
                json={"current_password": "x", "new_password": "newpassword2"},
            )
            assert resp.status_code == 401
        finally:
            if saved:
                client.headers["Authorization"] = saved

    def test_demo_user_cannot_change_password(self, client: TestClient) -> None:
        """Demo account password changes are blocked (Phase 19)."""
        token = client.post(
            "/auth/login",
            json={"email": "demo@grantpilot.local", "password": "DemoGrantPilot123!"},
        ).json()["access_token"]
        resp = client.post(
            "/auth/change-password",
            json={"current_password": "DemoGrantPilot123!", "new_password": "TempDemo1234!"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Analysis summary
# ---------------------------------------------------------------------------

class TestAnalysisSummary:
    def test_summary_returns_scores_and_counts(
        self, client: TestClient, project_id: str
    ) -> None:
        client.post(f"/projects/{project_id}/analyze")
        resp = client.get(f"/projects/{project_id}/analysis/summary")
        assert resp.status_code == 200
        body = resp.json()
        assert body["project_id"] == project_id
        assert isinstance(body["eligibility_score"], int)
        assert isinstance(body["readiness_score"], int)
        assert isinstance(body["requirement_count"], int)
        assert isinstance(body["satisfied_count"], int)
        assert isinstance(body["missing_doc_count"], int)
        assert isinstance(body["high_risk_count"], int)

    def test_summary_matches_mock_data(
        self, client: TestClient, project_id: str
    ) -> None:
        client.post(f"/projects/{project_id}/analyze")
        resp = client.get(f"/projects/{project_id}/analysis/summary")
        body = resp.json()
        # Mock data always returns 82/74
        assert body["eligibility_score"] == 82
        assert body["readiness_score"] == 74
        assert body["requirement_count"] == 10

    def test_summary_before_analyze_returns_404(
        self, client: TestClient, project_id: str
    ) -> None:
        resp = client.get(f"/projects/{project_id}/analysis/summary")
        assert resp.status_code == 404

    def test_summary_requires_auth(self, client: TestClient, project_id: str) -> None:
        client.post(f"/projects/{project_id}/analyze")
        saved = client.headers.get("authorization")
        del client.headers["authorization"]
        try:
            resp = client.get(f"/projects/{project_id}/analysis/summary")
            assert resp.status_code == 401
        finally:
            if saved:
                client.headers["Authorization"] = saved

    def test_summary_unknown_project_returns_404(self, client: TestClient) -> None:
        resp = client.get("/projects/proj_ghost/analysis/summary")
        assert resp.status_code == 404

    def test_demo_project_summary_available(self, client: TestClient) -> None:
        """Demo project is pre-analyzed — summary should be immediately available."""
        token = client.post(
            "/auth/login",
            json={"email": "demo@grantpilot.local", "password": "DemoGrantPilot123!"},
        ).json()["access_token"]
        resp = client.get(
            "/projects/proj_stem_2026/analysis/summary",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["eligibility_score"] == 82
        assert body["readiness_score"] == 74
