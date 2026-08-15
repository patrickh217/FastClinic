"""FastClinic — application entry point.

Middleware order is load-bearing and asserted by tests/integration/test_app.py:

    SecurityHeaders -> Session -> Beforeware(auth_gate) -> route

`before` runs after the session is available and before any handler, which is
exactly where a deny-by-default gate belongs.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fasthtml.common import Beforeware, fast_app, serve

from config import config
from middleware.auth_gate import auth_before
from middleware.security_headers import SecurityHeadersMiddleware
from routes import register_all_routes
from services.medbackend.base_client import close_shared_client


@asynccontextmanager
async def lifespan(app):
    yield
    await close_shared_client()


def create_app():
    settings = config.settings()

    app, rt = fast_app(
        pico=False,          # we ship our own stylesheet; PicoCSS would fight it
        default_hdrs=False,  # page() emits a complete document
        secret_key=settings["session_secret"],
        before=Beforeware(auth_before),
        lifespan=lifespan,
        static_path=".",
    )
    app.add_middleware(
        SecurityHeadersMiddleware,
        https_only=settings["environment"] == "production",
    )
    register_all_routes(rt)
    return app, rt


app, rt = create_app()


if __name__ == "__main__":
    serve(app="app", host="0.0.0.0", port=config.settings()["port"])
