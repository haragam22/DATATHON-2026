"""Phase 2 — local dev/test harness. Not deployed to Catalyst, not part of the submission.

Run: streamlit run streamlit_harness/app.py
"""
import json

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

from catalyst_client import get_app

load_dotenv()

st.set_page_config(page_title="KSP Crime AI — Dev Harness", layout="wide")
st.title("KSP Crime Database AI — Dev/Test Harness")
st.caption("Internal tool only. Never deployed, never part of the submission.")

# Known tables (schema.md / ddl_reference.md, Phase 1). No SDK call lists all
# tables in a project, so this is the checked-in source of truth.
TABLES = [
    "State", "District", "UnitType", "Unit", "Rank", "Designation", "Employee",
    "CaseCategory", "GravityOffence", "CrimeHead", "CrimeSubHead", "Act", "Section",
    "CrimeHeadActSection", "CaseStatusMaster", "Court", "CasteMaster", "ReligionMaster",
    "OccupationMaster", "CaseMaster", "Inv_OccuranceTime", "ComplainantDetails",
    "ActSectionAssociation", "Victim", "Accused", "ArrestSurrender",
    "inv_arrestsurrenderaccused", "ChargesheetDetails", "Account", "Transaction",
    "AccountCaseLink", "AppRole", "AppUser", "ConversationSession", "ConversationMessage",
    "AuditLog", "RiskScore", "Evidence",
]

# One tab per backend_ultraplan.md phase from here on (Phase 5/6 through 21).
# Endpoints not yet built will just 404/connection-error when hit — that's
# the honest result, not a fake "success", per CLAUDE.md's don't-mark-stubs-
# done rule. Each tab pre-fills the path/method/sample payload so testing a
# phase is just filling in an ID and clicking Send once its Function ships.
PHASE_TABS = [
    ("Query Pipeline (5/6)", "/api/query", "POST", {"question": "How many murder cases were registered in Mysuru district?"}, True),
    ("Follow-ups (10)", "/api/query", "POST", {"question": "How many murder cases were registered in Mysuru district?"}, False),
    ("Network/Graph (11)", "/api/network/1", "GET", None, False),
    ("Similar Cases (13)", "/api/similar-cases/1", "GET", None, False),
    ("Entity Context (14)", "/api/entity-context/1", "GET", None, False),
    ("Risk Score (15)", "/api/risk-score/1", "GET", None, False),
    ("Aggregates (16)", "/api/aggregates?type=trend", "GET", None, True),
    ("Hotspots (16)", "/api/hotspots", "GET", None, True),
    ("RBAC & Audit (17)", "/api/query", "POST", {"question": "test"}, True),
    ("Kannada/Voice (18)", "/api/query", "POST", {"question": "ಮೈಸೂರಿನಲ್ಲಿ ಎಷ್ಟು ಪ್ರಕರಣಗಳು ದಾಖಲಾಗಿವೆ?"}, True),
    ("Financial Trail (19)", "/api/financial-trail/1", "GET", None, True),
    ("Evidence (20)", "/api/evidence/1", "GET", None, True),
    ("Evidence Stratus Backfill (20, admin)", "/api/admin/backfill-evidence-stratus", "POST", {}, True),
    ("PDF Export (21)", "/api/conversation/1/export", "GET", None, True),
]

tab_names = ["Schema Browser", "Data Inspector", "Raw Query Runner", "Add Evidence"] + [t[0] for t in PHASE_TABS]
tabs = st.tabs(tab_names)
tab_schema, tab_data, tab_query, tab_evidence_add = tabs[0], tabs[1], tabs[2], tabs[3]
phase_tabs = tabs[4:]

try:
    app = get_app()
    connected = True
except Exception as e:  # noqa: BLE001 — surfaced to the UI, not swallowed
    connected = False
    st.error(f"Catalyst connection not configured: {e}")

st.sidebar.subheader("Deployed Function")
base_url = st.sidebar.text_input(
    "Function base URL (Catalyst console -> this Function -> Domain)",
    value="", placeholder="https://datathon-2026-xxxx.development.catalystserverless.in",
    key="function_base_url",
)


def call_endpoint(path: str, method: str, payload: dict | None):
    if not base_url:
        st.warning("Set the Function base URL in the sidebar first.")
        return
    url = base_url.rstrip("/") + path
    try:
        with st.spinner(f"{method} {path}"):
            if method == "GET":
                resp = requests.get(url, timeout=60)
            else:
                resp = requests.post(url, json=payload, timeout=60)
        st.caption(f"HTTP {resp.status_code}")
        try:
            st.json(resp.json())
        except ValueError:
            st.code(resp.text)
    except Exception as e:  # noqa: BLE001 — show the real network/HTTP error to the tester
        st.error(str(e))

with tab_schema:
    st.subheader("Schema Browser")
    table = st.selectbox("Table", TABLES, key="schema_table")
    if connected and st.button("Load columns", key="load_columns"):
        with st.spinner("Fetching column metadata..."):
            cols = app.datastore().table(table).get_all_columns()
        df = pd.DataFrame(cols)
        st.dataframe(df, use_container_width=True)

