"""Encounters, conditions and observations for a patient.

No ordering is possible — backbone generates no _sort argument — so results come
back in whatever order the server produced. Views must not imply chronology they
cannot guarantee; sort client-side when order matters to the reader.
"""

from __future__ import annotations

from typing import Any

from services.medbackend.fhir_client import FhirClient, SearchResult

ENCOUNTER_FIELDS = """
id status
period { start end }
type { coding { display } text }
serviceType { coding { display } }
"""

CONDITION_FIELDS = """
id recordedDate
code { coding { display } text }
clinicalStatus { coding { code } }
"""


def _display(concept: dict[str, Any] | None) -> str:
    if not concept:
        return ""
    if concept.get("text"):
        return concept["text"]
    for coding in concept.get("coding") or []:
        if coding.get("display"):
            return coding["display"]
    return ""


def encounter_row(resource: dict[str, Any]) -> dict[str, Any]:
    period = resource.get("period") or {}
    types = resource.get("type") or []
    return {
        "id": resource.get("id", ""),
        "date": (period.get("start") or "")[:10],
        "status": resource.get("status", ""),
        "type": _display(types[0] if types else None)
                or _display((resource.get("serviceType") or [{}])[0]),
    }


class ClinicalService:
    async def encounters_for(self, token: str | None, patient_id: str,
                             count: int = 50) -> SearchResult:
        result = await FhirClient(auth_token=token).search(
            "Encounter", ENCOUNTER_FIELDS, {"patient": patient_id}, count=count
        )
        rows = [encounter_row(r) for r in result.items]
        # Descending by date, done here because the server cannot do it.
        rows.sort(key=lambda r: r["date"], reverse=True)
        return SearchResult(items=rows, certain=result.certain, capped=result.capped)

    async def conditions_for(self, token: str | None, patient_id: str,
                             count: int = 50) -> SearchResult:
        result = await FhirClient(auth_token=token).search(
            "Condition", CONDITION_FIELDS, {"patient": patient_id}, count=count
        )
        return SearchResult(
            items=[{
                "id": r.get("id", ""),
                "recorded": (r.get("recordedDate") or "")[:10],
                "label": _display(r.get("code")),
                "status": _display(r.get("clinicalStatus")) or (
                    (r.get("clinicalStatus") or {}).get("coding") or [{}]
                )[0].get("code", ""),
            } for r in result.items],
            certain=result.certain,
            capped=result.capped,
        )


clinical_service = ClinicalService()


def demo() -> None:
    row = encounter_row({
        "id": "e1", "status": "finished",
        "period": {"start": "2026-03-04T09:00:00Z"},
        "type": [{"coding": [{"display": "Orthopaedic consultation"}]}],
    })
    assert row["date"] == "2026-03-04", row["date"]
    assert row["type"] == "Orthopaedic consultation"

    # text wins over coding.display, per FHIR
    assert _display({"text": "Free text", "coding": [{"display": "Coded"}]}) == "Free text"
    assert _display(None) == "" and _display({}) == ""

    # falls back to serviceType when type is absent, and to status when neither exists
    fallback = encounter_row({"id": "e2", "status": "planned",
                              "serviceType": [{"coding": [{"display": "Dental"}]}]})
    assert fallback["type"] == "Dental"
    bare = encounter_row({"id": "e3", "status": "planned"})
    assert bare["type"] == "" and bare["status"] == "planned" and bare["date"] == ""
    print("clinical_service self-check ok")


if __name__ == "__main__":
    demo()
