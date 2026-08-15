"""Overview tiles.

Every figure here is the size of one fetched page, never a clinic-wide total —
backbone reports no total and offers no aggregation. The tiles say so rather than
presenting a number that reads as authoritative.
"""

from __future__ import annotations

from fasthtml.common import Div, P

from components.common.states import error_state
from components.layout import kpi_card, kpi_grid
from services.medbackend.fhir_client import BackboneError, FhirClient


async def _count(token: str | None, resource_type: str, fields: str,
                 params: dict[str, str] | None = None) -> tuple[str, bool]:
    """Returns the figure to display and whether it is trustworthy at all."""
    result = await FhirClient(auth_token=token).search(
        resource_type, fields, params, count=1000
    )
    if not result.certain and not len(result):
        return "?", False
    return (f"{len(result)}+" if result.capped else str(len(result))), True


class OverviewHandlers:
    async def summary(self, ctx, token: str | None):
        try:
            patients, patients_ok = await _count(token, "Patient", "id")
            encounters, encounters_ok = await _count(token, "Encounter", "id")
            appointments, appointments_ok = await _count(
                token, "Appointment", "id", {"status": "booked"}
            )
        except BackboneError as exc:
            return Div(error_state(str(exc), denied=exc.denied), id="overview-summary")

        return Div(
            kpi_grid(
                kpi_card("Patients fetched", patients, "not a clinic total", warn=not patients_ok),
                kpi_card("Visits fetched", encounters, "not a clinic total", warn=not encounters_ok),
                kpi_card("Booked appointments", appointments, "not a clinic total",
                         warn=not appointments_ok),
            ),
            P(
                "A “?” means the record service returned nothing and could not "
                "confirm whether that is genuinely zero. A “+” means the page limit "
                "was reached and there are more.",
                cls="page-note",
            ),
            id="overview-summary",
        )


overview_handlers = OverviewHandlers()
