"""Page shell.

The stylesheet lays `.app` out as a named-area grid — "top top top" / "left center
right" — so .topbar, .left-pane and .center-pane must be DIRECT children of .app.
Nesting them inside a wrapper silently collapses the topbar into the 240px nav
column, which is exactly what the first screenshot caught.

The right rail is deferred: the copilot depended on the deleted slash-command
dispatcher and DB-backed tools. `.app.right-collapsed` zeroes that column, so the
two-pane layout needs no CSS change.
"""

from __future__ import annotations

from fasthtml.common import Body, Div, H1, Head, Html, Link, Meta, P, Title

from auth.auth_utils import AuthContext
from components.sidebar import sidebar
from components.theme import theme_styles
from components.topbar import topbar


def head(title: str) -> Head:
    # fast_app already bundles htmx — a second <script src=htmx> here would load
    # it twice and break event handling.
    return Head(
        Title(title),
        Meta(charset="utf-8"),
        Meta(name="viewport", content="width=device-width, initial-scale=1"),
        Link(rel="icon", href="/static/images/favicon.svg", type="image/svg+xml"),
        theme_styles(),
    )


def page(active: str, *content, ctx: AuthContext | None = None,
         environment: str = "development", lang: str = "en",
         title: str = "FastClinic"):
    return Html(
        head(title),
        Body(
            Div(
                topbar(environment, ctx, lang),
                sidebar(active, ctx, lang),
                Div(*content, cls="center-pane", id="main-content"),
                cls="app right-collapsed" + ("" if ctx else " no-nav"),
            ),
            Div(id="notification-area"),
            Div(id="modal-container"),
        ),
        lang=lang,
    )


def page_title(title: str, subtitle: str = "", actions=None):
    return Div(
        Div(H1(title), P(subtitle, cls="sub") if subtitle else None),
        actions,
        cls="page-title",
    )


def kpi_card(label: str, value, trend: str = "", warn: bool = False, neutral: bool = False):
    classes = "kpi" + (" warn" if warn else "") + (" neutral" if neutral else "")
    return Div(
        Div(label, cls="label"),
        Div(str(value), cls="value"),
        Div(trend, cls="trend") if trend else None,
        cls=classes,
    )


def kpi_grid(*cards):
    return Div(*cards, cls="kpi-grid")
