"""Route registration.

Imports are function-local to avoid circular imports between routes, components
and handlers. Order matters where a package registers both mutating and page
routes: forms must register before pages, or POST /x and GET /x collide.
"""

from __future__ import annotations

from fasthtml.common import RedirectResponse

from config import config


def register_all_routes(rt) -> None:
    from routes.auth import register_auth_routes
    from routes.dashboard import register_dashboard_routes
    from routes.patients import register_patient_routes

    register_auth_routes(rt)
    register_dashboard_routes(rt)
    register_patient_routes(rt)

    @rt("/health")
    def get():
        """Liveness. Always 200 while the process is up."""
        return {"status": "ok"}

    @rt("/health/ready")
    def get():
        """Readiness. Names missing settings; never reports their values."""
        ok, problems = config.readiness()
        if ok:
            return {"status": "ready"}
        from starlette.responses import JSONResponse
        return JSONResponse(
            {"status": "not-ready", "missing": problems}, status_code=503
        )

    @rt("/set-lang/{code}")
    def post(code: str, session, request):
        from i18n import safe_return_path, set_lang
        set_lang(session, code)
        return RedirectResponse(
            safe_return_path(request.headers.get("referer")), status_code=303
        )
