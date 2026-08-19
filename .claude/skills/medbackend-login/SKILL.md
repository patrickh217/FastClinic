---
name: medbackend-login
description: >
  Obtain a MedBackend access token headlessly, without a browser, for local testing, scripts
  and e2e tests. Use whenever something needs a real Practitioner or Patient bearer token
  against the dev project, or when an OAuth call is failing and you need to see where.
---

# Headless MedBackend login

The trap this exists to prevent: assuming the authorization code can only come from a browser, then hand-pasting one into an env var that is dead 10 minutes later and single-use. That stalled the original integration for days.

## The flow

`POST /oauth/{project_uid}/{entity_type}/login` returns **JSON**, not a 302:

```bash
BASE=https://dev-auth.medbackend.com
PROJ=$MEDBACKEND_PROJECT_ID
ENTITY=practitioner            # or 'patient' - the path segment is case-normalised
REDIRECT=$MEDBACKEND_REDIRECT_URI

RESP=$(curl -sS -X POST "$BASE/oauth/$PROJ/$ENTITY/login" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\",\"redirect_uri\":\"$REDIRECT\",\"state\":\"x\"}")

CODE=$(echo "$RESP" | sed -n 's/.*[?&]code=\([^&"]*\).*/\1/p')

curl -sS -X POST "$BASE/oauth/$PROJ/$ENTITY/token" \
  -H 'Content-Type: application/json' \
  -d "{\"grant_type\":\"authorization_code\",\"code\":\"$CODE\",\"redirect_uri\":\"$REDIRECT\",\"client_id\":\"$CLIENT_ID\",\"client_secret\":\"$CLIENT_SECRET\"}"
```

Then call backbone with **both** headers:

```bash
curl -sS -X POST "$MEDBACKEND_GRAPHQL_URL" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "X-Project-ID: $MEDBACKEND_PROJECT_ID" \
  -H 'Content-Type: application/json' \
  -d '{"query":"query { Me { reference } }"}'
```

`Me { reference }` is the bootstrap call — it returns `Practitioner/abc-123`, and compartment-scoped queries cannot be built without it.

## Rules that bite

- **`redirect_uri` must be byte-identical** between `/login` and `/token`. `/token` compares the stored value directly.
- The authorization code lives **10 minutes** and is **single-use**. Never store one.
- `client_id` is `medbackend_{project_uid_hex[:8]}_{entity}`. `client_secret` was issued once at user-flow creation and **cannot be rotated** — keep it in Infisical, never in a file.
- Access token 1 h; refresh 7 days and **rotated on every use** — persist the new one or the old chain dies.
- No PKCE. `code_verifier` is accepted and silently ignored; `client_secret` is mandatory.
- `/login` does **not** take `client_id`. Only `/authorize` and `/token` do.

## When it fails

| Response | Cause |
|---|---|
| 404 `Invalid project or entity type` | no `UserFlow` for `(project, entity_type)` in medbackend-oauth's own DB |
| 403 `Email not verified` | the account exists but never verified |
| 403 `Account setup incomplete` | `entity_id` is empty — the FHIR resource is created at email verification, not at signup |
| 401 `Invalid credentials` | also returned for an unknown user; it does not distinguish |
| 400 at `/token` | `redirect_uri` mismatch, or the code expired or was already used |

An account created in medbackend-app is **not** an account here. They are different user tables behind different identity providers.

## Discovery instead of hardcoding

`GET /projects/{project_uid}/connection-info` on medbackend-app (Authentik bearer token) returns `graphql_endpoint`, the required `X-Project-ID` header, and per-flow `client_id` / `auth_url` / `token_url` / `jwks_url` / `allowed_redirect_uris`. Prefer it over pasting URLs.
