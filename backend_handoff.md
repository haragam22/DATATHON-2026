# Backend Handoff (Person B → Person A)

Backend = one Zoho Catalyst Advanced I/O Function: `functions/datathon_2026_function/`. Entry point `main.py`, path-routed (no framework router — just `if request.path == ...`).

## Run it (for frontend wiring — real local server, uvicorn-equivalent)

This is what you want to hit from the frontend during dev. Catalyst's local
equivalent of `uvicorn main:app --reload` is `catalyst serve` — it runs the
Function(s) locally at `http://localhost:6003` (default port), live-reloads
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

Base URL once running: `http://localhost:6003/server/datathon_2026_function`
(Catalyst prefixes each function's routes with `/server/<function-name>`).
So e.g. `POST http://localhost:6003/server/datathon_2026_function/api/query`.

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
