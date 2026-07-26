"""Phase 21 backend half — live conversation logging + PDF export.

Nothing wrote ConversationSession/ConversationMessage before this (only
AuditLog was live-written, Phase 17) — app_layer.py's rows are synthetic
seed data only. Session flow (confirmed with the user): /api/query accepts
an optional "session_id" in its request body; when absent, the backend
creates a new ConversationSession and returns its SessionID in the response
envelope's data dict for the client to reuse on later turns in the same
conversation.

Built column names (AppUserID_FK, SessionID_FK) come from
data_generation/generators/app_layer.py's actual write path, same _FK doc
drift already flagged for AuditLog/RBAC — schema.md's table lists
"AppUserID"/"SessionID" without the suffix.

GET /api/conversation/{session_id}/export: assembles the session's
ConversationMessage history into an HTML transcript, then calls
zcatalyst_sdk's confirmed `SmartBrowz.convert_to_pdf(html)` (reads the
installed SDK source directly — it POSTs {"html": ...} and returns the raw
requests.Response; PDF bytes are in .content) to render it as a PDF.
"""

from __future__ import annotations

import html as html_escape
from datetime import datetime, timezone
from typing import Any

import zcql_util


def _catalyst_now() -> str:
    """Default timestamp for Catalyst DateTime columns. Must be a naive
    'YYYY-MM-DD HH:MM:SS' string with NO timezone offset suffix — the actual
    bug behind repeated 'datetime value expected' errors was
    datetime.now(timezone.utc).isoformat() appending '+00:00', which the
    Data Store API rejects outright (epoch-millis was also rejected).
    Matches the naive-isoformat convention data_generation's CSV bulk-import
    generators already use successfully for the same DateTime columns."""
    return datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None).isoformat(sep=" ")


class SessionNotFound(Exception):
    pass


class ConversationForbidden(Exception):
    pass


# Supervisor/Policymaker may view any session (same elevated tier used for
# entity-context/risk-score/financial-trail elsewhere) — everyone else may
# only touch a session they own. Flagged by security review as an IDOR
# otherwise: any caller could read/export any session_id.
_ELEVATED_ROLES = {"Supervisor", "Policymaker"}


def _check_ownership(owner_rowid: int | None, app_user: dict[str, Any] | None) -> None:
    if app_user and app_user.get("role_name") in _ELEVATED_ROLES:
        return
    caller_rowid = app_user["app_user_rowid"] if app_user else None
    if owner_rowid != caller_rowid:
        raise ConversationForbidden("not permitted to access this conversation session")


def get_or_create_session(app: Any, zcql_service: Any, app_user: dict[str, Any] | None, session_id: int | None) -> int:
    """Returns a business SessionID — either the given one (verified to
    exist AND owned by app_user) or a newly created session's."""
    if session_id is not None:
        rows = zcql_util.run(zcql_service, f"SELECT SessionID, AppUserID_FK FROM ConversationSession WHERE SessionID = {int(session_id)}")
        if not rows:
            raise SessionNotFound(f"SessionID {session_id} not found")
        owner = rows[0].get("AppUserID_FK")
        _check_ownership(int(owner) if owner is not None else None, app_user)
        return int(session_id)

    now = _catalyst_now()
    # SessionID is a mandatory business column, not the table's auto-increment
    # ROWID, so it must be supplied on insert. Compute next value ourselves;
    # ponytail: max+1 race under concurrent inserts, acceptable for this MVP.
    max_rows = zcql_util.run(zcql_service, "SELECT SessionID FROM ConversationSession ORDER BY SessionID DESC LIMIT 1")
    next_session_id = int(max_rows[0]["SessionID"]) + 1 if max_rows else 1
    app.datastore().table("ConversationSession").insert_row({
        "SessionID": next_session_id,
        "AppUserID_FK": app_user["app_user_rowid"] if app_user else None,
        "StartedAt": now,
        "EndedAt": None,
    })
    return next_session_id


def log_message(
    app: Any, zcql_service: Any, session_id: int, role: str, message_text: str,
    generated_sql: str = "", confidence_score: float | None = None, cited_case_ids: list[int] | None = None,
) -> None:
    session_rows = zcql_util.run(zcql_service, f"SELECT ROWID FROM ConversationSession WHERE SessionID = {int(session_id)}")
    if not session_rows:
        raise SessionNotFound(f"SessionID {session_id} not found")
    session_rowid = int(session_rows[0]["ROWID"])

    max_rows = zcql_util.run(zcql_service, "SELECT MessageID FROM ConversationMessage ORDER BY MessageID DESC LIMIT 1")
    next_message_id = int(max_rows[0]["MessageID"]) + 1 if max_rows else 1
    app.datastore().table("ConversationMessage").insert_row({
        "MessageID": next_message_id,
        "SessionID_FK": session_rowid,
        "Role": role,
        "MessageText": message_text,
        "GeneratedSQL": generated_sql,
        "ConfidenceScore": confidence_score,
        "CitedCaseMasterIDs": ",".join(str(c) for c in (cited_case_ids or [])),
        "CreatedAt": _catalyst_now(),
    })


def get_conversation_history(session_id: int, zcql_service: Any, app_user: dict[str, Any] | None) -> list[dict[str, Any]]:
    session_rows = zcql_util.run(zcql_service, f"SELECT ROWID, AppUserID_FK FROM ConversationSession WHERE SessionID = {int(session_id)}")
    if not session_rows:
        raise SessionNotFound(f"SessionID {session_id} not found")
    owner = session_rows[0].get("AppUserID_FK")
    _check_ownership(int(owner) if owner is not None else None, app_user)
    session_rowid = int(session_rows[0]["ROWID"])

    rows = zcql_util.run(
        zcql_service,
        f"SELECT MessageID, Role, MessageText, GeneratedSQL, ConfidenceScore, CitedCaseMasterIDs, CreatedAt "
        f"FROM ConversationMessage WHERE SessionID_FK = {session_rowid}",
    )
    rows.sort(key=lambda r: (r.get("CreatedAt") or "", int(r.get("MessageID", 0))))
    return rows


