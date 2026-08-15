"""Authorization-code flow against medbackend-oauth.

Confidential client only: client_secret is mandatory at /token and PKCE is not
implemented upstream (code_verifier is accepted and silently ignored), so the
exchange must happen server-side. Fine here; fatal for any future SPA or mobile app.
"""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass
from urllib.parse import parse_qs, urlencode, urlparse

from auth.oauth_config import FlowConfig
from services.medbackend.base_client import shared_client

# Upstream TTLs, from source: authorization code 600s, access 1h, refresh 7 days.
REFRESH_SKEW_SECONDS = 60


class OAuthError(RuntimeError):
    pass


@dataclass(slots=True)
class Tokens:
    access_token: str
    refresh_token: str
    expires_at: float

    def expired(self, now: float | None = None) -> bool:
        return (now or time.time()) >= self.expires_at - REFRESH_SKEW_SECONDS


def new_state() -> str:
    return secrets.token_urlsafe(24)


def authorization_url(cfg: FlowConfig, state: str) -> str:
    query = urlencode(
        {
            "client_id": cfg.client_id,
            "redirect_uri": cfg.redirect_uri,
            "response_type": "code",
            "state": state,
            "scope": "openid profile email",
        }
    )
    return f"{cfg.authorize_url}?{query}"


def code_from_redirect_url(redirect_url: str) -> str:
    """/login answers 200 JSON {"redirect_url": ...}, not a 302 — we parse it ourselves."""
    params = parse_qs(urlparse(redirect_url).query)
    code = (params.get("code") or [None])[0]
    if not code:
        raise OAuthError("no authorization code in redirect_url")
    return code


async def login_headless(cfg: FlowConfig, email: str, password: str, state: str) -> str:
    """Obtain an authorization code without a browser. For tests and seeding."""
    response = await shared_client().post(
        cfg.login_url,
        json={
            "email": email,
            "password": password,
            # Must be byte-identical to the value sent at /token.
            "redirect_uri": cfg.redirect_uri,
            "state": state,
        },
    )
    if response.status_code != 200:
        raise OAuthError(_login_hint(response.status_code, response.text))
    return code_from_redirect_url(response.json()["redirect_url"])


async def exchange_code(cfg: FlowConfig, code: str) -> Tokens:
    return await _token_request(
        cfg,
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": cfg.redirect_uri,
            "client_id": cfg.client_id,
            "client_secret": cfg.client_secret,
        },
    )


async def refresh(cfg: FlowConfig, refresh_token: str) -> Tokens:
    """Refresh tokens rotate on every use — persist the new one or the chain dies."""
    return await _token_request(
        cfg,
        {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": cfg.client_id,
            "client_secret": cfg.client_secret,
        },
    )


async def _token_request(cfg: FlowConfig, body: dict[str, str]) -> Tokens:
    response = await shared_client().post(cfg.token_url, json=body)
    if response.status_code != 200:
        raise OAuthError(
            f"token exchange failed ({response.status_code}): {response.text[:200]}. "
            "Most often redirect_uri differs by a byte from the one sent to /login, "
            "or the code is past its 10-minute life or already used."
        )
    payload = response.json()
    return Tokens(
        access_token=payload["access_token"],
        refresh_token=payload.get("refresh_token", ""),
        expires_at=time.time() + int(payload.get("expires_in", 3600)),
    )


def _login_hint(status: int, body: str) -> str:
    hints = {
        404: "no UserFlow for (project, entity_type) in medbackend-oauth's own DB",
        403: "email not verified, or entity_id empty because the FHIR resource is "
             "created at email verification rather than signup",
        401: "invalid credentials — also returned for an unknown user",
    }
    hint = hints.get(status, "")
    return f"login failed ({status}): {body[:200]}" + (f" — likely: {hint}" if hint else "")


def demo() -> None:
    from auth.oauth_config import PRACTITIONER, FlowConfig as FC

    cfg = FC(
        entity_type=PRACTITIONER,
        client_id="cid",
        client_secret="sec",
        project_uid="proj",
        base_url="https://auth.example",
        redirect_uri="http://localhost:5005/auth/callback",
    )
    url = authorization_url(cfg, "st8")
    assert "response_type=code" in url and "state=st8" in url
    assert "client_secret" not in url, "the secret must never reach a front-channel URL"

    assert code_from_redirect_url("http://localhost:5005/auth/callback?code=abc&state=st8") == "abc"
    try:
        code_from_redirect_url("http://localhost:5005/auth/callback?error=denied")
        raise AssertionError("missing code should raise")
    except OAuthError:
        pass

    now = 1_000_000.0
    fresh = Tokens("a", "r", now + 3600)
    assert not fresh.expired(now)
    # inside the skew window it counts as expired, so we refresh before failing a call
    assert Tokens("a", "r", now + 30).expired(now)
    assert Tokens("a", "r", now - 1).expired(now)
    print("oauth_service self-check ok")


if __name__ == "__main__":
    demo()
