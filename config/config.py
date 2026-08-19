"""Centralised configuration.

Values resolve env-var first, then a per-environment default. Secrets have no
defaults — a missing one is a startup error, never a silent fallback.
"""

from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()

ENVIRONMENTS = ("development", "staging", "production")

# URLs are not env vars in normal operation — they are a three-branch table.
# Override per key when running against something unusual.
_DEFAULTS: dict[str, dict[str, str]] = {
    "MEDBACKEND_GRAPHQL_URL": {
        "development": "https://dev-backbone.medbackend.com/graphql",
        "staging": "https://staging-backbone.medbackend.com/graphql",
        "production": "https://backbone.medbackend.com/graphql",
    },
    "MEDBACKEND_APP_URL": {
        "development": "https://dev-api.medbackend.com",
        "staging": "https://staging-api.medbackend.com",
        "production": "https://api.medbackend.com",
    },
    "MEDBACKEND_OAUTH_URL": {
        "development": "https://dev-auth.medbackend.com",
        "staging": "https://staging-auth.medbackend.com",
        "production": "https://auth.medbackend.com",
    },
}

# Values that must never reach the wire. /health/ready fails while any is present,
# so a half-configured deploy is loud instead of subtly wrong.
PLACEHOLDERS = frozenset({"", "changeme", "PRODUCTION_PROJECT_ID", "TODO", "xxx"})

_SECRET_HINT = ("SECRET", "TOKEN", "PASSWORD", "KEY")


class ConfigError(RuntimeError):
    pass


def _env() -> str:
    value = os.getenv("ENVIRONMENT", "development").strip().lower()
    if value not in ENVIRONMENTS:
        raise ConfigError(f"ENVIRONMENT must be one of {ENVIRONMENTS}, got {value!r}")
    return value


def get(key: str, default: str | None = None) -> str:
    """Resolve a non-secret setting. Raises if there is no value anywhere."""
    value = os.getenv(key)
    if value:
        return value
    table = _DEFAULTS.get(key)
    if table:
        return table[_env()]
    if default is not None:
        return default
    raise ConfigError(f"{key} is not set and has no default")


def get_secret(key: str, required: bool = True) -> str:
    value = os.getenv(key, "")
    if required and value in PLACEHOLDERS:
        raise ConfigError(f"{key} is missing or still a placeholder")
    return value


def get_int(key: str, default: int) -> int:
    raw = os.getenv(key)
    return int(raw) if raw else default


def is_secret_key(key: str) -> bool:
    return any(hint in key.upper() for hint in _SECRET_HINT)


@lru_cache(maxsize=1)
def settings() -> dict[str, object]:
    return {
        "environment": _env(),
        "port": get_int("FASTCLINIC_PORT", 5005),
        "public_url": get("FASTCLINIC_PUBLIC_URL", "http://localhost:5005"),
        "session_secret": get_secret("FASTCLINIC_SECRET"),
        "project_id": get_secret("MEDBACKEND_PROJECT_ID"),
        "graphql_url": get("MEDBACKEND_GRAPHQL_URL"),
        "app_url": get("MEDBACKEND_APP_URL"),
        "oauth_url": get("MEDBACKEND_OAUTH_URL"),
        "redirect_uri": get("MEDBACKEND_REDIRECT_URI"),
        "timeout_seconds": get_int("MEDBACKEND_TIMEOUT_SECONDS", 30),
        "max_retries": get_int("MEDBACKEND_MAX_RETRIES", 3),
    }


def readiness() -> tuple[bool, list[str]]:
    """Names of settings that are missing or still placeholders. Never values."""
    problems: list[str] = []
    for key in (
        "FASTCLINIC_SECRET",
        "MEDBACKEND_PROJECT_ID",
        "MEDBACKEND_REDIRECT_URI",
        "MEDBACKEND_PRACTITIONER_CLIENT_ID",
        "MEDBACKEND_PRACTITIONER_CLIENT_SECRET",
    ):
        if os.getenv(key, "") in PLACEHOLDERS:
            problems.append(key)
    return (not problems), problems


def demo() -> None:
    """Self-check: placeholders are caught, secrets never leak into errors."""
    os.environ["ENVIRONMENT"] = "development"
    assert get("MEDBACKEND_OAUTH_URL") == "https://dev-auth.medbackend.com"
    os.environ["ENVIRONMENT"] = "production"
    assert get("MEDBACKEND_OAUTH_URL") == "https://auth.medbackend.com"

    os.environ["MEDBACKEND_PROJECT_ID"] = "PRODUCTION_PROJECT_ID"
    try:
        get_secret("MEDBACKEND_PROJECT_ID")
        raise AssertionError("placeholder should have been rejected")
    except ConfigError as exc:
        assert "PRODUCTION_PROJECT_ID" not in str(exc), "error text leaked the value"

    # readiness() reads the real environment, so the check controls it explicitly
    # rather than inheriting whatever the caller happened to export.
    for key in (
        "FASTCLINIC_SECRET",
        "MEDBACKEND_REDIRECT_URI",
        "MEDBACKEND_PRACTITIONER_CLIENT_ID",
        "MEDBACKEND_PRACTITIONER_CLIENT_SECRET",
    ):
        os.environ.pop(key, None)
    os.environ["MEDBACKEND_PROJECT_ID"] = "real-value"

    ok, problems = readiness()
    assert not ok
    assert "FASTCLINIC_SECRET" in problems
    assert "MEDBACKEND_PROJECT_ID" not in problems, "a set value must not be flagged"
    assert "real-value" not in " ".join(problems), "readiness leaked a value"
    assert is_secret_key("MEDBACKEND_PRACTITIONER_CLIENT_SECRET")

    for key in ("FASTCLINIC_SECRET", "MEDBACKEND_REDIRECT_URI",
                "MEDBACKEND_PRACTITIONER_CLIENT_ID", "MEDBACKEND_PRACTITIONER_CLIENT_SECRET"):
        os.environ[key] = "set"
    ok, problems = readiness()
    assert ok and not problems
    print("config self-check ok")


if __name__ == "__main__":
    demo()
