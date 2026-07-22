"""Phase 2 — local dev/test harness. Not deployed to Catalyst, not part of the submission.

Run: streamlit run streamlit_harness/app.py
"""
import json

import pandas as pd
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

tab_schema, tab_data, tab_query, tab_pipeline = st.tabs(
    ["Schema Browser", "Data Inspector", "Raw Query Runner", "Pipeline Tester"]
)

try:
    app = get_app()
    connected = True
except Exception as e:  # noqa: BLE001 — surfaced to the UI, not swallowed
    connected = False
    st.error(f"Catalyst connection not configured: {e}")

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

with tab_pipeline:
    st.subheader("Pipeline Tester")
    st.caption(
        "Fires a test question at a deployed Catalyst Function (Stage 1/2 pipeline "
        "once it exists) and shows the raw response envelope: response_type, payload, "
        "answer_text, cited_case_ids, confidence_score, generated_sql, follow_up_questions."
    )
    function_id = st.text_input("Function ID (numeric, from Catalyst console)")
    question = st.text_area("Test question", value="How many cases were registered in Bengaluru last month?")
    extra_args = st.text_area("Extra function args (JSON, optional)", value="{}")
    if connected and st.button("Send"):
        try:
            args = json.loads(extra_args)
            args["question"] = question
            with st.spinner("Calling function..."):
                response = app.functions().execute(int(function_id), args)
            st.json(response)
        except Exception as e:  # noqa: BLE001 — show the real error to the tester
            st.error(str(e))
