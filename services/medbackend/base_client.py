"""Shared HTTP client for every outbound call to MedBackend.

One pooled httpx.AsyncClient for the process, closed in the app lifespan.
Nothing else in the codebase may talk to MedBackend directly.
"""

from __future__ import annotations

import httpx

from config import config

_client: httpx.AsyncClient | None = None


def shared_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        settings = config.settings()
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings["timeout_seconds"], connect=5.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            http2=True,
        )
    return _client


async def close_shared_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


class BaseApiClient:
    """Carries the two headers backbone requires and nothing more."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._auth_token: str | None = None
        self._project_id: str | None = None

    def set_auth_token(self, token: str | None) -> "BaseApiClient":
        self._auth_token = token
        return self

    def set_project_id(self, project_id: str | None) -> "BaseApiClient":
        self._project_id = project_id
        return self

    def headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        out = {"Content-Type": "application/json"}
        if self._auth_token:
            out["Authorization"] = f"Bearer {self._auth_token}"
        # Missing on a backbone call is an HTTP 400 before GraphQL even runs,
        # with code MISSING_PROJECT_UID. It does not look like an auth error.
        if self._project_id:
            out["X-Project-ID"] = self._project_id
        if extra:
            out.update(extra)
        return out
