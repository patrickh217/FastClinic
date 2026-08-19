# CLAUDE.md

Guidance for Claude Code working in this repository.

## What this is

**FastClinic** — a multi-specialty clinic operations SaaS. A FastHTML + HTMX cockpit for the back office of a clinic spanning general practice, surgical specialties and dental care: patients, appointments, charting, fee invoicing and patient recall.

**FastClinic owns no medical data.** MedBackend is the backend and system of record — FHIR R4 store, multi-tenant RBAC, patient and practitioner OAuth, terminology. This repo holds presentation, clinic workflow, and one MedBackend client package. Nothing else.

Port **5005**. Palette: primary `#1e6fb8`, dark `#1b2733`, accent `#1f9d72`. Tagline *"Modern clinical care, made personal."*

## Git — read before any command

| Remote | URL | Rule |
|---|---|---|
| `origin` | `patrickh217/FastClinic` | our fork. PRs go here. |
| `upstream` | `predictivelabsai/FastClinic` | public. **Never push.** |

The clone shipped with `origin` pointing at the public upstream. Work branches carry no upstream tracking, deliberately, so a bare `git push` has no default destination. `.claude/hooks/block-upstream-push.sh` blocks anything that would reach it anyway.

Always work in a worktree: `git worktree add .claude/worktrees/<task> -b claude/YYYY-MM-DD-<desc> upstream/main`.

## Key entrypoints

| Path | Read it when |
|---|---|
| `app.py` | wiring — middleware order is load-bearing and asserted by a test |
| `routes/__init__.py` | `register_all_routes(rt)`, plus `/`, `/health`, `/health/ready` |
| `services/medbackend/fhir_client.py` | **read first before any data work** — every backbone quirk is handled here and nowhere else |
| `auth/oauth_service.py` | the medbackend-oauth authorization-code flow |
| `config/config.py` | per-environment defaults; secrets by name, never by value |

## How to run

```bash
python -m venv .venv && .venv/bin/python -m pip install -r requirements.txt
infisical run --env=dev -- .venv/bin/python app.py                   # cockpit on :5005
infisical run --env=dev -- .venv/bin/python -m tools.seed_demo_data  # synthetic FHIR into the dev project
.venv/bin/python -m pytest tests/unit tests/integration              # offline, needs no secrets
infisical run --env=dev -- env MEDBACKEND_LIVE_TEST=1 .venv/bin/python -m pytest tests/e2e
```

Anything reading `MEDBACKEND_*` or `FASTCLINIC_SECRET` needs the `infisical run` prefix. The offline suite does not — it stubs the client.

No linter configured. `fasthtml.md` at the repo root is the FastHTML reference.

## Architecture

```
browser → FastHTML (app.py, routes/, components/)
            ├── auth/         medbackend-oauth: authorization_code + refresh
            │                 entity_type = Practitioner (staff) | Patient (portal)
            └── services/medbackend/
                  base_client.py   shared httpx.AsyncClient, X-Project-ID
                  fhir_client.py   backbone /graphql — FHIR R4 CRUD
                  app_client.py    medbackend-app REST — project, members
```

**The five-layer funnel.** Every feature follows it:

```
routes/<feature>/__init__.py     setup_<feature>_routes(rt) — calls sub-registrars, nothing else
  └─ routes/<feature>/_pages.py  GET → fetch → component → base_layout
       ├─ handlers/<feature>_handlers.py    singleton; catches exceptions, RETURNS FT
       │    └─ services/<feature>_service.py  FHIR ⇄ UI transforms
       │         └─ services/medbackend/fhir_client.py
       └─ components/<feature>/<feature>_component.py   page assembler — pure
            ├─ components/<feature>/ui/{table,stats,header,modals,actions}.py
            └─ components/common/{modal,forms,lazy}.py
```

`_forms` must register before `_pages`, or `POST /x` and `GET /x` collide. A feature starts as one file and becomes a package past ~400 LOC. `ui/` packages export through a barrel `__init__.py` with `__all__`.

## Non-negotiable rules

1. **No local persistence of clinical data.** No SQLite, no PostgreSQL, no ORM, no cache with a TTL. The session holds tokens and claims; everything else is fetched.
2. **Components do no I/O.** No `from services`, no `from handlers`, no `httpx`, no `async def`. Data arrives only as a plain `list` or `dict`.
3. **All outbound HTTP to MedBackend goes through `services/medbackend/`.** A bare `httpx` call elsewhere is a bug.
4. **Every backbone request carries `X-Project-ID`** matching the token's `project_uid` claim. Missing is an HTTP 400 *before* GraphQL runs — it does not look like an auth error.
5. **An empty list means unknown, not none.** backbone's `search_resources` swallows every exception and returns `[]`. Rendering "no allergies" when the query failed is the dangerous version of this bug.
6. **Never re-implement backbone.** RBAC, validation, compartments, terminology and audit are its job. Upstream breakage is filed as an issue, never patched around.
7. **Python-first, JS-last.** FastHTML → CSS → HTMX → inline JS, in that order. Before any `Script()` block, document why CSS and HTMX cannot do it.
8. **Secrets by name and location, never by value** — in code, in docs, in `.env.example`.

