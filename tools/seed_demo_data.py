"""Seed a MedBackend dev project with synthetic clinical data.

Composes two salvaged pieces: tools/synth.py generates structurally realistic
people and billable lines, services/fhir_builders.py turns rows into valid R4.
The adapter between them lives here — it is the part the deleted PMS importer
used to do, reduced to the fields the FHIR builders actually read.

Idempotent by search-before-create on a stable identifier. backbone does no
server-side dedup, so a retry without that check duplicates every record — the
exact bug that bit VaxMe's Immunization save path.

    python -m tools.seed_demo_data --dry-run          # build and validate, no writes
    python -m tools.seed_demo_data --patients 25      # write to the dev project

Credentials come from the environment: MEDBACKEND_SEED_EMAIL / _PASSWORD, plus
the usual MEDBACKEND_* settings. All data is synthetic; there is no real PHI.
"""

from __future__ import annotations

import argparse
import asyncio
import os
from datetime import date, datetime, timedelta

from auth import oauth_config, oauth_service
from services import fhir_builders as fb
from services.medbackend.base_client import close_shared_client
from services.medbackend.fhir_client import BackboneError, FhirClient
from tools import synth

# Excel stores dates as days since 1899-12-30. synth emits serials because it was
# written to produce an .xlsx export; the FHIR builders want ISO strings.
_EXCEL_EPOCH = date(1899, 12, 30)


def iso_from_serial(serial) -> str | None:
    if serial in (None, "", 0):
        return None
    try:
        return (_EXCEL_EPOCH + timedelta(days=float(serial))).isoformat()
    except (TypeError, ValueError, OverflowError):
        return None


def iso_dt_from_serial(serial) -> str | None:
    if serial in (None, "", 0):
        return None
    try:
        moment = datetime(1899, 12, 30) + timedelta(days=float(serial))
        return moment.isoformat(timespec="seconds")
    except (TypeError, ValueError, OverflowError):
        return None


def subject_row(patient: dict, client: dict | None) -> dict:
    """synth's `patient` sheet -> the row shape patient_resource() reads."""
    row = dict(patient)
    row["date_of_birth"] = iso_from_serial(patient.get("date_of_birth"))
    row["deceased_at"] = iso_dt_from_serial(patient.get("deceased"))
    if client:
        row["phone"] = client.get("phone")
        row["email"] = client.get("email")
    return row


def derive_consultations(items: list[dict]) -> list[dict]:
    """One Encounter per consultation_id.

    The deleted importer derived this table by grouping billable lines; the
    grouping is the only part worth keeping, so it is reproduced here rather
    than resurrecting the importer.
    """
    grouped: dict[int, dict] = {}
    for item in items:
        cid = item.get("consultation_id")
        if cid is None:
            continue
        row = grouped.setdefault(cid, {
            "id": cid,
            "subject_id": item.get("patient_id"),
            "consult_at": iso_dt_from_serial(item.get("used") or item.get("created")),
            "clinician_id": item.get("supervising_clinician_id"),
            "is_visit": 1,
        })
        if not row["consult_at"]:
            row["consult_at"] = iso_dt_from_serial(item.get("created"))
    return list(grouped.values())


def diagnosis_row(diagnosis: dict) -> dict:
    row = dict(diagnosis)
    row["subject_id"] = diagnosis.get("patient_id")
    row["diagnosed_at"] = iso_dt_from_serial(diagnosis.get("date"))
    row["recorded_date"] = iso_from_serial(diagnosis.get("date"))
    return row


def build_resources(n_patients: int, seed: int = 42) -> dict[str, list[dict]]:
    data = synth.generate(n_patients, seed=seed)
    clients = {c["id"]: c for c in data["client"]}

    patients = [
        fb.patient_resource(subject_row(p, clients.get(p.get("client_id"))))
        for p in data["patient"]
    ]
    practitioners = [
        fb.practitioner_resource(cid) for cid in sorted(set(synth.CLINICIANS))
    ]
    encounters = [
        fb.encounter_resource(c) for c in derive_consultations(data["Consultationitem"])
    ]
    conditions = [
        fb.condition_resource(diagnosis_row(d)) for d in data["Consultationdiagnosis"]
    ]
    return {
        "Organization": [fb.clinic_organization()],
        "Practitioner": practitioners,
        "Patient": patients,
        "Encounter": encounters,
        "Condition": conditions,
    }


def stable_identifier(resource: dict) -> str | None:
    """The value we search on before creating. No identifier means no dedup."""
    for ident in resource.get("identifier") or []:
        if ident.get("system", "").startswith(fb.CORE_SID) and ident.get("value"):
            return f"{ident['system']}|{ident['value']}"
    return None


