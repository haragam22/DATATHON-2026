"""Phase 15 prep: builds the labeled synthetic offender feature set Zia
AutoML needs as training data. Reads real Accused/ArrestSurrender/CaseMaster
rows from Catalyst Data Store (raw REST, same pattern as
paraphrase_existing_briefs.py), computes per-accused-row features, and
writes a CSV to upload via the console's QuickML/AutoML dataset import.

Label is a DOCUMENTED HEURISTIC, not real ground truth (CLAUDE.md: never
claim synthetic content has real predictive validity — same honesty
standard as app_layer.py's existing placeholder RiskScore seed data, just
built from real derived signal instead of pure random.uniform()):
  risk_label = 1 if (prior_case_count >= 2) or (arrest_count >= 2) or
               (max_gravity_rank indicates a Heinous-class case),
               with a 10% random label flip so the target isn't a pure
               deterministic function of the features (forces AutoML to
               actually learn a boundary instead of memorizing an
               if/else).

Output columns: AccusedMasterID (keep for join-back, exclude from model
features when configuring the AutoML pipeline), AgeYear, GenderID,
prior_case_count, arrest_count, primary_role_count, max_gravity_rank,
risk_label.

Run: python -m data_generation.build_risk_training_set
"""

from __future__ import annotations

import csv
import os
import random
import time

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "streamlit_harness", ".env"))

ACCOUNTS_URL = "https://accounts.zoho.in/oauth/v2/token"
QUERY_URL = f"https://api.catalyst.zoho.in/baas/v1/project/{os.environ['CATALYST_PROJECT_ID']}/query"
OUT_PATH = os.path.join(os.path.dirname(__file__), "csv_out", "RiskTrainingSet.csv")

random.seed(43)

_token_cache = {"access_token": "", "expires_at": 0.0}


def _with_retry(fn, attempts: int = 5, base_delay: float = 5.0):
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except (requests.exceptions.RequestException, RuntimeError) as e:
            last_error = e
            if attempt < attempts:
                delay = base_delay * (2 ** (attempt - 1))
                print(f"[build_risk_training_set] transient error (attempt {attempt}/{attempts}): {e} — retrying in {delay:.0f}s", flush=True)
                time.sleep(delay)
    raise last_error


def _access_token() -> str:
    if time.time() < _token_cache["expires_at"]:
        return _token_cache["access_token"]

    def _do_refresh():
        resp = requests.post(ACCOUNTS_URL, data={
            "refresh_token": os.environ["CATALYST_REFRESH_TOKEN"],
            "client_id": os.environ["CATALYST_CLIENT_ID"],
            "client_secret": os.environ["CATALYST_CLIENT_SECRET"],
            "grant_type": "refresh_token",
        }, timeout=30)
        resp.raise_for_status()
        return resp.json()

    body = _with_retry(_do_refresh)
    _token_cache["access_token"] = body["access_token"]
    _token_cache["expires_at"] = time.time() + body.get("expires_in", 3600) - 60
    return body["access_token"]


def zcql(query: str) -> list[dict]:
    def _do_query():
        resp = requests.post(
            QUERY_URL, json={"query": query},
            headers={
                "Authorization": f"Zoho-oauthtoken {_access_token()}",
                "CATALYST-ORG": os.environ["CATALYST_ORG_ID"],
                "Environment": os.environ["CATALYST_ENVIRONMENT"],
                "Content-Type": "application/json",
            },
            timeout=60,
        )
        body = resp.json()
        if body.get("status") != "success":
            raise RuntimeError(f"ZCQL failed: {body}")
        return body["data"]

    data = _with_retry(_do_query)
    return [next(iter(row.values())) for row in data]


def _fetch_all(table: str, columns: str) -> list[dict]:
    rows: list[dict] = []
    last_rowid = 0
    while True:
        batch = zcql(f"SELECT ROWID, {columns} FROM {table} WHERE ROWID > {last_rowid} ORDER BY ROWID ASC LIMIT 200")
        if not batch:
            break
        rows.extend(batch)
        last_rowid = int(batch[-1]["ROWID"])
    return rows