## Working with backbone — the traps

- **There is no total.** `ConnectionType.count` is a post-RBAC page length. `Bundle.total` is never read. Counts mean fetching ≤1000 rows and calling `len()`; label them as capped.
- **No `_sort`, `_lastUpdated`, `_include` or `_id`.** No ordering, no incremental sync, and an extra round-trip for every referenced name. Design lists around filters.
- **Every error is HTTP 200 prefixed `Authentication failed:`**, including RBAC denials. `"Access denied"` in the message is the only 403 discriminator.
- **`XUpdate` is a full PUT replace** — no PATCH, no `If-Match`. Re-read immediately before writing.
- **`XCreate` is not idempotent** and backbone does no server-side dedup. Search-before-create on a stable identifier.
- **Writes are denied by default** (`default_access: Forbidden`, templates ship `validation_rules: []`). A 403 on a new resource type is missing configuration, not our bug.
- **Generate client types from introspection against a running server.** backbone's `docs/complete_schema.graphql` is generator input and its `docs/graphql/*` has wrong argument names.
- `XList(count:, offset:)` lowercase; `XConnection(Count:, Offset:)` capitalised. Reads take `String!`, mutations `ID!`.

## Auth

Three identity planes. Staff and patients authenticate to **medbackend-oauth** (`entity_type` `Practitioner` / `Patient`). The tenant owner administering the project authenticates to **Authentik** via medbackend-app — a completely separate identity with no link to the Practitioner one, granting no FHIR access. A clinic admin logs in twice; that is by design.

The JWT carries **no `roles` and no `scope`** — backbone treats `entity_type` as the role. UI sub-roles derive from the practitioner's FHIR `PractitionerRole` resources, fetched once after login.

`/login` returns JSON `{"redirect_url": …}`, not a 302. Code TTL 10 min, access 1 h, refresh 7 days **rotated on every use**. No PKCE; `client_secret` mandatory; exchange server-side only. See the `medbackend-login` skill.

## Upstream dependencies — consumed, never modified

`backbone` (FHIR over GraphQL) · `medbackend-oauth` (patient/practitioner auth) · `medbackend-app` (project, members, RBAC config) · `medterminology`.

## Agents

`.claude/agents/` — `medbackend-contract-guard` (the boundary), `fhir-mapping-reviewer` (clinical correctness), `fasthtml-htmx-specialist` (layout, JS policy, HTMX), `ui-reviewer` (Playwright visual review).

`.claude/hooks/pre-commit-screenshots.sh` blocks a commit touching `routes/`, `components/`, `app.py` or `static/` without a screenshot under 60 minutes old. Starting the dev server is a safe local action — do it yourself.

## Secrets

Infisical project `1df07d5e-69fe-46f2-82e9-a3b638770491` (env `dev`). Prefix commands needing env vars with `infisical run --env=dev --`. No `.env` in this repo — see `infisical` skill.

Only five keys are stored there, because everything else has a code default: `FASTCLINIC_SECRET`, `MEDBACKEND_PROJECT_ID`, `MEDBACKEND_PRACTITIONER_CLIENT_ID`, `MEDBACKEND_PRACTITIONER_CLIENT_SECRET`, `MEDBACKEND_REDIRECT_URI` — exactly the set `config.readiness()` gates on. The three MedBackend URLs come from `_DEFAULTS` in `config/config.py`, keyed by environment. `.env.example` is stale and lists keys nothing reads.

## Restructure — landed

The conversion from a self-contained backend merged as [#1](https://github.com/patrickh217/FastClinic/pull/1) on 2026-08-19 (`aff16c2`). `pms/`, `web/db.py`, `web/ops_db.py`, `web/fhir/`, `web/adapters/`, `web/api.py` and the three legacy auth mechanisms are gone. If you find a reference to any of them, it is a leftover to delete, not an API to use.

Known gap: `components/sidebar.py` lists `/portal`, `/appointments` and `/clinical` in `NAV_ITEMS`, and none are registered routes — a practitioner with the `scheduling` or `clinical` capability gets a 404. Either strip the entries or build the routes; do not add more nav items to unbuilt screens.

Spec: `02 Projects/fastclinic/05 Specs/medbackend-client-restructure.md` in the MyBrain vault.
