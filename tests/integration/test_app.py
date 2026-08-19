"""Route and middleware behaviour through the test client."""

from __future__ import annotations

import pytest


@pytest.mark.integration
def test_health_is_always_up(raw_client):
    """GIVEN a running process WHEN /health is called THEN it answers 200."""
    response = raw_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.integration
def test_readiness_names_missing_settings_without_values(raw_client, monkeypatch):
    """GIVEN a placeholder secret WHEN /health/ready is called THEN it 503s with
    the setting NAME and never its value."""
    monkeypatch.setenv("MEDBACKEND_PRACTITIONER_CLIENT_SECRET", "")
    response = raw_client.get("/health/ready")
    assert response.status_code == 503
    body = response.json()
    assert "MEDBACKEND_PRACTITIONER_CLIENT_SECRET" in body["missing"]
    assert "test-secret" not in response.text


@pytest.mark.integration
def test_security_headers_present(raw_client):
    """GIVEN any response THEN the security headers are attached."""
    headers = raw_client.get("/health").headers
    assert headers["x-frame-options"] == "DENY"
    assert headers["x-content-type-options"] == "nosniff"
    assert "frame-ancestors 'none'" in headers["content-security-policy"]


@pytest.mark.integration
@pytest.mark.real_auth_gate
def test_gate_denies_by_default(raw_client):
    """GIVEN no session WHEN a protected page is requested THEN it redirects to login."""
    response = raw_client.get("/patients", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


@pytest.mark.integration
@pytest.mark.real_auth_gate
def test_gate_denies_htmx_with_hx_redirect(raw_client):
    """GIVEN an HTMX request WHEN unauthenticated THEN it gets 401 + HX-Redirect,
    because a 303 inside a swap would inject the login page into a fragment."""
    response = raw_client.get(
        "/patients", follow_redirects=False, headers={"HX-Request": "true"}
    )
    assert response.status_code == 401
    assert response.headers["hx-redirect"] == "/login"


@pytest.mark.integration
@pytest.mark.real_auth_gate
def test_public_paths_stay_open(raw_client):
    """GIVEN no session THEN the login page still renders."""
    response = raw_client.get("/login")
    assert response.status_code == 200
    assert "Staff sign-in" in response.text


@pytest.mark.integration
def test_patients_page_renders_shell_without_waiting_on_backbone(client):
    """GIVEN an authenticated session WHEN /patients is requested THEN the shell
    returns immediately with a lazy placeholder, not a blocked network call."""
    response = client.get("/patients")
    assert response.status_code == 200
    assert 'hx-get="/patients/table' in response.text
    assert 'hx-trigger="load"' in response.text


@pytest.mark.integration
def test_nav_reflects_capabilities(client):
    """GIVEN a doctor THEN clinical nav appears and the patient portal does not."""
    text = client.get("/patients").text
    assert "/appointments" in text
    assert 'href="/portal"' not in text
