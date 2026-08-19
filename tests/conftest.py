"""Shared fixtures.

The auth bypass is autouse with an opt-out marker rather than per-module patching:
the gate denies every non-public path, so without it every route test would just
assert a redirect to /login. Tests that exercise the gate itself carry
@pytest.mark.real_auth_gate.
"""

from __future__ import annotations

import base64
import json
import os

import pytest

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("FASTCLINIC_SECRET", "test-secret-not-a-real-key")
os.environ.setdefault("MEDBACKEND_PROJECT_ID", "test-project")
os.environ.setdefault("MEDBACKEND_REDIRECT_URI", "http://localhost:5005/auth/callback")
os.environ.setdefault("MEDBACKEND_PRACTITIONER_CLIENT_ID", "test-client")
os.environ.setdefault("MEDBACKEND_PRACTITIONER_CLIENT_SECRET", "test-secret")


def make_token(**claims) -> str:
    payload = {
        "entity_type": "Practitioner",
        "entity_id": "Practitioner/test-1",
        "project_uid": "test-project",
        "email": "clinician@example.test",
        **claims,
    }
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    return f"header.{body}.signature"


@pytest.fixture(autouse=True)
def bypass_auth_gate(request, monkeypatch):
    if "real_auth_gate" in request.keywords:
        yield
        return

    from auth.auth_utils import build_context
    import middleware.auth_gate as gate

    async def allow(req, session):
        req.scope["auth"] = build_context(
            make_token(),
            [{"code": [{"coding": [
                {"system": "http://terminology.hl7.org/CodeSystem/practitioner-role",
                 "code": "doctor"}
            ]}]}],
            reference="Practitioner/test-1",
        )
        return None

    monkeypatch.setattr(gate, "auth_before", allow)
    yield


@pytest.fixture
def client(bypass_auth_gate):
    """A test client built AFTER the bypass is installed, so Beforeware picks it up."""
    import importlib

    import app as app_module
    importlib.reload(app_module)

    from starlette.testclient import TestClient
    return TestClient(app_module.app)


@pytest.fixture
def raw_client():
    """Untouched app, for tests that assert on the real gate."""
    import importlib

    import middleware.auth_gate  # noqa: F401  - ensure the real module is loaded
    import app as app_module
    importlib.reload(app_module)

    from starlette.testclient import TestClient
    return TestClient(app_module.app)
