"""Sign-in against medbackend-oauth.

The login form itself is hosted and branded by medbackend-oauth — we only send the
user there and handle the callback. Two flows exist, Practitioner for staff and
Patient for the portal, and they are separate OAuth clients.
"""

from __future__ import annotations

from fasthtml.common import A, Div, H1, P, RedirectResponse

from auth import oauth_config, oauth_service
from auth.auth_utils import build_context
from components.layout import page
from config import config
from handlers.auth_handlers import auth_handlers
from middleware.auth_gate import clear_session


def register_auth_routes(rt) -> None:

    @rt("/login")
    def get(session, entity: str = ""):
        if entity in (oauth_config.PRACTITIONER, oauth_config.PATIENT):
            cfg = oauth_config.flow(entity)
            state = oauth_service.new_state()
            session["oauth_state"] = state
            session["entity_type"] = entity
            return RedirectResponse(
                oauth_service.authorization_url(cfg, state), status_code=303
            )

        return page(
            "login",
            Div(
                H1("Sign in to FastClinic"),
                P("Authentication is handled by MedBackend."),
                A("Staff sign-in", href="/login?entity=Practitioner", cls="btn primary"),
                A("Patient sign-in", href="/login?entity=Patient", cls="btn"),
                cls="card login-card",
            ),
            environment=config.settings()["environment"],
            title="Sign in — FastClinic",
        )

    @rt("/auth/callback")
    async def get(session, code: str = "", state: str = "", error: str = ""):
        if error:
            return _failure(f"MedBackend refused the sign-in: {error}")
        # Single-use, and the code dies after 10 minutes upstream.
        if not code or not state or state != session.pop("oauth_state", None):
            return _failure("The sign-in link was invalid or has already been used.")

        entity = session.get("entity_type", oauth_config.PRACTITIONER)
        cfg = oauth_config.flow(entity)
        try:
            tokens = await oauth_service.exchange_code(cfg, code)
        except oauth_service.OAuthError as exc:
            return _failure(str(exc))

        session["access_token"] = tokens.access_token
        session["refresh_token"] = tokens.refresh_token
        session["expires_at"] = tokens.expires_at

        # The JWT carries no roles, so identity beyond the claims comes from FHIR.
        context = build_context(tokens.access_token)
        identity = await auth_handlers.resolve_identity(
            tokens.access_token, context.entity_id, context.is_patient
        )
        session["reference"] = identity["reference"]
        session["practitioner_roles"] = identity["practitioner_roles"]

        return RedirectResponse("/portal" if context.is_patient else "/", status_code=303)

    @rt("/logout")
    def get(session):
        clear_session(session)
        session.pop("practitioner_roles", None)
        session.pop("reference", None)
        return RedirectResponse("/login", status_code=303)


def _failure(message: str):
    return page(
        "login",
        Div(
            H1("Sign-in failed"),
            P(message, cls="empty-hint"),
            A("Try again", href="/login", cls="btn primary"),
            cls="card login-card",
        ),
        environment=config.settings()["environment"],
        title="Sign-in failed — FastClinic",
    )
