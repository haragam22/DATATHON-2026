"""Phase 17 backend half — RBAC role-scope enforcement + AuditLog writes.

Role-scope matrix (confirmed with the user, not in any doc — flagging that
gap per CLAUDE.md rather than inventing it silently):
  Investigator / Analyst : query, network, similar-cases, aggregates, hotspots, evidence
  Supervisor / Policymaker : all of the above, plus entity-context, risk-score,
    financial-trail (individual-level / sensitive-data endpoints)
  Policymaker only : admin-backfill-evidence (a one-time ops/migration
    action, not a normal user query — there's no formal "Admin" role in
    schema.md's 4-role list, so the highest tier is the closest fit)

Unauthenticated requests (no Catalyst user token — e.g. the Streamlit
harness, or a frontend call made before Person A's login flow sends one) are
allowed through with AppUserID left null in the audit trail, ONLY when
ALLOW_UNAUTHENTICATED=true is set in the Function's environment — this keeps
CLAUDE.md's "use the harness continuously" workflow unblocked in dev without
leaving RBAC fail-open in the deployed prod Function (flagged by security
review: omitting the auth header would otherwise skip role checks entirely).
Unset/false in production -> unauthenticated requests get 401.

Built column names below (RoleID_FK, AppUserID_FK, Time_stamp) come from
data_generation/generators/app_layer.py's actual write path, which differs
from schema.md's doc table (RoleID/AppUserID without _FK) — same drift
pattern CLAUDE.md already flags elsewhere; trusting the generator since it's
what's actually been written to the Data Store.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import zcql_util

_ALLOW_UNAUTHENTICATED = os.environ.get("ALLOW_UNAUTHENTICATED", "").lower() == "true"

ROLE_SCOPES: dict[str, set[str]] = {
    "Investigator": {"query", "network", "similar-cases", "aggregates", "hotspots", "evidence", "conversation-export"},
    "Analyst": {"query", "network", "similar-cases", "aggregates", "hotspots", "evidence", "conversation-export"},
    "Supervisor": {"query", "network", "similar-cases", "aggregates", "hotspots", "evidence", "conversation-export", "entity-context", "risk-score", "financial-trail"},
    "Policymaker": {"query", "network", "similar-cases", "aggregates", "hotspots", "evidence", "conversation-export", "entity-context", "risk-score", "financial-trail", "admin-backfill-evidence"},
}


class ForbiddenScope(Exception):
    pass


class AuthenticationRequired(Exception):
    """Raised when there's no identifiable Catalyst user AND
    ALLOW_UNAUTHENTICATED isn't set — callers should map this to 401,
    distinct from ForbiddenScope's 403 (known user, wrong role)."""


def resolve_app_user(app: Any, zcql_service: Any) -> dict[str, Any] | None:
    """Best-effort lookup of the calling Catalyst user's AppUser row + role
    name. Returns None whenever there's no authenticated user on this
    request — callers must treat None as "unauthenticated, allow through",
    never as an error (see module docstring)."""
    try:
        current_user = app.authentication().get_current_user()
    except Exception:
        return None
    if not current_user or not current_user.get("user_id"):
        return None

    auth_id = str(current_user["user_id"]).replace("'", "''")
    user_rows = zcql_util.run(
        zcql_service, f"SELECT ROWID, AppUserID, RoleID_FK FROM AppUser WHERE CatalystAuthID = '{auth_id}'",
    )
    if not user_rows:
        return None
    user_row = user_rows[0]

    role_rows = zcql_util.run(
        zcql_service, f"SELECT RoleName FROM AppRole WHERE ROWID = {int(user_row['RoleID_FK'])}",
    )
    role_name = role_rows[0]["RoleName"] if role_rows else None

    return {
        "app_user_rowid": int(user_row["ROWID"]),
        "app_user_id": int(user_row["AppUserID"]),
        "role_name": role_name,
    }