def render_transcript_html(session_id: int, messages: list[dict[str, Any]]) -> str:
    rows_html = []
    for m in messages:
        role = html_escape.escape(str(m.get("Role", "")))
        text = html_escape.escape(str(m.get("MessageText", "")))
        created_at = html_escape.escape(str(m.get("CreatedAt", "")))
        rows_html.append(
            f'<div class="msg {role}"><div class="meta">{role} &middot; {created_at}</div>'
            f'<div class="text">{text}</div></div>'
        )
    return (
        "<html><head><meta charset='utf-8'><style>"
        "body{font-family:sans-serif;margin:2em;} "
        ".msg{margin-bottom:1em;padding:0.75em;border-radius:6px;} "
        ".user{background:#eef2ff;} .assistant{background:#f0fdf4;} "
        ".meta{font-size:0.8em;color:#666;margin-bottom:0.25em;}"
        "</style></head><body>"
        f"<h2>Conversation {session_id} — Export</h2>"
        + "".join(rows_html) +
        "</body></html>"
    )


def export_conversation_pdf(app: Any, session_id: int, zcql_service: Any, app_user: dict[str, Any] | None) -> bytes:
    messages = get_conversation_history(session_id, zcql_service, app_user)
    html_doc = render_transcript_html(session_id, messages)
    resp = app.smartbrowz().convert_to_pdf(html_doc)
    return resp.content


def _demo() -> None:
    """ponytail self-check: session creation, message logging, history
    ordering, HTML rendering — no live ZCQL/Stratus/SmartBrowz involved."""
    class _FakeTable:
        def __init__(self, store: dict[str, list[dict[str, Any]]], name: str, next_id: list[int]):
            self._store, self._name, self._next_id = store, name, next_id

        def insert_row(self, row: dict[str, Any]):
            id_col = "SessionID" if self._name == "ConversationSession" else "MessageID"
            row = dict(row, **{id_col: self._next_id[0], "ROWID": self._next_id[0]})
            self._next_id[0] += 1
            self._store.setdefault(self._name, []).append(row)
            return row

    class _FakeDatastore:
        def __init__(self, store, next_id):
            self._store, self._next_id = store, next_id

        def table(self, name: str):
            return _FakeTable(self._store, name, self._next_id)

    class _FakeZcql:
        def __init__(self, store: dict[str, list[dict[str, Any]]]):
            self._store = store

        def execute_query(self, sql: str):
            table = sql.split("FROM", 1)[1].split()[0]
            rows = self._store.get(table, [])
            if "SessionID_FK = " in sql:
                val = int(sql.split("SessionID_FK = ", 1)[1].split()[0])
                rows = [r for r in rows if int(r.get("SessionID_FK", -1)) == val]
            elif "SessionID = " in sql:
                val = int(sql.split("SessionID = ", 1)[1].split()[0])
                rows = [r for r in rows if int(r.get("SessionID", -1)) == val]
            elif "AppUserID_FK = " in sql:
                val = int(sql.split("AppUserID_FK = ", 1)[1].split()[0])
                rows = [r for r in rows if int(r.get("AppUserID_FK", -1)) == val]
            if "ORDER BY SessionID DESC" in sql:
                rows = sorted(rows, key=lambda r: int(r["SessionID"]), reverse=True)[:1]
            return rows

    class _FakeApp:
        def __init__(self, store, next_id):
            self._datastore = _FakeDatastore(store, next_id)

        def datastore(self):
            return self._datastore

    store: dict[str, list[dict[str, Any]]] = {}
    app = _FakeApp(store, [1])
    zcql = _FakeZcql(store)
    app_user = {"app_user_rowid": 7}

    session_id = get_or_create_session(app, zcql, app_user, None)
    assert session_id == 1, session_id

    same_session_id = get_or_create_session(app, zcql, app_user, session_id)
    assert same_session_id == session_id

    log_message(app, zcql, session_id, "user", "How many murder cases in Mysuru?")
    log_message(app, zcql, session_id, "assistant", "3 cases found.", generated_sql="SELECT ...", confidence_score=0.9, cited_case_ids=[1, 2, 3])

    history = get_conversation_history(session_id, zcql, app_user)
    assert len(history) == 2, history
    assert history[0]["Role"] == "user" and history[1]["Role"] == "assistant", history

    html_doc = render_transcript_html(session_id, history)
    assert "How many murder cases" in html_doc and "3 cases found." in html_doc, html_doc

    try:
        get_conversation_history(999, zcql, app_user)
        raise AssertionError("expected SessionNotFound")
    except SessionNotFound:
        pass

    # IDOR check: a different user can't read someone else's session...
    other_user = {"app_user_rowid": 8, "role_name": "Investigator"}
    try:
        get_conversation_history(session_id, zcql, other_user)
        raise AssertionError("expected ConversationForbidden")
    except ConversationForbidden:
        pass
    try:
        get_or_create_session(app, zcql, other_user, session_id)
        raise AssertionError("expected ConversationForbidden")
    except ConversationForbidden:
        pass
    # ...but an elevated role can.
    supervisor = {"app_user_rowid": 9, "role_name": "Supervisor"}
    get_conversation_history(session_id, zcql, supervisor)  # must not raise

    print("conversation._demo: all assertions passed")


if __name__ == "__main__":
    _demo()
