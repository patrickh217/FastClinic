"""Left navigation.

Every item declares the capability that reveals it. Capabilities come from the
practitioner's FHIR PractitionerRole codings (auth/auth_utils), so the nav follows
what the person actually is. This is a UX control only — hiding a link is not
authorization. backbone enforces access on every request regardless.
"""

from __future__ import annotations

from fasthtml.common import A, Div, H4, Span

from auth.auth_utils import AuthContext
from i18n import t

# (capability, key, label, icon, href)
NAV_ITEMS: list[tuple[str, list[tuple[str, str, str, str, str]]]] = [
    ("OVERVIEW", [
        ("patients", "dashboard", "Overview", "📊", "/"),
        ("portal", "portal", "My health", "🏠", "/portal"),
    ]),
    ("CLINICAL", [
        ("patients", "patients", "Patients", "🧑‍⚕️", "/patients"),
        ("scheduling", "appointments", "Appointments", "📅", "/appointments"),
        ("clinical", "clinical", "Clinical", "🩺", "/clinical"),
    ]),
    # Not listed yet, deliberately: the SEO suite (routes/seo.py) and Help
    # (routes/help.py) still need wiring to the new page shell, and the shortcuts
    # reference the slash commands of the deleted copilot. A nav link to a 404 is
    # worse than a missing one — they go back the commit they are registered in.
]


def _visible(capability: str, ctx: AuthContext | None) -> bool:
    if capability == "*":
        return True
    if ctx is None:
        return False
    return ctx.can(capability)


def sidebar(active: str, ctx: AuthContext | None = None, lang: str | None = None):
    sections = []
    for title, items in NAV_ITEMS:
        links = [
            A(
                Span(icon, cls="nav-icon"),
                Span(t(label, lang) if lang else label),
                href=href,
                cls=f"nav-item{' active' if key == active else ''}",
            )
            for capability, key, label, icon, href in items
            if _visible(capability, ctx)
        ]
        if links:
            # The stylesheet targets `.nav-section h4` — a bare div gets no styling.
            sections.append(Div(H4(title), *links, cls="nav-section"))
    return Div(*sections, cls="left-pane")


def demo() -> None:
    from auth.auth_utils import AuthContext as AC

    doctor = AC(entity_type="Practitioner", entity_id="Practitioner/1", project_uid="p",
                email="d@c.io", capabilities=frozenset({"patients", "clinical", "scheduling"}))
    rendered = str(sidebar("patients", doctor))
    assert "/patients" in rendered and "/appointments" in rendered
    assert "/portal" not in rendered, "a practitioner must not see the patient portal"

    patient = AC(entity_type="Patient", entity_id="Patient/9", project_uid="p",
                 email="p@c.io", capabilities=frozenset({"portal"}))
    rendered = str(sidebar("portal", patient))
    assert "/portal" in rendered
    assert "/patients" not in rendered, "a patient must not see the staff patient list"
    assert "/clinical" not in rendered

    # an empty section must not render its heading
    assert "CLINICAL" not in rendered
    print("sidebar self-check ok")


if __name__ == "__main__":
    demo()
