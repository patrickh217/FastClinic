"""Live end-to-end against a MedBackend dev project.

Opt-in: these are the only tests that touch the network. Run with

    MEDBACKEND_LIVE_TEST=1 pytest tests/e2e

plus MEDBACKEND_SEED_EMAIL / _PASSWORD and the usual MEDBACKEND_* settings.

They exist to catch the things no stub can: that the headless login path still
returns JSON rather than a 302, that the token is accepted, and that the
assumptions this client is built on still hold upstream.
"""

from __future__ import annotations

import os

import pytest

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        os.environ.get("MEDBACKEND_LIVE_TEST") != "1",
        reason="live suite; set MEDBACKEND_LIVE_TEST=1",
    ),
]


@pytest.fixture(scope="module")
async def token():
    """GIVEN dev credentials WHEN logging in headlessly THEN a bearer token comes back.

    This is the whole reason the fixture is shared: the authorization code is
    single-use and dies in 10 minutes, so one login serves the module.
    """
    from auth import oauth_config, oauth_service

    email = os.environ.get("MEDBACKEND_SEED_EMAIL")
    password = os.environ.get("MEDBACKEND_SEED_PASSWORD")
    if not email or not password:
        pytest.skip("MEDBACKEND_SEED_EMAIL / _PASSWORD not set")

    cfg = oauth_config.flow(oauth_config.PRACTITIONER)
    state = oauth_service.new_state()
    code = await oauth_service.login_headless(cfg, email, password, state)
    tokens = await oauth_service.exchange_code(cfg, code)
    assert tokens.access_token and tokens.refresh_token
    assert not tokens.expired(), "a freshly issued token must not read as expired"
    yield tokens.access_token

    from services.medbackend.base_client import close_shared_client
    await close_shared_client()


async def test_me_returns_a_reference(token):
    """GIVEN a practitioner token WHEN Me is queried THEN it returns Practitioner/<id>.

    Compartment-scoped queries cannot be built without this, so it is the first
    thing to break if the token shape changes.
    """
    from services.medbackend.fhir_client import FhirClient

    reference = await FhirClient(auth_token=token).me()
    assert reference and "/" in reference
    assert reference.split("/")[0] in {"Practitioner", "Patient", "RelatedPerson"}


async def test_patient_search_is_certain_when_data_exists(token):
    """GIVEN a seeded project WHEN patients are searched THEN the result is certain.

    An uncertain result here means the search silently failed upstream — the
    failure mode that renders as "no patients" if it is not caught.
    """
    from services.medbackend.fhir_client import FhirClient

    result = await FhirClient(auth_token=token).search("Patient", "id", count=5)
    if not len(result):
        pytest.skip("project has no patients; run tools.seed_demo_data first")
    assert result.certain


async def test_missing_project_header_is_a_400_not_an_auth_error(token):
    """GIVEN no X-Project-ID WHEN backbone is called THEN it fails before GraphQL.

    Middleware short-circuits with MISSING_PROJECT_UID. Handling this as an auth
    error would send the user to a pointless re-login.
    """
    from services.medbackend.fhir_client import BackboneError, FhirClient

    client = FhirClient(auth_token=token)
    client.set_project_id(None)
    with pytest.raises(BackboneError) as caught:
        await client.execute("query { Me { reference } }")
    assert not caught.value.unauthenticated
    assert "MISSING_PROJECT_UID" in str(caught.value) or "400" in str(caught.value)


async def test_rbac_denial_is_classified_as_denied_not_unauthenticated(token):
    """GIVEN a write with no RBAC rule THEN it is classified as denied.

    Writes default to Forbidden, so this is the expected shape of every write
    until per-project rules exist. If it ever classifies as unauthenticated, the
    app would log the user out instead of explaining the permission gap.
    """
    from services.medbackend.fhir_client import BackboneError, FhirClient

    client = FhirClient(auth_token=token)
    try:
        await client.create("Invoice", {"status": "draft"})
    except BackboneError as exc:
        assert not exc.unauthenticated, f"misclassified as an auth failure: {exc}"
    else:
        pytest.skip("Invoice writes are permitted on this project; nothing to assert")
