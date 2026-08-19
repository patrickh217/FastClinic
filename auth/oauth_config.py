"""medbackend-oauth endpoints.

Every endpoint is prefixed /oauth/{project_uid}/{entity_type}/ — there is no bare
/oauth/authorize. The path segment is .capitalize()-normalised upstream, and the
service generates lowercase itself, so we send lowercase.

Prefer discovery over these constructions where possible: medbackend-app's
GET /projects/{project_uid}/connection-info returns the same URLs plus the
client_id and allowed_redirect_uris for each flow.
"""

from __future__ import annotations

from dataclasses import dataclass

from config import config

PRACTITIONER = "Practitioner"
PATIENT = "Patient"
ENTITY_TYPES = (PRACTITIONER, PATIENT)


@dataclass(frozen=True, slots=True)
class FlowConfig:
    entity_type: str
    client_id: str
    client_secret: str
    project_uid: str
    base_url: str
    redirect_uri: str

    @property
    def _prefix(self) -> str:
        return f"{self.base_url.rstrip('/')}/oauth/{self.project_uid}/{self.entity_type.lower()}"

    @property
    def authorize_url(self) -> str:
        return f"{self._prefix}/authorize"

    @property
    def login_url(self) -> str:
        """Returns JSON {"redirect_url": ...}, NOT a 302. Used headlessly in tests."""
        return f"{self._prefix}/login"

    @property
    def token_url(self) -> str:
        return f"{self._prefix}/token"

    @property
    def jwks_url(self) -> str:
        return f"{self._prefix}/.well-known/jwks.json"


def flow(entity_type: str) -> FlowConfig:
    if entity_type not in ENTITY_TYPES:
        raise ValueError(f"entity_type must be one of {ENTITY_TYPES}, got {entity_type!r}")
    settings = config.settings()
    prefix = "MEDBACKEND_PRACTITIONER" if entity_type == PRACTITIONER else "MEDBACKEND_PATIENT"
    return FlowConfig(
        entity_type=entity_type,
        client_id=config.get_secret(f"{prefix}_CLIENT_ID"),
        # Issued once at user-flow creation and NOT rotatable — the rotation route
        # medbackend-app calls does not exist upstream. Losing it means a new flow.
        client_secret=config.get_secret(f"{prefix}_CLIENT_SECRET"),
        project_uid=settings["project_id"],
        base_url=settings["oauth_url"],
        redirect_uri=settings["redirect_uri"],
    )


def demo() -> None:
    cfg = FlowConfig(
        entity_type=PRACTITIONER,
        client_id="medbackend_c82bf761_practitioner",
        client_secret="s",
        project_uid="c82bf761-d720-4eb8-92e7-3719da7342fd",
        base_url="https://dev-auth.medbackend.com/",
        redirect_uri="http://localhost:5005/auth/callback",
    )
    assert cfg.authorize_url == (
        "https://dev-auth.medbackend.com/oauth/"
        "c82bf761-d720-4eb8-92e7-3719da7342fd/practitioner/authorize"
    ), cfg.authorize_url
    assert cfg.token_url.endswith("/practitioner/token")
    assert "//oauth" not in cfg.authorize_url, "trailing slash must not double up"

    try:
        flow("Doctor")
        raise AssertionError("invalid entity_type accepted")
    except ValueError:
        pass
    print("oauth_config self-check ok")


if __name__ == "__main__":
    demo()
