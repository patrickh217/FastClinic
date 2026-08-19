"""Turns service calls into FT, and exceptions into rendered states.

Routes stay thin because nothing below this layer is allowed to raise past it.
"""

from __future__ import annotations

from fasthtml.common import Div, P

from components.common.states import error_state, render_list
from components.patients.patients_component import patient_detail_component
from components.patients.ui.table import patient_table
from services.clinical_service import clinical_service
from services.medbackend.fhir_client import BackboneError
from services.patients_service import patients_service


class PatientHandlers:
    async def table(self, token: str | None, term: str = ""):
        try:
            result = await patients_service.search(token, {"name": term} if term else None)
        except BackboneError as exc:
            return error_state(str(exc), denied=exc.denied)
        return patient_table(result)

    async def detail(self, token: str | None, patient_id: str):
        try:
            patient = await patients_service.get(token, patient_id)
        except BackboneError as exc:
            return error_state(str(exc), denied=exc.denied)
        if patient is None:
            # backbone returns null both for "absent" and for a row-level RBAC
            # denial, with no error either way. We cannot tell them apart.
            return error_state(
                "This record is not available. It may not exist, or your role may "
                "not cover it — MedBackend does not distinguish the two."
            )
        return patient_detail_component(patient)

    async def encounters(self, token: str | None, patient_id: str):
        try:
            result = await clinical_service.encounters_for(token, patient_id)
        except BackboneError as exc:
            return error_state(str(exc), denied=exc.denied)
        return Div(
            render_list(
                result,
                lambda rows: Div(*[
                    Div(
                        P(row["date"] or "Undated", cls="encounter-date"),
                        P(row["type"] or row["status"], cls="encounter-type"),
                        cls="encounter-row",
                    )
                    for row in rows
                ]),
                noun="this patient's visit history",
                empty_message="No visits recorded.",
            ),
            id="patient-encounters",
        )


patient_handlers = PatientHandlers()
