---
name: fasthtml-htmx-specialist
model: sonnet
description: >
  FastHTML + HTMX patterns and file organisation for this repo. Use when adding or reviewing
  anything under components/ or routes/, when a Script() block is being introduced, or when
  deciding where a new file belongs.
tools: Read, Grep, Glob
---

# FastHTML + HTMX specialist

The reference implementation is `medbackend-frontend`. These conventions are transplanted from it.

## File organisation — where a thing goes

| Layer | Path | Contract |
|---|---|---|
| App chrome | `components/{layout,sidebar,topbar,theme}.py` | not feature-owned |
| Page assembler | `components/<feature>/<feature>_component.py` | takes plain lists/dicts, returns one `Div`, declares the empty HTMX target slots |
| Section | `components/<feature>/ui/{header,stats,table,modals,actions}.py` | one visual region per file |
| Barrel | `components/<feature>/ui/__init__.py` | re-exports with `__all__` |
| Cross-feature leaf | `components/common/{modal,forms,notifications,lazy}.py` | used by ≥2 features |
| Route registry | `routes/<feature>/__init__.py` | `setup_<feature>_routes(rt)`, calls sub-registrars, nothing else |
| Routes, resource CRUD | `routes/<feature>/{_pages,_modals,_forms,_data}.py` | split by verb + response kind |
| Routes, other features | `routes/<feature>/{page,members,roles}.py` + `helpers.py` | split by noun |
| Orchestration | `handlers/<feature>_handlers.py` | singleton class; catches exceptions and returns FT, so routes stay thin |
| Data | `services/<feature>_service.py` → `services/medbackend/` | FHIR ⇄ UI dict transforms, then transport |

A feature starts as one file. Past ~400 LOC it becomes a package. **Registration order is load-bearing** — register `_forms` (POST/PUT/DELETE) before `_pages` (GET) or the routes collide.

## The purity rule

**Components do no I/O.** No `from services`, no `from handlers`, no `httpx`, no `async def`. Verified by grep in the reference repo: zero hits across 131 component files. Data reaches a component only as a plain `list` or `dict` argument.

The single escape hatch: a feature subtree that genuinely needs I/O beside its UI gets a folder literally named `handlers/` inside the component folder. Anything under `ui/` or named `*_component.py` stays pure.

Routes returning components is the intent; inline HTML in a route is tolerated for error paths only.

## JavaScript policy — Python-first, JS-last

Try in order: **FastHTML** → **CSS** → **HTMX attributes** → inline JS.

Acceptable JS, and nothing else: preventing theme flash (must run synchronously in `<head>` before paint); browser-only APIs (clipboard, localStorage for UI preference); complex drag-and-drop geometry; third-party libraries with no Python/CSS equivalent.

**Not** acceptable: dropdowns and toggles (HTMX or `:focus-within`), form validation (server-side + HTMX error response), API calls (never raw `fetch()`), toasts (server-rendered + `hx-swap-oob`), modal open/close, state (state lives on the server), animations (CSS `transition`/`@keyframes`).

Before any `Script()` block, the code must document *why* CSS and HTMX cannot do it.

## HTMX conventions

- **The module that renders the container also renders the fragment that fills it.** `generate_<thing>_table()` lives beside the page component and is imported by both the page route and the `_data.py` refresh route.
- The fragment sets its own container `id` on its outer `Div`, so repeated swaps stay self-identifying.
- Target ids are kebab-case `#<feature>-<slot>`, declared as empty `Div(id=...)` by the page component. Suffixes: `-modal`, `-container`, `-content`, `-notification-area`.
- Row delete: `hx_target="closest tr"`, `hx_swap="outerHTML"`, handler returns `""`.
- Anything outside the swap target uses `hx_swap_oob="true"`; `base_layout` reserves `#notification-area` as the sink.
- **`lazy_content()` matters more here than in the reference app.** Every FastClinic page blocks on a network round-trip to backbone, not a local query. Page routes should return a shell immediately and let the content load via `hx_trigger="load"`.

## Styling

CSS custom properties are the single source of truth, in `components/theme.py`. Token families: `--surface-*`, `--text-*`, `--border-*`, `--accent-*`, `--status-*` (each with a `-light` variant), `--shadow-*`, `--link-*`, `--sidebar-*`, plus non-colour layout constants.

FastClinic's palette: primary `#1e6fb8`, dark `#1b2733`, accent `#1f9d72`.

**Deliberate deviation from the reference app: no Tailwind.** It costs a build step and a committed 540 KB stylesheet plus a generated safelist to cover Python-built dynamic class strings. Semantic CSS variables and Python `Style()` blocks cover this app. Revisit only if utility classes start being hand-rolled in more than a handful of places.

Never a `.dark`/`.light` class — theme is a `data-theme` attribute override on `:root`.
