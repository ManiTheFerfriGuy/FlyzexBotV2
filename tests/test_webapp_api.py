from __future__ import annotations

import json
from pathlib import Path

import asyncio

import pytest
from fastapi.testclient import TestClient

from webapp.server import app as webapp


@pytest.fixture(autouse=True)
def cleanup_storage_files():
    # Ensure test-created storage artifacts are removed after tests
    yield
    for p in (
        Path("data/storage.json"),
        Path("data/storage.sqlite"),
    ):
        try:
            if p.exists():
                p.unlink()
        except Exception:
            # Best-effort cleanup
            pass


def test_protected_endpoints_require_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    # Ensure ADMIN_API_KEY is not configured -> should return 503
    monkeypatch.delenv("ADMIN_API_KEY", raising=False)

    with TestClient(webapp) as client:
        r = client.get("/api/admins")
        assert r.status_code == 503
        assert "Admin API key" in (r.json().get("detail") or "")

    # Configure ADMIN_API_KEY, but do not send header -> should return 401
    monkeypatch.setenv("ADMIN_API_KEY", "test_admin_key")

    with TestClient(webapp) as client:
        r = client.get("/api/admins")
        assert r.status_code == 401
        assert (r.json().get("detail") or "").lower() == "unauthorized"


def test_admin_crud_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    # Configure secrets for lifespan
    monkeypatch.setenv("ADMIN_API_KEY", "test_admin_key")

    headers = {"X-Admin-Api-Key": "test_admin_key"}

    with TestClient(webapp) as client:
        # List admins (empty)
        r = client.get("/api/admins", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 0
        assert data["admins"] == []

        # Create admin
        payload = {"user_id": 9999, "username": "tester", "full_name": "Tester"}
        r = client.post("/api/admins", headers={**headers, "Content-Type": "application/json"}, json=payload)
        assert r.status_code == 200
        assert r.json()["status"] in {"created", "updated"}

        # Get admin
        r = client.get("/api/admins/9999", headers=headers)
        assert r.status_code == 200
        admin = r.json().get("admin")
        assert admin and admin["user_id"] == 9999

        # Insights should be accessible with key
        r = client.get("/api/applications/insights", headers=headers)
        assert r.status_code == 200
        assert "pending" in r.json()

        # Delete admin
        r = client.delete("/api/admins/9999", headers=headers)
        assert r.status_code == 204

        # Get admin again -> 404
        r = client.get("/api/admins/9999", headers=headers)
        assert r.status_code == 404


def test_pending_applications_filters_and_dashboard(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADMIN_API_KEY", "test_admin_key")

    headers = {"X-Admin-Api-Key": "test_admin_key"}

    with TestClient(webapp) as client:
        storage = client.app.state.storage

        async def _seed() -> None:
            await storage.add_application(
                1001,
                full_name="Alpha One",
                username="alpha",
                answer="First answer",
                language_code="fa",
                responses=[],
            )
            await storage.add_application(
                1002,
                full_name="Beta Two",
                username="beta",
                answer="Second insight",
                language_code="en",
                responses=[],
            )
            await storage.add_application(
                1003,
                full_name="Gamma Three",
                username="gamma",
                answer="Third detail",
                language_code="fa",
                responses=[],
            )

        asyncio.run(_seed())

        # Provide deterministic ordering for tests
        storage._state.applications[1001].created_at = "2023/01/01 · 09:00:00 UTC"  # type: ignore[attr-defined]
        storage._state.applications[1002].created_at = "2023/01/02 · 09:00:00 UTC"  # type: ignore[attr-defined]
        storage._state.applications[1003].created_at = "2023/01/03 · 09:00:00 UTC"  # type: ignore[attr-defined]
        asyncio.run(storage.save())

        params = {"limit": 1, "sort": "recent"}
        r = client.get("/api/applications/pending", headers=headers, params=params)
        assert r.status_code == 200
        payload = r.json()
        assert payload["total"] == 3
        assert len(payload["applications"]) == 1
        assert payload["applications"][0]["user_id"] == 1003

        params = {"language": ["fa"], "sort": "oldest"}
        r = client.get("/api/applications/pending", headers=headers, params=params)
        assert r.status_code == 200
        payload = r.json()
        assert payload["total"] == 2
        assert [app["user_id"] for app in payload["applications"]] == [1001, 1003]

        params = {"search": "beta"}
        r = client.get("/api/applications/pending", headers=headers, params=params)
        assert r.status_code == 200
        payload = r.json()
        assert payload["total"] == 1
        assert payload["applications"][0]["user_id"] == 1002

        r = client.get("/api/applications/1002", headers=headers)
        assert r.status_code == 200
        detail = r.json()
        assert detail["application"]["user_id"] == 1002
        assert detail["history"]["status"] == "pending"

        # Mark two applications as decided to exercise dashboard aggregation
        asyncio.run(storage.pop_application(1002))
        asyncio.run(storage.mark_application_status(1002, "approved"))
        asyncio.run(storage.pop_application(1003))
        asyncio.run(storage.mark_application_status(1003, "denied"))

        r = client.get("/api/applications/dashboard", headers=headers)
        assert r.status_code == 200
        dashboard = r.json()
        assert dashboard["pending"] == 1
        assert dashboard["approved"] == 1
        assert dashboard["denied"] == 1
        assert dashboard["pending_by_language"]["fa"] == 1
        assert dashboard["approval_rate"] == pytest.approx(0.5)

        # Requesting unknown application should yield 404
        r = client.get("/api/applications/9999", headers=headers)
        assert r.status_code == 404


def test_prefixed_paths_are_served(monkeypatch: pytest.MonkeyPatch) -> None:
    with TestClient(webapp) as client:
        client.app.state.base_path = "/demo"
        client.app.root_path = "/demo"

        prefixed_response = client.get("/demo/api/leaderboard/xp/top?limit=3")
        assert prefixed_response.status_code == 200
        assert prefixed_response.json()["leaderboard"] == []


def test_global_xp_top_persists_plain_json(monkeypatch: pytest.MonkeyPatch) -> None:
    with TestClient(webapp) as client:
        storage = client.app.state.storage
        settings = client.app.state.settings
        storage_path = settings.storage.path

        async def _seed() -> None:
            await storage.add_xp(2001, 555, 15, full_name="Alpha One")
            await storage.add_xp(2002, 666, 25, username="@beta")
            await storage.add_xp(2003, 555, 30)

        asyncio.run(_seed())

    payload = json.loads(storage_path.read_text(encoding="utf-8"))
    assert "xp" in payload
    assert payload["xp"]["2001"]["555"] == 15
    assert payload["xp"]["2003"]["555"] == 30

    with TestClient(webapp) as client:
        response = client.get("/api/leaderboard/xp/top?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert [entry["user_id"] for entry in data["leaderboard"]] == [555, 666]
        assert data["leaderboard"][0]["xp"] == 45
        assert data["leaderboard"][0]["full_name"] == "Alpha One"
        assert data["leaderboard"][1]["xp"] == 25
        assert data["leaderboard"][1]["username"] == "beta"

        plain_response = client.get("/api/leaderboard/xp/top?limit=3")
        assert plain_response.status_code == 200
