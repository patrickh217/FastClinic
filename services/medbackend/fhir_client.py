"""The only module that talks to backbone, and the only one that knows its quirks.

Every trap documented in the vault's backbone gotchas is handled here exactly once:

- `search_resources` server-side swallows every exception and returns `[]`, so an
  empty list is indistinguishable from a failure. We surface that as `certain=False`
  rather than letting a view render "none".
- Every error arrives HTTP 200 with the prefix "Authentication failed:", RBAC
  denials included. "Access denied" inside the message is the only 403 signal.
- `ConnectionType.count` is a post-RBAC page length, not a total. There is no total.
- `XList(count:, offset:)` is lowercase; `XConnection(Count:, Offset:)` is not.
- Reads take `String!`, mutations take `ID!`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from config import config
from services.medbackend.base_client import BaseApiClient, shared_client

# backbone caps a page here; deeper pagination is not implemented upstream
# (XList sends _skip, XConnection sends _offset, neither is a FHIR param, and
# Azure's continuation token is not handled anywhere).
MAX_PAGE = 1000


class BackboneError(RuntimeError):
    """A backbone failure we could classify."""

    def __init__(self, message: str, *, denied: bool = False, unauthenticated: bool = False):
        super().__init__(message)
        self.denied = denied
        self.unauthenticated = unauthenticated


@dataclass(slots=True)
class SearchResult:
    """A list of resources plus whether we actually know it is complete.

    `certain=False` means the query may have failed silently. Views must render
    that as an indeterminate state — never as "no results". In a clinical view,
    showing "no allergies" for a failed query is the dangerous version of this bug.
    """

    items: list[dict[str, Any]] = field(default_factory=list)
    certain: bool = True
    capped: bool = False

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self):
        return iter(self.items)


def classify(message: str) -> BackboneError:
    """backbone gives no error code, so the message text is all we have."""
    lowered = message.lower()
    if "access denied" in lowered or "forbidden" in lowered:
        return BackboneError(message, denied=True)
    if "no valid token" in lowered or "token validation failed" in lowered:
        return BackboneError(message, unauthenticated=True)
    return BackboneError(message)


class FhirClient(BaseApiClient):
    def __init__(self, auth_token: str | None = None, project_id: str | None = None) -> None:
        settings = config.settings()
        super().__init__(settings["graphql_url"])
        self.set_auth_token(auth_token)
        self.set_project_id(project_id or settings["project_id"])

    async def execute(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        response = await shared_client().post(
            self.base_url,
            headers=self.headers(),
            json={"query": query, "variables": variables or {}},
        )
        # Pre-GraphQL middleware failures are real HTTP with a machine-readable code.
        if response.status_code != 200:
            body = _safe_json(response)
            code = body.get("code", response.status_code)
            raise BackboneError(f"{code}: {body.get('message', response.text[:200])}")

        payload = response.json()
        if payload.get("errors"):
            raise classify(payload["errors"][0].get("message", "unknown backbone error"))
        return payload.get("data") or {}

    async def me(self) -> str | None:
        """`Practitioner/abc-123`. Compartment queries cannot be built without it."""
        data = await self.execute("query { Me { reference } }")
        return (data.get("Me") or {}).get("reference")

    async def read(self, resource_type: str, resource_id: str, fields: str) -> dict[str, Any] | None:
        # Reads take String!, unlike mutations which take ID!.
        query = f"query Read($id: String!) {{ {resource_type}(id: $id) {{ {fields} }} }}"
        data = await self.execute(query, {"id": resource_id})
        # A row-level RBAC denial also arrives as null, with no error. Indistinguishable.
        return data.get(resource_type)

    async def search(
        self,
        resource_type: str,
        fields: str,
        params: dict[str, str] | None = None,
        count: int = 50,
    ) -> SearchResult:
        """Search one page. There is no total and no sort — do not offer either."""
        count = min(count, MAX_PAGE)
        params = params or {}
        arg_defs = ", ".join(f"${k}: String" for k in params)
        arg_use = ", ".join(f"{k}: ${k}" for k in params)
        signature = f"({arg_defs})" if arg_defs else ""
        call = ", ".join(filter(None, [arg_use, f"count: {count}"]))
        query = (
            f"query Search{signature} {{ {resource_type}List({call}) {{ {fields} }} }}"
        )
        try:
            data = await self.execute(query, dict(params))
        except BackboneError:
            raise
        items = data.get(f"{resource_type}List") or []
        # Upstream returns [] on failure as well as on genuine emptiness. We cannot
        # tell them apart, so an empty page is reported as uncertain.
        return SearchResult(items=items, certain=bool(items), capped=len(items) >= count)

    async def validate(self, resource_type: str, resource: dict[str, Any]) -> list[dict[str, Any]]:
        """Free dry run — no write. Call before every create."""
        query = (
            f"mutation Validate($resource: {resource_type}CreateInput!) "
            f"{{ {resource_type}Validate(resource: $resource) "
            f"{{ valid errors {{ field message severity }} }} }}"
        )
        data = await self.execute(query, {"resource": resource})
        result = data.get(f"{resource_type}Validate") or {}
        return [] if result.get("valid") else (result.get("errors") or [])

    async def create(self, resource_type: str, resource: dict[str, Any], fields: str = "id") -> dict[str, Any]:
        query = (
            f"mutation Create($resource: {resource_type}CreateInput!) "
            f"{{ {resource_type}Create(resource: $resource) {{ {fields} }} }}"
        )
        data = await self.execute(query, {"resource": resource})
        return data.get(f"{resource_type}Create") or {}

    async def update(self, resource_type: str, resource_id: str, resource: dict[str, Any], fields: str = "id") -> dict[str, Any]:
        # Full PUT replace — no PATCH, no If-Match, no version check. Callers must
        # re-read immediately before building `resource`, or risk a lost update.
        query = (
            f"mutation Update($id: ID!, $resource: {resource_type}UpdateInput!) "
            f"{{ {resource_type}Update(id: $id, resource: $resource) {{ {fields} }} }}"
        )
        data = await self.execute(query, {"id": resource_id, "resource": resource})
        return data.get(f"{resource_type}Update") or {}


def _safe_json(response) -> dict[str, Any]:
    try:
        return response.json()
    except ValueError:
        return {}


def demo() -> None:
    """Self-check for the two classification rules that carry real risk."""
    denied = classify("Authentication failed: Access denied: Practitioner cannot create Invoice.")
    assert denied.denied and not denied.unauthenticated

    expired = classify("Authentication failed: No valid token found")
    assert expired.unauthenticated and not expired.denied

    other = classify("Authentication failed: something else entirely")
    assert not other.denied and not other.unauthenticated

    empty = SearchResult(items=[], certain=False)
    assert not empty.certain, "an empty page must never be reported as certain"
    assert len(empty) == 0

    full = SearchResult(items=[{"id": "1"}], certain=True, capped=False)
    assert full.certain and len(full) == 1
    print("fhir_client self-check ok")


if __name__ == "__main__":
    demo()