with tab_data:
    st.subheader("Data Inspector")
    table = st.selectbox("Table", TABLES, key="data_table")
    limit = st.number_input("Row limit", min_value=1, max_value=1000, value=25)
    if connected and st.button("Preview rows", key="preview_rows"):
        query = f"SELECT * FROM {table} LIMIT {int(limit)}"
        with st.spinner(query):
            result = app.zcql().execute_query(query)
        if not result:
            st.info("Table is empty.")
        else:
            rows = [list(r.values())[0] for r in result] if isinstance(result[0], dict) else result
            st.dataframe(pd.DataFrame(rows), use_container_width=True)

with tab_query:
    st.subheader("Raw ZCQL Query Runner")
    st.caption("SELECT / INSERT / UPDATE / DELETE against the primary Data Store.")
    query = st.text_area("ZCQL query", value="SELECT * FROM CaseMaster LIMIT 10", height=100)
    if connected and st.button("Run query"):
        try:
            with st.spinner("Running..."):
                result = app.zcql().execute_query(query)
            st.success(f"{len(result)} row(s) returned.")
            st.json(result)
        except Exception as e:  # noqa: BLE001 — show the real ZCQL error to the tester
            st.error(str(e))

with tab_evidence_add:
    st.subheader("Add Evidence")
    st.caption(
        "Uploads a file straight to the 'evidences' Stratus bucket and writes the "
        "Evidence row — via this harness's admin-scope SDK credentials, not the "
        "deployed Function (whose per-request scope can't reach the developer "
        "machine's local files). This is the practical way to backfill real "
        "Stratus URLs for Phase 20, one file at a time."
    )
    st.warning(
        "CLAUDE.md: evidence is placeholder/stock content only. No real or "
        "fake photorealistic photos of synthetic people or realistic crime "
        "scenes — that's a credibility risk, not a feature. Stick to "
        "generic/abstract placeholders (e.g. a document scan, a blurred "
        "object photo, an evidence-tag close-up) if generating new images."
    )
    ev_case_id = st.number_input("CaseMasterID (business ID, not ROWID)", min_value=1, step=1, key="ev_case_id")
    ev_type = st.selectbox("Evidence type", ["image", "audio", "document"], key="ev_type")
    ev_description = st.text_input("Description", key="ev_description")
    ev_file = st.file_uploader("File", key="ev_file")
    if connected and st.button("Upload and link to case", key="ev_submit"):
        if not ev_file:
            st.warning("Choose a file first.")
        else:
            try:
                with st.spinner("Looking up case..."):
                    case_rows = app.zcql().execute_query(
                        f"SELECT ROWID FROM CaseMaster WHERE CseMasterID = {int(ev_case_id)}"
                    )
                    if case_rows and isinstance(case_rows[0], dict) and "ROWID" not in case_rows[0]:
                        case_rows = [list(r.values())[0] for r in case_rows]  # unwrap {table: {...}} nesting
                if not case_rows:
                    st.error(f"No CaseMaster row with CseMasterID={int(ev_case_id)}.")
                else:
                    case_rowid = int(case_rows[0]["ROWID"])
                    key = f"{int(ev_case_id)}_{ev_file.name}"
                    with st.spinner(f"Uploading {ev_file.name} to Stratus..."):
                        bucket = app.stratus().bucket("evidences")
                        bucket.put_object(key, ev_file.getvalue())
                        object_url = bucket.object(key).get_details().get("object_url")
                    if not object_url:
                        st.error("Upload succeeded but Stratus returned no object_url.")
                    else:
                        with st.spinner("Writing Evidence row..."):
                            uploaded_row = app.datastore().table("Evidence").insert_row({
                                "CaseMasterID_FK": case_rowid,
                                "EvidenceType": ev_type,
                                "FileURL": object_url,
                                "Description": ev_description,
                                "UploadedDate": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                            })
                        st.success(f"Uploaded and linked. FileURL: {object_url}")
                        st.json(uploaded_row)
            except Exception as e:  # noqa: BLE001 — show the real Stratus/Data Store error to the tester
                st.error(str(e))

_BUILT_NOTE = {
    True: "Built (functions/datathon_2026_function/pipeline.py) — response envelope: response_type, data, cited_case_ids, generated_sql, confidence_score, follow_up_questions.",
    False: "Not built yet — will 404/connection-error until its Function/route ships. Path and sample payload are pre-filled for when it does.",
}

for (name, default_path, default_method, default_payload, is_built), tab in zip(PHASE_TABS, phase_tabs):
    with tab:
        st.subheader(name)
        st.caption(_BUILT_NOTE[is_built])
        path = st.text_input("Path", value=default_path, key=f"path_{name}")
        method = st.selectbox("Method", ["GET", "POST"], index=0 if default_method == "GET" else 1, key=f"method_{name}")
        payload_text = st.text_area(
            "JSON body (POST only)",
            value=json.dumps(default_payload, indent=2) if default_payload else "{}",
            key=f"payload_{name}", height=100,
        )
        if st.button("Send", key=f"send_{name}"):
            try:
                payload = json.loads(payload_text) if method == "POST" else None
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON body: {e}")
            else:
                call_endpoint(path, method, payload)
