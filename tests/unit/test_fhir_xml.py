"""FHIR XML serialisation.

Kept from the pre-restructure suite because the exporter survived: it now
serialises what backbone returns rather than locally-assembled rows. Element
order is pinned by the FHIR spec, so a reordering bug is a spec violation that
downstream validators will reject.
"""

from __future__ import annotations

from xml.etree import ElementTree as ET

import pytest

from services.fhir_xml import FHIR_NS, bundle_to_xml

BUNDLE = {
    "resourceType": "Bundle",
    "id": "b1",
    "type": "document",
    "entry": [
        {
            "resource": {
                "resourceType": "Patient",
                "id": "p1",
                "active": True,
                "name": [{"family": "Okafor", "given": ["Ada"]}],
                "gender": "female",
                "birthDate": "1990-06-02",
            }
        }
    ],
}


@pytest.mark.unit
def test_bundle_serialises_to_the_fhir_namespace():
    """GIVEN a Bundle WHEN serialised THEN the root is a namespaced Bundle."""
    root = ET.fromstring(bundle_to_xml(BUNDLE))
    assert root.tag == f"{{{FHIR_NS}}}Bundle"


def _text() -> str:
    # bundle_to_xml returns bytes: it is served as an application/fhir+xml body,
    # and encoding it once at the source avoids a round-trip through str.
    return bundle_to_xml(BUNDLE).decode("utf-8")


@pytest.mark.unit
def test_primitives_are_value_attributes_not_text():
    """GIVEN a FHIR primitive THEN it serialises as value="…", per the spec —
    element text would be silently wrong and still parse."""
    xml = _text()
    assert 'value="female"' in xml
    assert 'value="1990-06-02"' in xml
    assert ">female<" not in xml


@pytest.mark.unit
def test_booleans_serialise_lowercase():
    """GIVEN a boolean THEN it is 'true', not Python's 'True'."""
    xml = _text()
    assert 'value="true"' in xml
    assert 'value="True"' not in xml


@pytest.mark.unit
def test_patient_with_a_name_serialises():
    """GIVEN a patient with name, telecom and address WHEN serialised THEN it
    succeeds. Before 2026-08-15 the ordering table had no entry for any of the
    three, so the fail-closed serializer rejected every named patient."""
    bundle = {
        "resourceType": "Bundle", "id": "b2", "type": "document",
        "entry": [{"resource": {
            "resourceType": "Patient", "id": "p2",
            "name": [{"family": "Okafor", "given": ["Ada"]}],
            "telecom": [{"system": "phone", "value": "+44 20 7000 0000"}],
            "address": [{"city": "London", "country": "GB"}],
        }}],
    }
    xml = bundle_to_xml(bundle).decode("utf-8")
    assert 'value="Okafor"' in xml and 'value="London"' in xml


@pytest.mark.unit
def test_round_trips_through_a_parser():
    """GIVEN the output WHEN parsed THEN it is well-formed and carries the patient."""
    root = ET.fromstring(bundle_to_xml(BUNDLE))
    families = [e.get("value") for e in root.iter(f"{{{FHIR_NS}}}family")]
    assert families == ["Okafor"]
