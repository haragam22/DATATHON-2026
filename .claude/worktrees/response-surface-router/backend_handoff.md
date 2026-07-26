# Backend Handoff (Person B → Person A)

Backend = one Zoho Catalyst Advanced I/O Function: `functions/datathon_2026_function/`. Entry point `main.py`, path-routed (no framework router — just `if request.path == ...`).

## Run it (for frontend wiring — real local server, uvicorn-equivalent)

This is what you want to hit from the frontend during dev. Catalyst's local
equivalent of `uvicorn main:app --reload` is `catalyst serve` — it runs the
Function(s) locally at `http://localhost:3000` (confirmed port on this
machine — check your terminal's `catalyst serve` startup log for the actual
port if it differs), live-reloads
on file changes, and proxies real Catalyst services (datastore/auth/cache)
back to the cloud project, so RBAC/DB calls work exactly like prod.

From repo root (not inside the function folder — `catalyst.json` at root
already points `functions.source` at `functions/`):
```
npm install -g zcatalyst-cli   # already installed here, one-time on new machines
catalyst login                 # one-time, opens browser
catalyst serve
```
CLI is already logged into project `datathon-2026` / env `Development` (see
`.catalystrc` at repo root) — should just work.

Base URL once running: `http://localhost:3000/server/datathon_2026_function`
(Catalyst prefixes each function's routes with `/server/<function-name>`).
So e.g. `POST http://localhost:3000/server/datathon_2026_function/api/query`.
Bare `http://localhost:3000/` (no `/server/...` prefix) is Catalyst's local
dev **console UI** (redirects to `/app/`), not the API — don't point the
frontend at that.

Set `ALLOW_UNAUTHENTICATED=true` in the function's env (Catalyst console →
your function → Environment Variables, or a local `.env` if `catalyst serve`
picks one up) while your login flow isn't wired yet — otherwise every
endpoint 401s with no auth token. Turn it back off before prod deploy.

`catalyst deploy` pushes to the actual cloud Function URL instead of
localhost — use that once you want a stable URL that doesn't depend on your
machine being on.

**Local dev harness (Streamlit, not for frontend wiring — manual endpoint testing only):**
```
cd streamlit_harness
pip install -r requirements.txt
streamlit run app.py
```
Has a tab per endpoint pre-filled with sample payloads, plus schema browser / raw ZCQL query runner. `.env` needs whatever `catalyst_client.py` expects (Catalyst project creds). This harness is dev-only, never deployed/submitted.

## Production auth (no OAuth setup needed — this is only for the harness)

The self-client refresh-token/scopes dance in the next section is **only**
for the Streamlit harness, because it's a standalone script running outside
Catalyst and has to authenticate itself from scratch. Production/deployed
code needs none of it.

In prod, `main.py` does `zcatalyst_sdk.initialize(req=request)` —
Catalyst injects whoever's logged in from the incoming HTTP request
automatically. No refresh token, no client_id/secret, no scopes to set up
per environment.

What that means for wiring up the real app:
- Frontend handles login via Catalyst's built-in Authentication service
  (Catalyst client SDK's login flow — a normal user/password or OAuth login
  screen, unrelated to the self-client stuff below). That's on you to wire
  up; ask if you need pointers on Catalyst's client-side auth SDK.
- Once a user's logged in, every request their browser makes to the Function
  carries that identity automatically — `auth.py`'s `resolve_app_user()`
  reads it via `app.authentication().get_current_user()`, maps it to an
  `AppUser`/`AppRole` row, and `check_scope()` gates by role. This already
  works as-is, whether you're hitting `catalyst serve` locally or the
  deployed Function — no separate config per environment.
- `ALLOW_UNAUTHENTICATED` must be **unset or `false`** on the deployed
  Function's env (Catalyst console → your function → Environment
  Variables). Leave it `true` only while testing locally without a login
  flow wired up yet — `true` in prod means any unauthenticated request
  skips RBAC entirely, since there's no logged-in user to check a role
  against.

## Streamlit harness setup (one-time, self-client OAuth)

The harness doesn't use `catalyst login` — it talks to Catalyst as a
standalone script via a Zoho self-client OAuth app, config lives in
`streamlit_harness/.env` (copy from `.env.example`). Three things WILL trip
you up if skipped — all baked into `.env.example` now, but if you're
generating your own credentials from scratch:

1. **Generate the refresh token with the right scopes.** Zoho API Console →
   your Self Client → Generate Code → paste this exact scope string (the
   scope group is called `tables`, NOT `datastore`/`baas` — those names get
   rejected by the console even though the internal REST path is
   `/baas/...`):
   ```
   ZohoCatalyst.tables.READ,ZohoCatalyst.tables.rows.READ,ZohoCatalyst.tables.rows.CREATE,ZohoCatalyst.tables.rows.UPDATE,ZohoCatalyst.tables.rows.DELETE,ZohoCatalyst.tables.columns.READ,ZohoCatalyst.zcql.CREATE
   ```
   The code Zoho gives you expires in 10 minutes — exchange it immediately:
   `POST https://accounts.zoho.in/oauth/v2/token` with
   `grant_type=authorization_code`, `code=<that grant code>`, your
   `client_id`/`client_secret`. The **refresh_token** in that response is
   permanent (doesn't expire — only dies if you regenerate the client secret
   or explicitly revoke it) — that's what goes in `CATALYST_REFRESH_TOKEN`.
   Wrong scope name shows up as `OAUTH_SCOPE_MISMATCH` 401s specifically on
   Schema Browser / Data Inspector calls (query-pipeline tabs use a
   different, already-correct scope, so those working ≠ everything working).

