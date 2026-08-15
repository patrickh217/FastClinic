"""The patient table and its search box. Pure — rows arrive as plain dicts."""

from __future__ import annotations

from fasthtml.common import A, Div, Form, Input, Table, Tbody, Td, Th, Thead, Tr

from components.common.states import render_list

TABLE_ID = "patient-table-container"


def search_box(term: str = ""):
    return Form(
        Input(
            type="search",
            name="name",
            value=term,
            placeholder="Search by name…",
            # delay: prevents one request per keystroke
            hx_get="/patients/table",
            hx_trigger="keyup changed delay:400ms, search",
            hx_target=f"#{TABLE_ID}",
            hx_swap="outerHTML",
            aria_label="Search patients by name",
        ),
        cls="search-box",
        role="search",
    )


def _rows(rows: list[dict]):
    return Table(
        Thead(Tr(*[Th(h) for h in ("Name", "Gender", "Date of birth", "Age", "Phone")])),
        Tbody(*[
            Tr(
                Td(A(row["name"], href=f"/patients/{row['id']}")),
                Td(row["gender"] or "—"),
                Td(row["birth_date"] or "—"),
                Td(str(row["age"]) if row["age"] is not None else "—"),
                Td(row["phone"] or "—"),
            )
            for row in rows
        ]),
        cls="data-table",
    )


def patient_table(result):
    """Sets its own container id so repeated HTMX swaps stay self-identifying."""
    return Div(
        render_list(
            result,
            _rows,
            noun="the patient list",
            empty_message="No patients match this search.",
            empty_hint="Try a shorter name fragment — search matches on name fields only.",
        ),
        id=TABLE_ID,
    )
