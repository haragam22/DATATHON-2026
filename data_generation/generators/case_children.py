"""CaseMaster's child/junction tables: ComplainantDetails, Victim, Accused,
ActSectionAssociation, ArrestSurrender, inv_arrestsurrenderaccused,
ChargesheetDetails.

Consistency rules enforced here:
- ActSectionAssociation picks Act=IPC if CrimeRegisteredDate < 2024-07-01
  else BNS (ddl_reference.md #13's query-time rule, held at generation time
  too so the dual-legal-code demo is coherent out of the box).
- Accused.PersonID is a per-case sequential label (A1, A2, ...), not global.
- ComplainantDetails.CasteID/ReligionID sampled independently of crime
  outcome (CLAUDE.md hard constraint) — uniform random, never conditioned
  on CrimeSubHeadID/GravityOffenceID.
- ArrestSurrender.AccusedMasterID_FK always references an Accused row from
  the SAME CaseMasterID (built from the same case's accused list, never
  cross-case).
- Age sampling stays within validate.py's [7, 100] bound.
- Accused for "network" cases (per case_master.py's case_plans, see
  narratives.py) draw from a shared, small persona pool instead of minting
  a fresh one-off name every time — the same persona's Name/AgeYear/
  GenderID deliberately recurs across several CaseMasterIDs so Phase 9's
  graph layer has real repeat-offender/gang edges to find via
  inv_arrestsurrenderaccused, not an all-strangers dataset.
"""

from __future__ import annotations

import datetime
import random
from typing import Any

from data_generation.generators import narratives
from data_generation.utils import id_sequence, write_csv

random.seed(44)

PERSONA_POOL_SIZE = 120  # smaller pool -> more within-gang reuse per case, see narratives.py

BNS_CUTOVER = datetime.date(2024, 7, 1)


def _random_name() -> str:
    return narratives.random_full_name(random)


def generate_complainants(
    case_master_rows: list[dict[str, Any]],
    case_master_rowid_map: dict[int, int],
    occupation_rows: list[dict[str, Any]],
    occupation_rowid_map: dict[int, int],
    religion_rows: list[dict[str, Any]],
    religion_rowid_map: dict[int, int],
    caste_rows: list[dict[str, Any]],
    caste_rowid_map: dict[int, int],
) -> list[dict[str, Any]]:
    ids = id_sequence(1)
    rows = []
    for case in case_master_rows:
        occ = random.choice(occupation_rows)
        rel = random.choice(religion_rows)
        caste = random.choice(caste_rows)  # independent of crime outcome, see docstring
        rows.append({
            "ComplainantID": next(ids),
            "CaseMasterID_FK": case_master_rowid_map[case["CaseMasterID"]],
            "ComplainantName": _random_name(),
            "AgeYear": random.randint(18, 75),
            "OccupationID_FK": occupation_rowid_map[occ["OccupationID"]],
            "ReligionID_FK": religion_rowid_map[rel["ReligionID"]],
            "CasteID_FK": caste_rowid_map[caste["caste_master_id"]],
            "GenderID": random.choice([1, 2]),
        })
    write_csv(rows, "ComplainantDetails")
    return rows


def generate_victims(
    case_master_rows: list[dict[str, Any]],
    case_master_rowid_map: dict[int, int],
) -> list[dict[str, Any]]:
    ids = id_sequence(1)
    rows = []
    for case in case_master_rows:
        for _ in range(random.randint(1, 3)):
            rows.append({
                "VictimMasterID": next(ids),
                "CaseMasterID_FK": case_master_rowid_map[case["CaseMasterID"]],
                "VictimName": _random_name(),
                "AgeYear": random.randint(7, 90),
                "GenderID": random.choice([1, 2]),
                "VictimPolice": random.random() < 0.03,
            })
    write_csv(rows, "Victim")
    return rows


