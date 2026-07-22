"""AppRole, AppUser, ConversationSession/Message, AuditLog, RiskScore,
Evidence (rows + placeholder files via evidence.py).

AppUser.CatalystAuthID is an explicit placeholder (`<SET_ME:auth-id-N>`)
per CLAUDE.md — real Catalyst Authentication IDs only exist once accounts
are provisioned in the deployed app; this generator cannot invent valid
ones.

RiskScore.TopFeaturesJSON / CounterfactualJSON: placeholder JSON *shape*
only, not real SHAP output — the model that produces real values doesn't
exist at Phase 3. Kept obviously synthetic (feature names are generic
column references, not tuned weights).
"""

from __future__ import annotations

import datetime
import json
import random
from typing import Any

from data_generation.generators.evidence import generate_placeholder_audio, generate_placeholder_image
from data_generation.utils import id_sequence, write_csv

random.seed(47)

ROLES = ["Investigator", "Analyst", "Supervisor", "Policymaker"]
EVIDENCE_TYPES = ["image", "audio", "document"]  # "video" omitted — no video generator (see evidence.py)
SAMPLE_QUESTIONS = [
    "How many cases were registered in {district} last month?",
    "List accused with more than one arrest in {district}.",
    "What is the trend of theft cases over the last year?",
    "Show cases under BNS section 103(1).",
]


def generate_app_roles() -> list[dict[str, Any]]:
    ids = id_sequence(1)
    rows = [{"RoleID": next(ids), "RoleName": r} for r in ROLES]
    write_csv(rows, "AppRole")
    return rows


def generate_app_users(
    employee_rows: list[dict[str, Any]],
    employee_rowid_map: dict[int, int],
    role_rows: list[dict[str, Any]],
    role_rowid_map: dict[int, int],
    count: int = 30,
) -> list[dict[str, Any]]:
    ids = id_sequence(1)
    rows = []
    sample_employees = random.sample(employee_rows, k=min(count, len(employee_rows)))
    for employee in sample_employees:
        user_id = next(ids)
        role = random.choice(role_rows)
        rows.append({
            "AppUserID": user_id,
            "CatalystAuthID": f"<SET_ME:auth-id-{user_id}>",
            "EmployeeID_FK": employee_rowid_map[employee["EmployeeID"]],
            "RoleID_FK": role_rowid_map[role["RoleID"]],
        })
    write_csv(rows, "AppUser")
    return rows


def generate_conversation_sessions(
    app_user_rows: list[dict[str, Any]],
    app_user_rowid_map: dict[int, int],
    count: int = 100,
) -> list[dict[str, Any]]:
    ids = id_sequence(1)
    rows = []
    for _ in range(count):
        user = random.choice(app_user_rows)
        started = datetime.datetime.now().replace(microsecond=0) - datetime.timedelta(days=random.randint(0, 365), hours=random.randint(0, 23))
        ended = started + datetime.timedelta(minutes=random.randint(2, 45))
        rows.append({
            "SessionID": next(ids),
            "AppUserID_FK": app_user_rowid_map[user["AppUserID"]],
            "StartedAt": started.isoformat(sep=" "),
            "EndedAt": ended.isoformat(sep=" "),
        })
    write_csv(rows, "ConversationSession")
    return rows


def generate_conversation_messages(
    session_rows: list[dict[str, Any]],
    session_rowid_map: dict[int, int],
    case_master_rows: list[dict[str, Any]],
    case_master_rowid_map: dict[int, int],
    district_names: list[str],
) -> list[dict[str, Any]]:
    ids = id_sequence(1)
    rows = []
    for session in session_rows:
        started = datetime.datetime.fromisoformat(session["StartedAt"])
        question = random.choice(SAMPLE_QUESTIONS).format(district=random.choice(district_names))
        cited_cases = random.sample(case_master_rows, k=min(3, len(case_master_rows)))
        cited_ids = ",".join(str(case_master_rowid_map[c["CaseMasterID"]]) for c in cited_cases)

        rows.append({
            "MessageID": next(ids),
            "SessionID_FK": session_rowid_map[session["SessionID"]],
            "Role": "user",
            "MessageText": question,
            "GeneratedSQL": "",
            "ConfidenceScore": None,
            "CitedCaseMasterIDs": "",
            "CreatedAt": started.isoformat(sep=" "),
        })
        rows.append({
            "MessageID": next(ids),
            "SessionID_FK": session_rowid_map[session["SessionID"]],
            "Role": "assistant",
            "MessageText": f"Found {len(cited_cases)} matching case(s). See cited CaseMasterIDs.",
            "GeneratedSQL": "SELECT * FROM CaseMaster WHERE 1=1 LIMIT 3",  # placeholder, not schema-decoder output
            "ConfidenceScore": round(random.uniform(0.55, 0.98), 2),
            "CitedCaseMasterIDs": cited_ids,
            "CreatedAt": (started + datetime.timedelta(seconds=random.randint(1, 20))).isoformat(sep=" "),
        })
    write_csv(rows, "ConversationMessage")
    return rows


