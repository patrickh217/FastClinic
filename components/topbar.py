"""Top bar: brand, environment, language, current user.

Class names match the salvaged stylesheet: .topbar > .brand + .actions, with
.env-pill and .app-lang-select inside.
"""

from __future__ import annotations

from pathlib import Path

from fasthtml.common import A, Div, Form, Option, Select, Span

from auth.auth_utils import AuthContext
from i18n import LANGUAGES


def _version() -> str:
    """VERSION holds "<semver> <date>" on one line — only the number belongs in the UI."""
    path = Path(__file__).resolve().parent.parent / "VERSION"
    try:
        return path.read_text(encoding="utf-8").strip().split()[0]
    except (OSError, IndexError):
        return "dev"


def _language_selector(lang: str):
    return Form(
        Select(
            *[Option(code.upper(), value=code, selected=(code == lang)) for code in LANGUAGES],
            name="code",
            cls="app-lang-select",
            onchange="this.form.action='/set-lang/'+this.value; this.form.submit();",
        ),
        method="post",
        action="/set-lang/en",
    )


def topbar(environment: str, ctx: AuthContext | None, lang: str = "en"):
    actions = [_language_selector(lang)]
    if ctx:
        actions.append(Span(ctx.email))
        actions.append(A("Sign out", href="/logout"))
    else:
        actions.append(A("Sign in", href="/login"))

    return Div(
        Div(
            Span(cls="brand-dot"),
            Span("FastClinic"),
            Span(f"v{_version()}", cls="env-pill"),
            cls="brand",
        ),
        Div(
            # A production session must never be mistakable for a sandbox one.
            *([Span(environment.upper(), cls="env-pill")] if environment != "production" else []),
            *actions,
            cls="actions",
        ),
        cls="topbar",
    )
