"""HTMX fragment endpoints for the patients feature.

Registered before the page routes so the static segments win over the
`/patients/{patient_id}` wildcard.
"""

from __future__ import annotations

from handlers.patients_handlers import patient_handlers


def register_patient_data_routes(rt) -> None:

    @rt("/patients/table")
    async def get(session, name: str = ""):
        return await patient_handlers.table(session.get("access_token"), name)

    @rt("/patients/{patient_id}/encounters")
    async def get(session, patient_id: str):
        return await patient_handlers.encounters(session.get("access_token"), patient_id)
