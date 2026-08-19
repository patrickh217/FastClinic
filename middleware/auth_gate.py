"""Deny-by-default request gate.

Everything requires a session unless it is explicitly public. The inverse — a
decorator on each protected route — is how medbackend-frontend ended up with 102
of 251 routes unprotected.

This is a UX and blast-radius control, not authorization. It reads claims without
verifying the signature; backbone validates the token on every request and is the
real boundary. Never move an access decision here.
"""

from __future__ import annotations

import time

from starlette.responses import JSONResponse, RedirectResponse, Response

from auth import oauth_config, oauth_service
from auth.auth_utils import build_context

PUBLIC_EXACT = frozenset({
    "/login", "/logout", "/auth/callback", "/health", "/health/ready",
    "/compliance", "/favicon.ico", "/robots.txt", "/sitemap.xml",
})
PUBLIC_PREFIXES = ("/static/", "/set-lang/")

SESSION_KEYS = ("access_token", "refresh_token", "expires_at", "entity_type")


def is_public(path: str) -> bool:
    return path in PUBLIC_EXACT or path.startswith(PUBLIC_PREFIXES)


def clear_session(session) -> None:
    for key in SESSION_KEYS:
        session.pop(key, None)


def _deny(request) -> Response:
    """Shape the refusal to the caller: HTMX, API, or a browser."""
    if request.headers.get("HX-Request"):
        return Response(status_code=401, headers={"HX-Redirect": "/login"})
    if request.url.path.startswith("/api/"):
        return JSONResponse({"error": "unauthenticated"}, status_code=401)
    return RedirectResponse("/login", status_code=303)


async def auth_before(request, session):
    if is_public(request.url.path):
        return None

    token = session.get("access_token")
    if not token:
        return _deny(request)

    # Access tokens live an hour and refresh tokens rotate on every use, so the new
    # refresh token must be written back or the whole chain dies at the next renewal.
    expires_at = float(session.get("expires_at", 0))
    if time.time() >= expires_at - oauth_service.REFRESH_SKEW_SECONDS:
        refresh_token = session.get("refresh_token")
        if not refresh_token:
            clear_session(session)
            return _deny(request)
        try:
            cfg = oauth_config.flow(session.get("entity_type", oauth_config.PRACTITIONER))
            tokens = await oauth_service.refresh(cfg, refresh_token)
        except Exception:
            clear_session(session)
            return _deny(request)
        session["access_token"] = token = tokens.access_token
        session["refresh_token"] = tokens.refresh_token
        session["expires_at"] = tokens.expires_at

    request.scope["auth"] = build_context(
        token,
        session.get("practitioner_roles") or [],
        session.get("reference"),
    )
    return None


def demo() -> None:
    assert is_public("/login") and is_public("/static/css/app.css")
    assert is_public("/health/ready")
    assert not is_public("/patients")
    assert not is_public("/"), "the dashboard is not public"
    # a path that merely starts with a public word must not slip through
    assert not is_public("/logout-everyone")
    assert not is_public("/staticky")

    session = {"access_token": "a", "refresh_token": "r", "expires_at": 1, "other": "keep"}
    clear_session(session)
    assert session == {"other": "keep"}
    print("auth_gate self-check ok")


if __name__ == "__main__":
    demo()