2. **Set `CATALYST_ACCOUNTS_URL`/`X_ZOHO_CATALYST_ACCOUNTS_URL`** to
   `https://accounts.zoho.in` in `.env`. `zcatalyst_sdk` defaults this to a
   nonexistent `accounts.localzoho.com` placeholder and reads it at
   **import time**, so setting it anywhere except before
   `import zcatalyst_sdk` (i.e. top of `catalyst_client.py`, before
   `streamlit`/`app.py` get a chance to) does nothing.

3. **Set `X_ZOHO_CATALYST_CONSOLE_URL=https://console.catalyst.zoho.in`.**
   The self-client refresh-token credential is always treated as ADMIN scope
   by the SDK (it never checks the per-call `user=` kwarg), and ADMIN-scope
   calls route through this var, not `project_domain`/`api.catalyst.zoho.in`.
   Left unset, this silently defaults to a fake `.localzoho.com` host that
   hangs on DNS instead of erroring — the "request never seems to
   finish/nothing happens" symptom, not a clean 401/500.

All three are already in `.env.example` — just fill in the three `<SET_ME>`
values (refresh token, client id, client secret) and everything else works.

Also, `catalyst_client.py` carries one more permanent patch for a real SDK
bug (not an env issue): `zcatalyst_sdk==1.4.0` builds request URLs as
`base_url + "/" + path` where `path` already starts with `/`, producing a
double slash (`accounts.zoho.in//oauth/v2/token`) that 404s with an HTML
error page the SDK then can't `.json()`-parse. Patched via a
`requests.Session.request` wrapper in that file — don't need to touch it
again unless upgrading the SDK fixes it upstream.

## Auth & roles

Every endpoint (except `/`, `/cache`) calls `check_scope(app_user, "<endpoint-name>")`. `app_user` comes from the Catalyst auth token on the request, mapped to an `AppUser` row → `AppRole`.

- No token + `ALLOW_UNAUTHENTICATED=true` → allowed through, audit log gets null user.
- No token + flag off → **401**.
- Token but role lacks scope → **403**.

Role → allowed endpoints:
| Role | Scopes |
|---|---|
| Investigator / Analyst | query, network, similar-cases, aggregates, hotspots, evidence, conversation-export |
| Supervisor | + entity-context, risk-score, financial-trail |
| Policymaker | + admin-backfill-evidence |

So: build role-gating in frontend UI too (hide risk-score/entity-context/financial-trail tabs for Investigator/Analyst users), since the API will 403 them anyway.

## Endpoints

Every JSON response (except PDF export, `/`, `/cache`) is the same envelope:
```json
{
  "response_type": "text|card|chart|map|network|evidence",
  "data": { ... shape varies per endpoint ... },
  "cited_case_ids": [1,2,3],
  "generated_sql": "...",
  "confidence_score": 0.0,
  "follow_up_questions": []
}
```

| Method | Path | Auth scope | Notes |
|---|---|---|---|
| POST | `/api/query` | `query` | Body: `{"question": str, "session_id"?: int}`. Runs NL→SQL pipeline. Creates/continues a conversation session; response `data.session_id` echoes it back — pass it on the next call to continue the thread. On pipeline failure still returns 200 with `data.error` set (not a 4xx) so the frontend can render a chat bubble either way. |
| GET | `/api/network/<case_id>` | `network` | `response_type: "network"`, graph data for the case. |
| GET | `/api/similar-cases/<case_id>` | `similar-cases` | `response_type: "card"`, `data.similar_cases: [{case_id, ...}]`. |
| GET | `/api/entity-context/<accused_id>` | `entity-context` | Supervisor+ only. `data.past_case_ids`. |
| GET | `/api/risk-score/<accused_id>` | `risk-score` | Supervisor+ only. `data.risk_score` (also mirrored into `confidence_score`). |
| GET | `/api/aggregates?type=<type>&date_from=&date_to=&crime_type=` | `aggregates` | `response_type: "chart"`. `type` invalid → 400. |
| GET | `/api/hotspots?date_from=&date_to=&crime_type=` | `hotspots` | `response_type: "map"`, `data.clusters: [{case_ids, ...}]`. |
| GET | `/api/financial-trail/<case_id>` | `financial-trail` | Supervisor+ only. |
| GET | `/api/evidence/<case_id>` | `evidence` | `response_type: "evidence"`, `data.items`. |
| POST | `/api/admin/backfill-evidence-stratus` | `admin-backfill-evidence` | Policymaker only. One-time ops/migration action, not a normal UI button — don't expose this in the main app UI. |
| GET | `/api/conversation/<session_id>/export` | `conversation-export` | Returns raw `application/pdf` bytes, not JSON. `Content-Disposition: attachment; filename=conversation_<id>.pdf`. |
| GET | `/` | none | Health check, `{"status":"success"}`. |

All `<id>` path params must be digits or you get 400 before auth is even checked.

## Errors

Every error path returns `{"error": "<message>"}` with the matching status: 400 (bad input), 401 (no auth), 403 (wrong role), 404 (case/session not found), 405 (wrong HTTP method), 500 (unhandled).

## Known gaps / things to double check before building on top

- Role-scope matrix (above) was confirmed verbally with the user, not written in any spec doc — if requirements change, it lives in `auth.py`'s docstring + `ROLE_SCOPES` dict, not `schema.md`.
- `schema.md` documents column names as `RoleID`/`AppUserID`; actual DB columns (per the data generator) are `RoleID_FK`/`AppUserID_FK`. Trust the code, not that doc, if you see a mismatch elsewhere.
- `/api/admin/backfill-evidence-stratus` is a migration action — don't wire a frontend button to it without checking with me first.
