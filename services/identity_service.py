"""Who the signed-in user is, resolved from FHIR after the token arrives.

The JWT carries entity_type and entity_id and nothing else useful — no roles, no
scope. Everything the UI needs beyond that comes from FHIR: `Me { reference }`
for compartment-scoped queries, and PractitionerRole for capabilities.

Both lookups are best-effort by design. A practitioner whose PractitionerRole is
missing still gets a working default nav, and backbone remains the real gate — so
degrading here costs a menu entry, never a security boundary.
"""

from __future__ import annotations

from services.medbackend.fhir_client import FhirClient

PRACTITIONER_ROLE_FIELDS = (
    "id code { coding { system code display } } specialty { coding { code display } }"
)


class IdentityService:
    async def resolve(self, token: str, entity_id: str, is_patient: bool) -> dict:
        client = FhirClient(auth_token=token)

        try:
            reference = await client.me()
        except Exception:
            reference = None

        roles: list[dict] = []
        # entity_id is empty until email verification creates the FHIR resource
        # upstream; searching on an empty practitioner would match everything.
        if not is_patient and entity_id:
            try:
                found = await client.search(
                    "PractitionerRole", PRACTITIONER_ROLE_FIELDS,
                    {"practitioner": entity_id},
                )
                roles = found.items
            except Exception:
                roles = []

        return {"reference": reference, "practitioner_roles": roles}


identity_service = IdentityService()
