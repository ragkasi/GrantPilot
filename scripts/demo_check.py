#!/usr/bin/env python3
"""
GrantPilot demo readiness check.

Verifies that the backend is running and the demo flow works end-to-end.
Exits 0 if all checks pass, 1 if any fail.

Usage:
    # Local dev (default)
    python scripts/demo_check.py

    # Railway or any hosted deployment
    python scripts/demo_check.py --api-url https://your-backend.up.railway.app
"""
import argparse
import json
import sys
import urllib.error
import urllib.request


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _request(url: str, *, method: str = "GET", data: dict | None = None,
             headers: dict | None = None) -> dict:
    body = json.dumps(data).encode() if data else None
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def _check_health(base: str) -> dict:
    body = _request(f"{base}/health")
    assert body.get("status") == "ok", f"expected status=ok, got {body}"
    return body


def _check_login(base: str) -> str:
    body = _request(
        f"{base}/auth/login",
        method="POST",
        data={"email": "demo@grantpilot.local", "password": "DemoGrantPilot123!"},
    )
    assert "access_token" in body, f"no access_token: {body}"
    return body["access_token"]


def _check_analysis(base: str, token: str) -> dict:
    body = _request(
        f"{base}/projects/proj_stem_2026/analysis",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert "eligibility_score" in body, "missing eligibility_score"
    assert "analysis_source" in body, "missing analysis_source (Phase 14)"
    return body


def _check_summary(base: str, token: str) -> dict:
    body = _request(
        f"{base}/projects/proj_stem_2026/analysis/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert "eligibility_score" in body, "missing eligibility_score"
    return body


def _check_report_meta(base: str, token: str) -> dict:
    body = _request(
        f"{base}/projects/proj_stem_2026/report",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert "project_id" in body, "missing project_id"
    return body


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

CHECKS = [
    ("Backend /health", _check_health, False),
    ("Demo login", _check_login, False),
    ("Demo analysis exists", _check_analysis, True),
    ("Analysis summary endpoint", _check_summary, True),
    ("Report metadata endpoint", _check_report_meta, True),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="GrantPilot demo readiness check")
    parser.add_argument("--api-url", default="http://localhost:8000",
                        help="Backend base URL (default: http://localhost:8000)")
    args = parser.parse_args()
    base = args.api_url.rstrip("/")

    print(f"\nGrantPilot Demo Readiness Check")
    print(f"  API: {base}\n")

    failures: list[str] = []
    token: str | None = None
    analysis_source: str | None = None

    for label, fn, needs_token in CHECKS:
        if needs_token and token is None:
            print(f"  [SKIP] {label} (login failed)")
            failures.append(label)
            continue
        try:
            if fn is _check_health:
                fn(base)
            elif fn is _check_login:
                token = fn(base)
            else:
                result = fn(base, token)
                if fn is _check_analysis:
                    analysis_source = result.get("analysis_source")
            print(f"  [PASS] {label}")
        except AssertionError as exc:
            print(f"  [FAIL] {label}: {exc}")
            failures.append(label)
        except urllib.error.URLError as exc:
            print(f"  [FAIL] {label}: connection error — {exc.reason}")
            failures.append(label)
        except Exception as exc:
            print(f"  [FAIL] {label}: {type(exc).__name__}: {exc}")
            failures.append(label)

    print()
    if failures:
        print(f"  {len(failures)} check(s) FAILED: {', '.join(failures)}")
        sys.exit(1)

    print("  All checks passed — app is demo-ready.")
    if analysis_source:
        print(f"  analysis_source: {analysis_source}")
    print()
    print("  Credentials:  demo@grantpilot.local / DemoGrantPilot123!")
    print("  Project:      proj_stem_2026 (BrightPath Youth Foundation)")
    if base == "http://localhost:8000":
        print("  Frontend:     http://localhost:3000")
        print("  API docs:     http://localhost:8000/docs")
    else:
        print(f"  API docs:     {base}/docs")
    print()


if __name__ == "__main__":
    main()
