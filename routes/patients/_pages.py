"""Full-page patient routes."""

from __future__ import annotations

from components.layout import page
from components.patients.patients_component import patients_component
from config import config
from handlers.patients_handlers import patient_handlers


def register_patient_page_routes(rt) -> None:

    @rt("/patients")
    def get(request, name: str = ""):
        ctx = request.scope["auth"]
        return page(
            "patients",
            patients_component(name),
            ctx=ctx,
            environment=config.settings()["environment"],
            title="Patients — FastClinic",
        )

    @rt("/patients/{patient_id}")
    async def get(request, session, patient_id: str):
        ctx = request.scope["auth"]
        body = await patient_handlers.detail(session.get("access_token"), patient_id)
        return page(
            "patients",
            body,
            ctx=ctx,
            environment=config.settings()["environment"],
            title="Patient — FastClinic",
        )
