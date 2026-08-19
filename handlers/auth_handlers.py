"""Auth-callback orchestration, so routes/auth.py never reaches into services."""

from __future__ import annotations

from services.identity_service import identity_service


class AuthHandlers:
    async def resolve_identity(self, token: str, entity_id: str, is_patient: bool) -> dict:
        return await identity_service.resolve(token, entity_id, is_patient)


auth_handlers = AuthHandlers()
