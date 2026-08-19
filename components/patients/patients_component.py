"""Page assemblers for the patients feature. Pure — no I/O."""

from __future__ import annotations

from fasthtml.common import A, Div, H2, P, Span

from components.common.lazy import lazy_content
from components.layout import page_title
from components.patients.ui.table import search_box


def patients_component(term: str = ""):
    return Div(
        page_title(
            "Patients",
            "Records live in MedBackend. Search matches name, identifier, date of "
            "birth and contact details — there is no free-text search across the record.",
        ),
        search_box(term),
        lazy_content(f"/patients/table?name={term}", section_id="patient-table-container"),
        cls="page",
    )


def _field(label: str, value):
    return Div(Span(label, cls="field-label"), Span(value or "—", cls="field-value"), cls="field")


def patient_detail_component(patient: dict):
    address = (patient.get("address") or [{}])[0]
    lines = ", ".join(filter(None, [
        " ".join(address.get("line") or []),
        address.get("city", ""),
        address.get("postalCode", ""),
        address.get("country", ""),
    ]))
    return Div(
        A("← All patients", href="/patients", cls="back-link"),
        page_title(patient["name"]),
        Div(
            _field("Gender", patient["gender"]),
            _field("Date of birth", patient["birth_date"]),
            _field("Age", patient["age"]),
            _field("Phone", patient["phone"]),
            _field("Email", patient["email"]),
            _field("Address", lines),
            _field("GP", patient.get("general_practitioner")),
            cls="field-grid",
        ),
        H2("Clinical record"),
        lazy_content(f"/patients/{patient['id']}/encounters", section_id="patient-encounters"),
        cls="page",
    )
