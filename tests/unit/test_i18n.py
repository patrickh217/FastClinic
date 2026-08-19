"""i18n behaviour, focused on the parts that can go wrong silently or unsafely."""

from __future__ import annotations

import pytest

from i18n import LANGUAGES, catalog, get_lang, safe_return_path, set_lang, t


@pytest.mark.unit
@pytest.mark.parametrize("hostile", [
    "https://evil.example/steal",
    "//evil.example/steal",
    "http://evil.example",
    "/\\evil.example",
    "/path\nInjected: header",
    "javascript:alert(1)",
])
def test_safe_return_path_rejects_open_redirects(hostile):
    """GIVEN a hostile referer WHEN a language switch returns THEN it lands on /.

    The language selector reflects the referer back as a redirect target, so this
    is the app's open-redirect boundary.
    """
    assert safe_return_path(hostile) == "/"


@pytest.mark.unit
def test_safe_return_path_keeps_local_paths_and_query():
    """GIVEN a local path WHEN it returns THEN the path and query survive intact."""
    assert safe_return_path("/patients?name=ada") == "/patients?name=ada"
    assert safe_return_path("/") == "/"
    assert safe_return_path(None) == "/"


@pytest.mark.unit
def test_set_lang_rejects_unknown_codes():
    """GIVEN an unknown language WHEN set THEN it falls back rather than storing junk."""
    session: dict = {}
    set_lang(session, "kl")
    assert get_lang(session) in LANGUAGES


@pytest.mark.unit
def test_translation_falls_back_to_source_text():
    """GIVEN a string with no catalogue entry THEN the source text is returned,
    so a missing translation degrades to English instead of an empty label."""
    assert t("Patients", "en") == "Patients"
    assert t("a string nobody has translated", "de") == "a string nobody has translated"


@pytest.mark.unit
@pytest.mark.parametrize("code", sorted(LANGUAGES))
def test_every_declared_language_has_a_loadable_catalogue(code):
    """GIVEN a language offered in the selector THEN its catalogue actually loads."""
    assert isinstance(catalog(code), dict)