def generate_audit_log(
    app_user_rows: list[dict[str, Any]],
    app_user_rowid_map: dict[int, int],
    count: int = 200,
) -> list[dict[str, Any]]:
    ids = id_sequence(1)
    rows = []
    for _ in range(count):
        user = random.choice(app_user_rows)
        ts = datetime.datetime.now().replace(microsecond=0) - datetime.timedelta(days=random.randint(0, 365))
        rows.append({
            "AuditLogID": next(ids),
            "AppUserID_FK": app_user_rowid_map[user["AppUserID"]],
            "QueryText": random.choice(SAMPLE_QUESTIONS).format(district="Bengaluru Urban"),
            "GeneratedSQL": "SELECT * FROM CaseMaster WHERE 1=1 LIMIT 3",
            "Timestamp": ts.isoformat(sep=" "),
            "ResultRowCount": random.randint(0, 50),
        })
    # Built as "Time_stamp" — schema.md naming drift.
    write_csv(rows, "AuditLog", column_rename={"Timestamp": "Time_stamp"})
    return rows


def generate_risk_scores(
    accused_rows: list[dict[str, Any]],
    accused_rowid_map: dict[int, int],
    sample_rate: float = 0.3,
) -> list[dict[str, Any]]:
    ids = id_sequence(1)
    rows = []
    for accused in accused_rows:
        if random.random() > sample_rate:
            continue
        top_features = {"prior_arrests": round(random.uniform(0, 1), 2),
                         "case_gravity": round(random.uniform(0, 1), 2),
                         "recency_days": round(random.uniform(0, 1), 2)}
        rows.append({
            "RiskScoreID": next(ids),
            "AccusedMasterID_FK": accused_rowid_map[accused["AccusedMasterID"]],
            "RiskScoreValue": round(random.uniform(0, 1), 3),
            "ComputedDate": datetime.date.today().isoformat(),
            "ModelVersion": "placeholder-v0",
            "TopFeaturesJSON": json.dumps(top_features),
            "CounterfactualJSON": json.dumps({"note": "placeholder shape, not real SHAP output"}),
        })
    write_csv(rows, "RiskScore")
    return rows


def generate_evidence(
    case_master_rows: list[dict[str, Any]],
    case_master_rowid_map: dict[int, int],
    evidence_rate: float = 0.15,
) -> list[dict[str, Any]]:
    ids = id_sequence(1)
    rows = []
    for case in case_master_rows:
        if random.random() > evidence_rate:
            continue
        for _ in range(random.randint(1, 2)):
            evidence_id = next(ids)
            ev_type = random.choice(EVIDENCE_TYPES)
            if ev_type == "image":
                file_path = generate_placeholder_image(evidence_id, case["CrimeNo"])
            elif ev_type == "audio":
                file_path = generate_placeholder_audio(evidence_id)
            else:
                file_path = ""  # document evidence: metadata-only row, no binary generated
            uploaded = datetime.date.fromisoformat(case["CrimeRegisteredDate"]) + datetime.timedelta(days=random.randint(0, 30))
            rows.append({
                "EvidenceID": evidence_id,
                "CaseMasterID_FK": case_master_rowid_map[case["CaseMasterID"]],
                "EvidenceType": ev_type,
                "FileURL": file_path,  # local path placeholder; TODO Stratus upload, see evidence.py
                "Description": f"Synthetic {ev_type} evidence placeholder for {case['CrimeNo']}",
                "UploadedDate": uploaded.isoformat() + " 00:00:00",
            })
    write_csv(rows, "Evidence")
    return rows
