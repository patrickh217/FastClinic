"""Session auth context and role derivation.

The JWT carries no `roles` and no `scope` — the complete payload is sub, iss, aud,
project_uid, entity_type, entity_id, email, iat, exp. backbone treats `entity_type`
as the role, so the whole server-side vocabulary is Patient | Practitioner | Device
| RelatedPerson.

Anything finer is FHIR `PractitionerRole`, which is also what backbone itself checks
when a rule carries required_role_system / required_role_code. So the UI's capability
map is derived from the practitioner's PractitionerRole resources, never from a local
table. This is a UX control only — real authorization happens in backbone.
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field

PRACTITIONER_ROLE_SYSTEM = "http://terminology.hl7.org/CodeSystem/practitioner-role"

# Capabilities gate what the nav offers. backbone decides what actually returns data.
ALL_CAPABILITIES = frozenset(
    {"patients", "clinical", "scheduling", "billing", "activation", "admin"}
)

_ROLE_CAPABILITIES: dict[str, frozenset[str]] = {
    "doctor": frozenset({"patients", "clinical", "scheduling", "activation"}),
    "nurse": frozenset({"patients", "clinical", "scheduling"}),
    "pharmacist": frozenset({"patients", "clinical"}),
    "ict": ALL_CAPABILITIES,
    "researcher": frozenset({"patients"}),
    "teacher": frozenset({"patients"}),
}

# A practitioner with no PractitionerRole we recognise still has to be able to work.
# backbone is the real gate, so a permissive nav here cannot leak data — it can only
# show a screen that then comes back empty or denied.
_DEFAULT_PRACTITIONER = frozenset({"patients", "clinical", "scheduling"})
_PATIENT = frozenset({"portal"})


@dataclass(slots=True)
class AuthContext:
    entity_type: str
    entity_id: str
    project_uid: str
    email: str
    reference: str | None = None
    capabilities: frozenset[str] = field(default_factory=frozenset)

    @property
    def is_patient(self) -> bool:
        return self.entity_type == "Patient"

    def can(self, capability: str) -> bool:
        return capability in self.capabilities


def decode_claims(token: str) -> dict:
    """Read claims WITHOUT verifying the signature.

    Deliberate: backbone validates against medbackend-oauth's JWKS on every request.
    Verifying here would duplicate that and tempt us into treating this as
    authorization. It is not — it decides what to render, nothing more.
    """
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload))
    except (IndexError, ValueError) as exc:
        raise ValueError("malformed JWT") from exc


def capabilities_from_roles(practitioner_roles: list[dict]) -> frozenset[str]:
    """Union the capabilities of every PractitionerRole coding we recognise."""
    granted: set[str] = set()
    for role in practitioner_roles or []:
        for concept in role.get("code") or []:
            for coding in concept.get("coding") or []:
                if coding.get("system") != PRACTITIONER_ROLE_SYSTEM:
                    continue
                granted |= _ROLE_CAPABILITIES.get(coding.get("code", ""), frozenset())
    return frozenset(granted) or _DEFAULT_PRACTITIONER


def build_context(token: str, practitioner_roles: list[dict] | None = None,
                  reference: str | None = None) -> AuthContext:
    claims = decode_claims(token)
    entity_type = claims.get("entity_type", "")
    capabilities = _PATIENT if entity_type == "Patient" else capabilities_from_roles(
        practitioner_roles or []
    )
    return AuthContext(
        entity_type=entity_type,
        # Empty until email verification creates the FHIR resource upstream; a blank
        # entity_id fails every compartment check, so callers must treat it as unusable.
        entity_id=claims.get("entity_id", ""),
        project_uid=claims.get("project_uid", ""),
        email=claims.get("email", ""),
        reference=reference,
        capabilities=capabilities,
    )


def demo() -> None:
    def fake_jwt(payload: dict) -> str:
        body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        return f"header.{body}.signature"

    token = fake_jwt(
        {"entity_type": "Practitioner", "entity_id": "Practitioner/1",
         "project_uid": "p", "email": "a@b.c"}
    )
    ctx = build_context(token, [
        {"code": [{"coding": [{"system": PRACTITIONER_ROLE_SYSTEM, "code": "doctor"}]}]}
    ])
    assert ctx.entity_type == "Practitioner" and not ctx.is_patient
    assert ctx.can("clinical") and ctx.can("activation")
    assert not ctx.can("billing"), "doctor must not pick up billing by accident"

    # unknown coding -> permissive default, never an empty set that locks the user out
    unknown = build_context(token, [
        {"code": [{"coding": [{"system": "http://example/other", "code": "wizard"}]}]}
    ])
    assert unknown.capabilities == _DEFAULT_PRACTITIONER

    # two roles union rather than the last one winning
    both = build_context(token, [
        {"code": [{"coding": [{"system": PRACTITIONER_ROLE_SYSTEM, "code": "nurse"}]}]},
        {"code": [{"coding": [{"system": PRACTITIONER_ROLE_SYSTEM, "code": "ict"}]}]},
    ])
    assert both.can("admin") and both.can("billing")

    patient = build_context(fake_jwt({"entity_type": "Patient", "entity_id": "Patient/9"}))
    assert patient.is_patient and patient.capabilities == _PATIENT
    assert not patient.can("clinical")

    unverified = build_context(fake_jwt({"entity_type": "Practitioner", "entity_id": ""}))
    assert unverified.entity_id == "", "blank entity_id must survive to be checked"

    try:
        decode_claims("not-a-jwt")
        raise AssertionError("malformed token should raise")
    except ValueError:
        pass
    print("auth_utils self-check ok")


if __name__ == "__main__":
    demo()
