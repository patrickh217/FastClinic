"""Patients: FHIR <-> UI transforms and the searches the UI is allowed to offer.

Only search parameters that backbone actually generates are exposed. There is no
_sort and no _lastUpdated, so no "recent patients" view can exist — the finder is
built around filters instead.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from services.medbackend.fhir_client import FhirClient, SearchResult

LIST_FIELDS = """
id active gender birthDate
name { family given }
telecom { system value }
identifier { system value }
"""

DETAIL_FIELDS = LIST_FIELDS + """
address { line city postalCode country }
generalPractitioner { reference display }
"""

# Backbone's generated Patient search arguments, minus the ones the UI has no use
# for. Anything absent here does not exist upstream — do not add speculatively.
SEARCHABLE = ("name", "family", "given", "identifier", "birthdate", "phone", "email")


def full_name(resource: dict[str, Any]) -> str:
    names = resource.get("name") or []
    if not names:
        return "(no name)"
    first = names[0]
    given = " ".join(first.get("given") or [])
    return f"{given} {first.get('family', '')}".strip() or "(no name)"


def contact(resource: dict[str, Any], system: str) -> str:
    for entry in resource.get("telecom") or []:
        if entry.get("system") == system and entry.get("value"):
            return entry["value"]
    return ""


def age(birth_date: str | None) -> int | None:
    if not birth_date:
        return None
    try:
        born = date.fromisoformat(birth_date[:10])
    except ValueError:
        return None
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def to_row(resource: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": resource.get("id", ""),
        "name": full_name(resource),
        "gender": (resource.get("gender") or "").title(),
        "birth_date": resource.get("birthDate") or "",
        "age": age(resource.get("birthDate")),
        "phone": contact(resource, "phone"),
        "email": contact(resource, "email"),
        "active": resource.get("active", True),
    }


class PatientsService:
    async def search(self, token: str | None, filters: dict[str, str] | None = None,
                     count: int = 50) -> SearchResult:
        params = {k: v for k, v in (filters or {}).items() if k in SEARCHABLE and v}
        result = await FhirClient(auth_token=token).search(
            "Patient", LIST_FIELDS, params, count=count
        )
        return SearchResult(
            items=[to_row(r) for r in result.items],
            certain=result.certain,
            capped=result.capped,
        )

    async def get(self, token: str | None, patient_id: str) -> dict[str, Any] | None:
        resource = await FhirClient(auth_token=token).read("Patient", patient_id, DETAIL_FIELDS)
        if not resource:
            return None
        row = to_row(resource)
        row["address"] = resource.get("address") or []
        row["general_practitioner"] = (resource.get("generalPractitioner") or [{}])[0].get("display", "")
        return row


patients_service = PatientsService()


def demo() -> None:
    resource = {
        "id": "p1", "gender": "female", "birthDate": "1990-06-02", "active": True,
        "name": [{"family": "Okafor", "given": ["Ada", "N"]}],
        "telecom": [{"system": "email", "value": "a@b.c"}, {"system": "phone", "value": "+44 1"}],
    }
    row = to_row(resource)
    assert row["name"] == "Ada N Okafor"
    assert row["phone"] == "+44 1" and row["email"] == "a@b.c"
    assert row["gender"] == "Female"
    assert row["age"] == age("1990-06-02") and row["age"] is not None

    assert full_name({}) == "(no name)"
    assert full_name({"name": [{"family": "Solo"}]}) == "Solo"
    assert contact({}, "phone") == ""
    # a partial date must not crash the whole list
    assert age("not-a-date") is None and age(None) is None
    assert age("2000") is None

    svc = PatientsService()
    filtered = {k: v for k, v in {"name": "ada", "_sort": "name", "": "x"}.items()
                if k in SEARCHABLE and v}
    assert filtered == {"name": "ada"}, "unsupported params must be dropped, not sent"
    assert "_lastUpdated" not in SEARCHABLE and "_sort" not in SEARCHABLE
    print("patients_service self-check ok")


if __name__ == "__main__":
    demo()