def generate_accused(
    case_master_rows: list[dict[str, Any]],
    case_master_rowid_map: dict[int, int],
    case_plans: dict[int, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[int, list[dict[str, Any]]], dict[int, str]]:
    """Returns (rows, accused_by_case_master_id, gang_role_by_accused_id).

    Network cases (case_plans[...]["is_network"]) draw AccusedName/AgeYear/
    GenderID from the shared persona pool so the same identity recurs
    across cases — see module docstring. gang_role_by_accused_id (keyed by
    the named AccusedMasterID, not written to the Accused CSV — Accused has
    no gang column in schema) feeds inv_arrestsurrenderaccused's
    RoleInEvent for network cases."""
    ids = id_sequence(1)
    rows = []
    by_case: dict[int, list[dict[str, Any]]] = {}
    gang_role_by_accused_id: dict[int, str] = {}
    persona_pool = narratives.get_persona_pool(PERSONA_POOL_SIZE, random)

    for case in case_master_rows:
        plan = case_plans[case["CaseMasterID"]]
        accused_count = plan["accused_count"]
        case_accused = []

        if plan["is_network"]:
            gang_personas = [p for p in persona_pool if p["GangName"] == plan["gang_name"]]
            pool = gang_personas or persona_pool
            # sample WITHOUT replacement within a case — the same persona
            # can't be two different accused (A1, A2, ...) in one case.
            chosen_personas = random.sample(pool, k=min(accused_count, len(pool)))
        else:
            chosen_personas = [None] * accused_count

        for i, persona in enumerate(chosen_personas, start=1):
            accused_id = next(ids)
            if persona is not None:
                name, age, gender = persona["Name"], persona["BaseAge"], persona["GenderID"]
                gang_role_by_accused_id[accused_id] = persona["GangRole"]
            else:
                name, age, gender = _random_name(), random.randint(14, 80), random.choice([1, 2])

            row = {
                "AccusedMasterID": accused_id,
                "CaseMasterID_FK": case_master_rowid_map[case["CaseMasterID"]],
                "AccusedName": name,
                "AgeYear": age,
                "GenderID": gender,
                "PersonID": f"A{i}",
            }
            rows.append(row)
            case_accused.append(row)
        by_case[case["CaseMasterID"]] = case_accused

    write_csv(rows, "Accused")
    return rows, by_case, gang_role_by_accused_id


def generate_act_section_association(
    case_master_rows: list[dict[str, Any]],
    case_master_rowid_map: dict[int, int],
    act_rowid_map: dict[str, int],
    section_rows: list[dict[str, Any]],
    section_rowid_map: dict[tuple[int, str], int],
) -> list[dict[str, Any]]:
    sections_by_act: dict[str, list[dict[str, Any]]] = {"IPC": [], "BNS": []}
    for sec in section_rows:
        for code, rowid in act_rowid_map.items():
            if sec["ActCode_FK"] == rowid:
                sections_by_act[code].append(sec)

    rows = []
    for case in case_master_rows:
        registered = datetime.date.fromisoformat(case["CrimeRegisteredDate"])
        act_code = "IPC" if registered < BNS_CUTOVER else "BNS"
        candidates = sections_by_act[act_code]
        chosen = random.sample(candidates, k=min(random.randint(1, 3), len(candidates)))
        for order, sec in enumerate(chosen, start=1):
            rows.append({
                "CaseMasterID_FK": case_master_rowid_map[case["CaseMasterID"]],
                "ActID_FK": act_rowid_map[act_code],
                "SectionID_FK": section_rowid_map[(sec["ActCode_FK"], sec["SectionCode"])],
                "ActOrderID": 1,
                "SectionOrderID": order,
            })
    write_csv(rows, "ActSectionAssociation")
    return rows


def generate_arrest_surrender(
    case_master_rows: list[dict[str, Any]],
    case_master_rowid_map: dict[int, int],
    accused_by_case_master_id: dict[int, list[dict[str, Any]]],
    accused_rowid_map: dict[int, int],
    state_rowid_map: dict[int, int],
    unit_rowid_to_district_rowid: dict[int, int],
    employee_rows: list[dict[str, Any]],
    employee_rowid_map: dict[int, int],
    court_rows: list[dict[str, Any]],
    court_rowid_map: dict[int, int],
    arrest_rate: float = 0.6,
) -> tuple[list[dict[str, Any]], dict[int, int]]:
    """Returns (rows, named_id -> row_index-position) so pipeline.py can
    build the ArrestSurrender ROWID map after import for the junction
    table below."""
    ids = id_sequence(1)
    rows = []
    for case in case_master_rows:
        registered = datetime.date.fromisoformat(case["CrimeRegisteredDate"])
        for accused in accused_by_case_master_id.get(case["CaseMasterID"], []):
            if random.random() > arrest_rate:
                continue
            employee = random.choice(employee_rows)
            court = random.choice(court_rows)
            arrest_date = registered + datetime.timedelta(days=random.randint(0, 90))
            rows.append({
                "ArrestSurrenderID": next(ids),
                "CaseMasterID_FK": case_master_rowid_map[case["CaseMasterID"]],
                "ArrestSurrenderTypeID": random.choice([1, 2]),  # 1=Arrest, 2=Surrender
                "ArrestSurrenderDate": arrest_date.isoformat(),
                "ArrestSurrenderStateId_FK": state_rowid_map[1],
                "ArrestSurrenderDistrictId_FK": unit_rowid_to_district_rowid[case["PoliceStationID_FK"]],
                "PoliceStationID_FK": case["PoliceStationID_FK"],
                "IOID_FK": employee_rowid_map[employee["EmployeeID"]],
                "CourtID_FK": court_rowid_map[court["CourtID"]],
                "AccusedMasterID_FK": accused_rowid_map[accused["AccusedMasterID"]],
                "IsAccused": True,
                "IsComplainantAccused": random.random() < 0.05,
            })
    write_csv(rows, "ArrestSurrender")
    return rows, {}


def generate_arrest_surrender_accused(
    arrest_surrender_rows: list[dict[str, Any]],
    arrest_surrender_rowid_map: dict[int, int],
    gang_role_by_accused_rowid: dict[int, str] | None = None,
) -> list[dict[str, Any]]:
    """1:1 by construction (one ArrestSurrender row already targets one
    Accused), materialized as the explicit junction table the graph layer
    (Phase 9) reads. RoleInEvent carries the persona's gang role
    (Leader/Lieutenant -> "Primary", Member/Associate -> "Associate") for
    network-case accused, so the graph has meaningful role differentiation
    instead of every node saying "Primary"."""
    gang_role_by_accused_rowid = gang_role_by_accused_rowid or {}
    ids = id_sequence(1)
    rows = []
    for arrest in arrest_surrender_rows:
        gang_role = gang_role_by_accused_rowid.get(arrest["AccusedMasterID_FK"])
        role_in_event = "Primary" if gang_role in (None, "Leader", "Lieutenant") else "Associate"
        rows.append({
            "ArrestSurrenderAccusedID": next(ids),
            "ArrestSurrenderID_FK": arrest_surrender_rowid_map[arrest["ArrestSurrenderID"]],
            "AccusedMasterID_FK": arrest["AccusedMasterID_FK"],
            "RoleInEvent": role_in_event,
            "CreatedDate": arrest["ArrestSurrenderDate"] + " 00:00:00",
        })
    write_csv(rows, "inv_arrestsurrenderaccused")
    return rows


def generate_chargesheet_details(
    case_master_rows: list[dict[str, Any]],
    case_master_rowid_map: dict[int, int],
    case_status_rowid_map: dict[int, int],
    charge_sheeted_status_named_id: int,
    employee_rows: list[dict[str, Any]],
    employee_rowid_map: dict[int, int],
) -> list[dict[str, Any]]:
    ids = id_sequence(1)
    charge_sheeted_rowid = case_status_rowid_map[charge_sheeted_status_named_id]
    rows = []
    for case in case_master_rows:
        if case["CaseStatusID_FK"] != charge_sheeted_rowid:
            continue
        registered = datetime.date.fromisoformat(case["CrimeRegisteredDate"])
        cs_date = registered + datetime.timedelta(days=random.randint(30, 180))
        employee = random.choice(employee_rows)
        rows.append({
            "CSID": next(ids),
            "CaseMasterID_FK": case_master_rowid_map[case["CaseMasterID"]],
            "csdate": cs_date.isoformat() + " 00:00:00",
            "cstype": random.choice(["A", "B", "C"]),
            "PolicePersonID_FK": employee_rowid_map[employee["EmployeeID"]],
        })
    write_csv(rows, "ChargesheetDetails")
    return rows
