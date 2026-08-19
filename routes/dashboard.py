"""Overview.

Deliberately thin. backbone reports no totals and offers no aggregation, so the
revenue, specialty-mix and procedure KPIs this page used to carry cannot be
rebuilt honestly against it. What remains is a set of capped, explicitly labelled
counts plus links into the views that do work.
"""

from __future__ import annotations

from fasthtml.common import Div

from components.common.lazy import lazy_content
from components.layout import page, page_title
from config import config


def register_dashboard_routes(rt) -> None:

    @rt("/")
    def get(request, session):
        ctx = request.scope["auth"]
        if ctx.is_patient:
            from fasthtml.common import RedirectResponse
            return RedirectResponse("/portal", status_code=303)

        return page(
            "dashboard",
            Div(
                page_title(
                    "Overview",
                    "MedBackend reports no record totals, so the figures below count "
                    "only what was fetched. They are not clinic-wide totals.",
                ),
                lazy_content("/overview/summary", section_id="overview-summary", rows=3),
                cls="page",
            ),
            ctx=ctx,
            environment=config.settings()["environment"],
            title="Overview — FastClinic",
        )

    @rt("/overview/summary")
    async def get(request, session):
        from handlers.overview_handlers import overview_handlers
        return await overview_handlers.summary(
            request.scope["auth"], session.get("access_token")
        )