# GravityOffence's LookupValue text -> a numeric severity rank for the
# max_gravity_rank feature. Values match lookups.py's generated set.
_GRAVITY_RANK = {"Non-Heinous": 0, "Heinous": 1}


def main() -> None:
    print("[build_risk_training_set] fetching Accused...", flush=True)
    accused = _fetch_all("Accused", "AccusedMasterID, AccusedName, AgeYear, GenderID, CaseMasterID_FK")

    print("[build_risk_training_set] fetching ArrestSurrender...", flush=True)
    arrests = _fetch_all("ArrestSurrender", "AccusedMasterID_FK")
    arrested_accused_rowids = {int(r["AccusedMasterID_FK"]) for r in arrests}

    print("[build_risk_training_set] fetching inv_arrestsurrenderaccused (primary-role flags)...", flush=True)
    links = _fetch_all("inv_arrestsurrenderaccused", "AccusedMasterID_FK, RoleInEvent")
    primary_by_accused_rowid: dict[int, int] = {}
    for link in links:
        rowid = int(link["AccusedMasterID_FK"])
        primary_by_accused_rowid[rowid] = primary_by_accused_rowid.get(rowid, 0) + (
            1 if link["RoleInEvent"] == "Primary" else 0
        )

    print("[build_risk_training_set] fetching CaseMaster gravity...", flush=True)
    cases = _fetch_all("CaseMaster", "CseMasterID, GravityOffenceID")
    case_rowid_to_gravity_fk = {int(c["ROWID"]): int(c["GravityOffenceID"]) for c in cases}
    gravity_lookup = _fetch_all("GravityOffence", "LookupValue")
    gravity_rowid_to_rank = {int(g["ROWID"]): _GRAVITY_RANK.get(g["LookupValue"], 0) for g in gravity_lookup}

    # Identity groups (recidivism match, same convention as network.py/entity_context.py).
    identity_groups: dict[tuple[str, int, int], list[dict]] = {}
    for a in accused:
        key = (a["AccusedName"], int(a["AgeYear"]), int(a["GenderID"]))
        identity_groups.setdefault(key, []).append(a)

    rows_out = []
    for identity_rows in identity_groups.values():
        case_rowids = {int(a["CaseMasterID_FK"]) for a in identity_rows}
        prior_case_count = len(case_rowids)
        arrest_count = sum(1 for a in identity_rows if int(a["ROWID"]) in arrested_accused_rowids)
        primary_role_count = sum(primary_by_accused_rowid.get(int(a["ROWID"]), 0) for a in identity_rows)
        max_gravity_rank = max(
            (gravity_rowid_to_rank.get(case_rowid_to_gravity_fk.get(cr, -1), 0) for cr in case_rowids),
            default=0,
        )

        base_risk = 1 if (prior_case_count >= 2 or arrest_count >= 2 or max_gravity_rank == 1) else 0
        risk_label = 1 - base_risk if random.random() < 0.10 else base_risk

        for a in identity_rows:
            rows_out.append({
                "AccusedMasterID": a["AccusedMasterID"],
                "AgeYear": a["AgeYear"],
                "GenderID": a["GenderID"],
                "prior_case_count": prior_case_count,
                "arrest_count": arrest_count,
                "primary_role_count": primary_role_count,
                "max_gravity_rank": max_gravity_rank,
                "risk_label": risk_label,
            })

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
        writer.writeheader()
        writer.writerows(rows_out)

    print(f"[build_risk_training_set] wrote {len(rows_out)} rows to {OUT_PATH}", flush=True)
    print(f"[build_risk_training_set] risk_label distribution: "
          f"{sum(1 for r in rows_out if r['risk_label'] == 1)} high-risk, "
          f"{sum(1 for r in rows_out if r['risk_label'] == 0)} low-risk", flush=True)


if __name__ == "__main__":
    main()
