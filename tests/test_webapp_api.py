from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from webapp.server import app as webapp


@pytest.fixture(autouse=True)
def cleanup_storage_files():
    # Ensure test-created storage artifacts are removed after tests
    yield
    for p in (
        Path("data/storage.json.enc"),
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
    # cryptography is already a project dependency
    from cryptography.fernet import Fernet

    key = Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("BOT_SECRET_KEY", key)
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
