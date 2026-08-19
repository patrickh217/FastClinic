# FastClinic

Multi-specialty clinic operations SaaS — a FastHTML + HTMX cockpit for the back office of a clinic spanning general practice, surgical specialties and dental care: patients, appointments, charting, fee invoicing and patient recall.

**FastClinic owns no medical data.** MedBackend is the backend and system of record — FHIR R4 store, multi-tenant RBAC, patient and practitioner OAuth, terminology. This repo holds presentation, clinic workflow, and one MedBackend client package.

Tagline: *Modern clinical care, made personal.* Port **5005**.

## Run it

```bash
python -m venv .venv && .venv/bin/python -m pip install -r requirements.txt
cp .env.example .env          # fill in MEDBACKEND_* from your project's connection-info
.venv/bin/python app.py       # http://localhost:5005
```

You need a MedBackend project to point at. `GET /projects/{project_uid}/connection-info` on medbackend-app returns the GraphQL endpoint, the `X-Project-ID` value, and the per-flow `client_id` / auth URLs. The `client_secret` is issued once at user-flow creation and cannot be rotated, so it comes to you out of band.

```bash
.venv/bin/python -m tools.seed_demo_data      # synthetic FHIR into a dev project
.venv/bin/python -m pytest tests/unit tests/integration      # offline
MEDBACKEND_LIVE_TEST=1 .venv/bin/python -m pytest tests/e2e  # live, against dev
```

`/health` is liveness. `/health/ready` is the deploy gate — it 503s while any required setting is missing or still a placeholder, and reports setting *names* only.

## Layout

```
app.py                  create_app(): SecurityHeaders -> Session -> auth gate -> routes
config/                 per-environment defaults; secrets have no defaults
auth/                   medbackend-oauth authorization-code flow, claims, capabilities
middleware/             deny-by-default gate, security headers
services/medbackend/    the only code that talks to MedBackend
services/               FHIR <-> UI transforms per feature
handlers/               turns service calls into FT, and exceptions into rendered states
components/             server-rendered view functions - no I/O, ever
routes/                 one package per feature: _pages / _modals / _forms / _data
tools/                  demo seeding, one-off conversions
tests/                  unit (offline) / integration (stubbed) / e2e (live, opt-in)
```

Data flows one way: `routes -> handlers -> services -> services/medbackend -> backbone`. Components receive plain lists and dicts and never reach outwards.

## Working against MedBackend

Things that will surprise you, all verified against backbone's source:

- **There is no total.** `ConnectionType.count` is a post-RBAC page length; FHIR's `Bundle.total` is never read upstream. A count means fetching up to 1000 rows and calling `len()`, so every figure in the UI is labelled as capped.
- **No `_sort`, `_lastUpdated`, `_include` or `_id`.** No ordering, no incremental sync, and an extra round-trip for each referenced name. List screens are built around filters.
- **An empty list may mean the query failed** — backbone swallows exceptions and returns `[]`. `SearchResult.certain` carries that distinction, and views render "could not confirm" rather than "none".
- **Every error is HTTP 200 prefixed `Authentication failed:`**, RBAC denials included. `"Access denied"` in the message is the only 403 signal.
- **Writes are denied by default.** `default_access` is `Forbidden` and project templates ship `validation_rules: []`, so each write phase needs per-project RBAC rules first.
- **The JWT carries no roles.** UI capabilities derive from the practitioner's FHIR `PractitionerRole` codings.

## Deployment

`Dockerfile` (python:3.12-slim, port 5005). The container is stateless — no volume, no database, nothing to persist between restarts.

## Status

Phase 1 (read-only cockpit) is in progress: patients list and detail, encounters, overview counts. Appointments, clinical charting, the patient portal, billing and recall follow — each gated on the per-project RBAC rules that writes require.

Data is synthetic. There is no real patient data in this repository.