def check_scope(app_user: dict[str, Any] | None, endpoint: str) -> None:
    """Raises AuthenticationRequired (401) if there's no identifiable user
    and ALLOW_UNAUTHENTICATED isn't set (deny by default in prod). Raises
    ForbiddenScope (403) if an authenticated user's role doesn't cover this
    endpoint. Only passes unauthenticated through when the dev/harness flag
    is explicitly on."""
    if app_user is None:
        if _ALLOW_UNAUTHENTICATED:
            return
        raise AuthenticationRequired("authentication required")
    role_name = app_user.get("role_name")
    allowed = ROLE_SCOPES.get(role_name, set())
    if endpoint not in allowed:
        raise ForbiddenScope(f"role {role_name!r} is not permitted to access {endpoint!r}")


def write_audit_log(
    app: Any, app_user: dict[str, Any] | None, question: str, generated_sql: str, result_row_count: int,
) -> None:
    """Writes one AuditLog row for a completed /api/query call. Failures are
    logged by the caller, never silently swallowed (CLAUDE.md) — this
    function lets exceptions propagate."""
    app.datastore().table("AuditLog").insert_row({
        "AppUserID_FK": app_user["app_user_rowid"] if app_user else None,
        "QueryText": question,
        "GeneratedSQL": generated_sql,
        "Time_stamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(sep=" "),
        "ResultRowCount": result_row_count,
    })


def _demo() -> None:
    """ponytail self-check: scope matrix + resolve_app_user's None-handling,
    no live ZCQL/Catalyst auth involved."""
    class _FakeZcql:
        def __init__(self, tables: dict[str, list[dict[str, Any]]]):
            self._tables = tables

        def execute_query(self, sql: str):
            table = sql.split("FROM", 1)[1].split()[0]
            rows = self._tables.get(table, [])
            if "CatalystAuthID = '" in sql:
                wanted = sql.split("CatalystAuthID = '", 1)[1].split("'")[0]
                rows = [r for r in rows if r.get("CatalystAuthID") == wanted]
            return rows

    class _FakeAuth:
        def __init__(self, user: dict[str, Any] | None, raises: bool = False):
            self._user = user
            self._raises = raises

        def get_current_user(self):
            if self._raises:
                raise RuntimeError("no session")
            return self._user

    class _FakeApp:
        def __init__(self, auth: _FakeAuth):
            self._auth = auth

        def authentication(self):
            return self._auth

    zcql = _FakeZcql({
        "AppUser": [{"ROWID": 1, "AppUserID": 1, "RoleID_FK": 1, "CatalystAuthID": "auth-1"}],
        "AppRole": [{"ROWID": 1, "RoleName": "Investigator"}],
    })

    # No Catalyst user token at all -> unauthenticated.
    app_anon = _FakeApp(_FakeAuth(None, raises=True))
    assert resolve_app_user(app_anon, zcql) is None

    # Deny by default in prod (ALLOW_UNAUTHENTICATED unset/false).
    global _ALLOW_UNAUTHENTICATED
    _ALLOW_UNAUTHENTICATED = False
    try:
        check_scope(None, "risk-score")
        raise AssertionError("expected AuthenticationRequired")
    except AuthenticationRequired:
        pass

    # Dev/harness bypass only when the flag is explicitly on.
    _ALLOW_UNAUTHENTICATED = True
    check_scope(None, "risk-score")  # must not raise
    _ALLOW_UNAUTHENTICATED = False

    # Authenticated Investigator -> allowed on "query", forbidden on "risk-score".
    app_known = _FakeApp(_FakeAuth({"user_id": "auth-1"}))
    app_user = resolve_app_user(app_known, zcql)
    assert app_user == {"app_user_rowid": 1, "app_user_id": 1, "role_name": "Investigator"}, app_user
    check_scope(app_user, "query")
    try:
        check_scope(app_user, "risk-score")
        raise AssertionError("expected ForbiddenScope")
    except ForbiddenScope:
        pass

    # Authenticated but no matching AppUser row -> treated as unauthenticated.
    app_unknown = _FakeApp(_FakeAuth({"user_id": "auth-999"}))
    assert resolve_app_user(app_unknown, zcql) is None

    print("auth._demo: all assertions passed")


if __name__ == "__main__":
    _demo()