async def upsert(client: FhirClient, resource_type: str, resource: dict) -> str:
    """Search first, then create. Never blind-create — retries would duplicate."""
    token = stable_identifier(resource)
    if token:
        existing = await client.search(resource_type, "id", {"identifier": token}, count=1)
        if len(existing):
            return "skipped"
    created = await client.create(resource_type, resource)
    return "created" if created.get("id") else "failed"


async def seed(n_patients: int, dry_run: bool, seed_value: int = 42) -> int:
    resources = build_resources(n_patients, seed_value)
    total = sum(len(v) for v in resources.values())

    if dry_run:
        for resource_type, items in resources.items():
            missing = [r for r in items if not stable_identifier(r)]
            print(f"{resource_type:<14} {len(items):>5}"
                  f"{'  !! ' + str(len(missing)) + ' without a stable identifier' if missing else ''}")
        print(f"\n{total} resources built, nothing written (--dry-run).")
        return 0

    client = FhirClient(auth_token=await _token())
    tally: dict[str, int] = {}
    # Order matters: references must resolve, so Organization and Practitioner
    # exist before the Patients and Encounters that point at them.
    for resource_type, items in resources.items():
        for resource in items:
            try:
                outcome = await upsert(client, resource_type, resource)
            except BackboneError as exc:
                outcome = "denied" if exc.denied else "error"
                print(f"  {resource_type}: {exc}")
            tally[f"{resource_type}:{outcome}"] = tally.get(f"{resource_type}:{outcome}", 0) + 1

    for key in sorted(tally):
        print(f"{key:<28} {tally[key]}")
    return 0 if not any(k.endswith((":failed", ":error")) for k in tally) else 1


async def _token() -> str:
    email = os.environ.get("MEDBACKEND_SEED_EMAIL", "")
    password = os.environ.get("MEDBACKEND_SEED_PASSWORD", "")
    if not email or not password:
        raise SystemExit(
            "Set MEDBACKEND_SEED_EMAIL and MEDBACKEND_SEED_PASSWORD, or use --dry-run."
        )
    cfg = oauth_config.flow(oauth_config.PRACTITIONER)
    state = oauth_service.new_state()
    code = await oauth_service.login_headless(cfg, email, password, state)
    tokens = await oauth_service.exchange_code(cfg, code)
    return tokens.access_token


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--patients", type=int, default=25)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    async def run() -> int:
        try:
            return await seed(args.patients, args.dry_run, args.seed)
        finally:
            await close_shared_client()

    return asyncio.run(run())


def demo() -> None:
    """Self-check: the adapter and the dedup key, without touching the network."""
    # Round-trip against synth's own serialiser rather than a hand-computed date:
    # this proves the adapter is the exact inverse of what generated the data.
    for original in (date(1980, 12, 29), date(2026, 6, 10), date(1900, 1, 1)):
        assert iso_from_serial(synth._serial(original)) == original.isoformat()

    assert iso_from_serial(None) is None and iso_from_serial(0) is None
    assert iso_from_serial("not-a-number") is None, "a bad serial must not crash a whole run"

    moment = datetime(2022, 4, 7, 15, 18)
    assert (iso_dt_from_serial(synth._serial_dt(moment)) or "").startswith("2022-04-07")

    items = [
        {"consultation_id": 7, "patient_id": 1001, "used": 44658.6375,
         "supervising_clinician_id": 101},
        {"consultation_id": 7, "patient_id": 1001, "used": 44658.7,
         "supervising_clinician_id": 101},
        {"consultation_id": 8, "patient_id": 1002, "used": 44659.5,
         "supervising_clinician_id": 102},
        {"consultation_id": None, "patient_id": 1002},
    ]
    consultations = derive_consultations(items)
    assert len(consultations) == 2, "lines must collapse to one encounter per consultation"
    assert {c["id"] for c in consultations} == {7, 8}

    built = build_resources(3, seed=1)
    assert len(built["Patient"]) == 3
    assert built["Patient"][0]["resourceType"] == "Patient"
    assert built["Patient"][0].get("birthDate"), "birthDate must survive the serial conversion"
    assert built["Organization"] and built["Practitioner"]

    # Every resource we write must carry a dedup key, or a retry duplicates it.
    for resource_type, resources in built.items():
        for resource in resources:
            assert stable_identifier(resource), f"{resource_type} has no stable identifier"

    key = stable_identifier(built["Patient"][0])
    assert key and key.count("|") == 1 and key.startswith(fb.CORE_SID)
    print("seed_demo_data self-check ok")


if __name__ == "__main__":
    if os.environ.get("SELF_CHECK"):
        demo()
    else:
        raise SystemExit(main())
