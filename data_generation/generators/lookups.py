"""Master/lookup data: State, District, Unit hierarchy, Employee, Act/Section
(IPC+BNS), CrimeHead/CrimeSubHead, and the remaining small reference tables.

Karnataka's 31 real districts are used for State/District so downstream
geography (Unit, Court, ArrestSurrender state/district) is grounded in real
places. Police-station-level Unit names are structurally plausible
(synthetic), not real KSP station names/addresses.

IPC->BNS section cross-references for headline offences are the
well-publicized substitutions from the BNS 2023 rollout (murder 302->103(1),
theft 379->303(2), etc). Flagged here as PUBLIC-BUT-UNVERIFIED: cross-check
against the official BNS gazette text before this dataset is used for
anything beyond a demo. Non-headline sections get placeholder BNS numbers
in the same block range — clearly synthetic, not claimed as real mappings.

Every generate_* function returns `list[dict]` (the table's rows, named IDs
only) and also writes the CSV via utils.write_csv. Functions that need a
parent's ROWID take a `{named_id: rowid}` map argument, supplied by
pipeline.py after the parent table has been imported into Catalyst.
"""

from __future__ import annotations

import random
from typing import Any

from data_generation.utils import id_sequence, write_csv

random.seed(42)

KARNATAKA_DISTRICTS = [
    "Bagalkot", "Ballari", "Belagavi", "Bengaluru Rural", "Bengaluru Urban",
    "Bidar", "Chamarajanagar", "Chikballapur", "Chikkamagaluru", "Chitradurga",
    "Dakshina Kannada", "Davanagere", "Dharwad", "Gadag", "Hassan", "Haveri",
    "Kalaburagi", "Kodagu", "Kolar", "Koppal", "Mandya", "Mysuru", "Raichur",
    "Ramanagara", "Shivamogga", "Tumakuru", "Udupi", "Uttara Kannada",
    "Vijayapura", "Yadgir", "Vijayanagara",
]

# (IPC section, BNS section, offence label) — headline offences only, marked
# unverified above. AI-generated is-a mapping, cross-check before real use.
IPC_BNS_HEADLINE = [
    ("302", "103(1)", "Murder"),
    ("304B", "80(2)", "Dowry Death"),
    ("376", "64", "Rape"),
    ("363", "137(2)", "Kidnapping"),
    ("379", "303(2)", "Theft"),
    ("380", "305", "Theft in dwelling house"),
    ("392", "309(4)", "Robbery"),
    ("395", "310(2)", "Dacoity"),
    ("406", "316(2)", "Criminal breach of trust"),
    ("420", "318(4)", "Cheating"),
    ("447", "329(3)", "Criminal trespass"),
    ("498A", "85", "Cruelty by husband/relatives"),
    ("506", "351(2)", "Criminal intimidation"),
    ("509", "79", "Insult to modesty of woman"),
    ("147", "191(2)", "Rioting"),
    ("148", "191(3)", "Rioting, armed with weapon"),
    ("149", "190", "Unlawful assembly, common object"),
    ("120B", "61(2)", "Criminal conspiracy"),
    ("34", "3(5)", "Common intention"),
    ("354", "74", "Assault on woman with intent to outrage modesty"),
]

RANKS = ["Constable", "Head Constable", "ASI", "SI", "PSI", "Inspector",
         "DySP", "SP", "DIG", "IG", "ADGP"]
DESIGNATIONS = ["Investigating Officer", "Station House Officer",
                "Circle Inspector", "Sub-Divisional Officer",
                "District Superintendent", "Range DIG"]
UNIT_TYPES = [("State HQ", 1), ("Range", 2), ("District", 3),
              ("Sub-Division", 4), ("Police Station", 5), ("Traffic PS", 5)]
CASE_CATEGORIES = ["FIR", "UDR", "PAR", "NCR", "MVC"]
GRAVITY = ["Heinous", "Non-Heinous"]
CASE_STATUSES = ["Under Investigation", "Charge Sheeted", "Closed",
                  "Final Report - B", "Final Report - C"]
CASTES = ["General", "OBC", "SC", "ST", "Category-1", "Category-2A",
          "Category-2B", "Category-3A", "Category-3B"]
RELIGIONS = ["Hindu", "Muslim", "Christian", "Sikh", "Buddhist", "Jain",
             "Other"]
OCCUPATIONS = ["Unemployed", "Student", "Agriculture", "Daily Wage Labour",
               "Private Sector", "Government Service", "Business",
               "Homemaker", "Self-Employed", "Retired"]
CRIME_HEADS = ["Crime Against Body", "Crime Against Property",
               "Crime Against Women", "Crime Against Children",
               "Economic Offences", "Cyber Crime", "Special & Local Laws"]
CRIME_SUBHEADS = {
    "Crime Against Body": ["Murder", "Attempt to Murder", "Grievous Hurt", "Kidnapping"],
    "Crime Against Property": ["Theft", "Robbery", "Dacoity", "Burglary", "Criminal Trespass"],
    "Crime Against Women": ["Rape", "Dowry Death", "Cruelty by Husband", "Molestation"],
    "Crime Against Children": ["POCSO Offences", "Child Kidnapping", "Child Labour"],
    "Economic Offences": ["Cheating", "Criminal Breach of Trust", "Forgery"],
    "Cyber Crime": ["Online Fraud", "Identity Theft", "Cyberstalking"],
    "Special & Local Laws": ["NDPS", "Arms Act", "Excise Act"],
}


def generate_states() -> list[dict[str, Any]]:
    rows = [{"StateID": 1, "StateName": "Karnataka", "NationalityID": 1, "Active": True}]
    write_csv(rows, "State")
    return rows


def generate_districts(state_rowid_map: dict[int, int]) -> list[dict[str, Any]]:
    ids = id_sequence(1)
    rows = [
        {"DistrictID": next(ids), "DistrictName": name,
         "StateID_FK": state_rowid_map[1], "Active": True}
        for name in KARNATAKA_DISTRICTS
    ]
    write_csv(rows, "District")
    return rows


def generate_unit_types() -> list[dict[str, Any]]:
    ids = id_sequence(1)
    rows = [
        {"UnitTypeID": next(ids), "UnitTypeName": name, "CityDistState": "District",
         "Hierarchy": hierarchy, "Active": True}
        for name, hierarchy in UNIT_TYPES
    ]
    write_csv(rows, "UnitType")
    return rows


def generate_units(
    unittype_rowid_map: dict[int, int],
    state_rowid_map: dict[int, int],
    district_rows: list[dict[str, Any]],
    district_rowid_map: dict[int, int],
    stations_per_district: int = 4,
) -> list[dict[str, Any]]:
    """Police-station-level Unit rows nested under each District.

    UnitTypeID 5 = "Police Station" per UNIT_TYPES above. ParentUnit is left
    unset here (self-FK resolved in a second pass by pipeline.py once this
    table's own ROWIDs are known — Unit is the one table that's its own
    parent, so it needs an extra import->fetch-ROWID->update round-trip).
    """
    ids = id_sequence(1)
    station_type_rowid = unittype_rowid_map[5]
    rows = []
    for d in district_rows:
        dist_name = d["DistrictName"]
        dist_rowid = district_rowid_map[d["DistrictID"]]
        for i in range(1, stations_per_district + 1):
            rows.append({
                "UnitID": next(ids),
                "UnitName": f"{dist_name} PS-{i}",
                "TypeID_FK": station_type_rowid,
                "ParentUnit": "",
                "NationalityID": 1,
                "StateID_FK": state_rowid_map[1],
                "DistrictID_FK": dist_rowid,
                "Active": True,
            })
    write_csv(rows, "Unit")
    return rows


def generate_ranks() -> list[dict[str, Any]]:
    ids = id_sequence(1)
    rows = [{"RankID": next(ids), "RankName": r, "Hierarchy": i, "Active": True}
            for i, r in enumerate(RANKS, start=1)]
    write_csv(rows, "Rank")
    return rows


def generate_designations() -> list[dict[str, Any]]:
    ids = id_sequence(1)
    rows = [{"DesignationID": next(ids), "DesignationName": d, "Active": True, "SortOrder": i}
            for i, d in enumerate(DESIGNATIONS, start=1)]
    # Built as "DesigationName" — schema.md naming drift.
    write_csv(rows, "Designation", column_rename={"DesignationName": "DesigationName"})
    return rows


def generate_employees(
    district_rows: list[dict[str, Any]],
    district_rowid_map: dict[int, int],
    unit_rows: list[dict[str, Any]],
    unit_rowid_map: dict[int, int],
    rank_rowid_map: dict[int, int],
    designation_rowid_map: dict[int, int],
    count: int = 300,
) -> list[dict[str, Any]]:
    ids = id_sequence(1)
    first_names = ["Arjun", "Deepa", "Suresh", "Lakshmi", "Manjunath", "Kavya",
                   "Ravindra", "Anitha", "Prakash", "Sowmya", "Naveen", "Divya"]
    rows = []
    for _ in range(count):
        unit = random.choice(unit_rows)
        district_named_id = next(
            d["DistrictID"] for d in district_rows
            if district_rowid_map[d["DistrictID"]] == unit["DistrictID_FK"]
        )
        rank_named_id = random.randint(1, len(RANKS))
        designation_named_id = random.randint(1, len(DESIGNATIONS))
        rows.append({
            "EmployeeID": next(ids),
            "DistrictID_FK": district_rowid_map[district_named_id],
            "UnitID_FK": unit_rowid_map[unit["UnitID"]],
            "RankID_FK": rank_rowid_map[rank_named_id],
            "DesignationID_FK": designation_rowid_map[designation_named_id],
            "KGID": f"KGID{100000 + next(ids)}",
            "FirstName": random.choice(first_names),
            "EmployeeDOB": _random_dob(22, 58),
            "GenderID": random.choice([1, 2]),
            "BloodGroupID": random.randint(1, 8),
            "PhysicallyChallenged": random.random() < 0.02,
            "AppointmentDate": _random_dob(1, 30),
        })
    write_csv(rows, "Employee")
    return rows


def generate_case_category() -> list[dict[str, Any]]:
    ids = id_sequence(1)
    rows = [{"CaseCategoryID": next(ids), "LookupValue": v} for v in CASE_CATEGORIES]
    write_csv(rows, "CaseCategory")
    return rows


def generate_gravity_offence() -> list[dict[str, Any]]:
    ids = id_sequence(1)
    rows = [{"GravityOffenceID": next(ids), "LookupValue": v} for v in GRAVITY]
    # Built as "GravityOffence" (same name as the table) — schema.md naming drift.
    write_csv(rows, "GravityOffence", column_rename={"GravityOffenceID": "GravityOffence"})
    return rows


def generate_crime_head() -> list[dict[str, Any]]:
    ids = id_sequence(1)
    rows = [{"CrimeHeadID": next(ids), "CrimeGroupName": v, "Active": True} for v in CRIME_HEADS]
    write_csv(rows, "CrimeHead")
    return rows


def generate_crime_subhead(
    crimehead_rows: list[dict[str, Any]], crimehead_rowid_map: dict[int, int]
) -> list[dict[str, Any]]:
    ids = id_sequence(1)
    rows = []
    for ch in crimehead_rows:
        subheads = CRIME_SUBHEADS[ch["CrimeGroupName"]]
        for seq, name in enumerate(subheads, start=1):
            rows.append({
                "CrimeSubHeadID": next(ids),
                "CrimeHeadID_FK": crimehead_rowid_map[ch["CrimeHeadID"]],
                "CrimeHeadName": name,
                "SeqID": seq,
            })
    write_csv(rows, "CrimeSubHead")
    return rows


def generate_act() -> list[dict[str, Any]]:
    rows = [
        {"ActCode": "IPC", "ActDescription": "Indian Penal Code, 1860",
         "ShortName": "IPC", "Active": True},
        {"ActCode": "BNS", "ActDescription": "Bharatiya Nyaya Sanhita, 2023",
         "ShortName": "BNS", "Active": True},
    ]
    write_csv(rows, "Act")
    return rows


def generate_section(act_rowid_map: dict[str, int]) -> list[dict[str, Any]]:
    """ActCode is the named PK per ddl_reference.md (no separate ActID)."""
    rows = []
    for ipc_sec, bns_sec, label in IPC_BNS_HEADLINE:
        rows.append({"ActCode_FK": act_rowid_map["IPC"], "SectionCode": ipc_sec,
                      "SectionDescription": label, "Active": True})
        rows.append({"ActCode_FK": act_rowid_map["BNS"], "SectionCode": bns_sec,
                      "SectionDescription": label, "Active": True})
    write_csv(rows, "Section")
    return rows


def generate_crimehead_act_section(
    crimehead_rows: list[dict[str, Any]],
    crimehead_rowid_map: dict[int, int],
    act_rowid_map: dict[str, int],
    section_rows: list[dict[str, Any]],
    section_rowid_map: dict[tuple[int, str], int],
) -> list[dict[str, Any]]:
    """Loose crime-head -> act/section linkage for query-time joins.

    Every headline section is linked to "Crime Against Body" or "Crime
    Against Property" heads heuristically by offence label; good enough for
    demo-scale realism, not a legally authoritative crosswalk.
    """
    body_head_id = next(c["CrimeHeadID"] for c in crimehead_rows
                         if c["CrimeGroupName"] == "Crime Against Body")
    property_head_id = next(c["CrimeHeadID"] for c in crimehead_rows
                             if c["CrimeGroupName"] == "Crime Against Property")
    property_labels = {"Theft in dwelling house", "Theft", "Robbery", "Dacoity",
                        "Criminal breach of trust", "Cheating", "Criminal trespass"}
    rows = []
    for sec in section_rows:
        head_id = property_head_id if sec["SectionDescription"] in property_labels else body_head_id
        rows.append({
            "CrimeHeadID_FK": crimehead_rowid_map[head_id],
            "ActCode_FK": sec["ActCode_FK"],
            "SectionCode_FK": section_rowid_map[(sec["ActCode_FK"], sec["SectionCode"])],
        })
    write_csv(rows, "CrimeHeadActSection")
    return rows


def generate_case_status() -> list[dict[str, Any]]:
    ids = id_sequence(1)
    rows = [{"CaseStatusID": next(ids), "CaseStatusName": v} for v in CASE_STATUSES]
    write_csv(rows, "CaseStatusMaster")
    return rows


def generate_court(
    district_rows: list[dict[str, Any]],
    district_rowid_map: dict[int, int],
    state_rowid_map: dict[int, int],
) -> list[dict[str, Any]]:
    ids = id_sequence(1)
    rows = []
    for d in district_rows:
        rows.append({
            "CourtID": next(ids),
            "CourtName": f"District & Sessions Court, {d['DistrictName']}",
            "DistrictID_FK": district_rowid_map[d["DistrictID"]],
            "StateID_FK": state_rowid_map[1],
            "Active": True,
        })
    # Built as "Acitve" — schema.md naming drift.
    write_csv(rows, "Court", column_rename={"Active": "Acitve"})
    return rows


def generate_caste_master() -> list[dict[str, Any]]:
    ids = id_sequence(1)
    rows = [{"caste_master_id": next(ids), "caste_master_name": v} for v in CASTES]
    write_csv(rows, "CasteMaster")
    return rows


def generate_religion_master() -> list[dict[str, Any]]:
    ids = id_sequence(1)
    rows = [{"ReligionID": next(ids), "ReligionName": v} for v in RELIGIONS]
    write_csv(rows, "ReligionMaster")
    return rows


def generate_occupation_master() -> list[dict[str, Any]]:
    ids = id_sequence(1)
    rows = [{"OccupationID": next(ids), "OccupationName": v} for v in OCCUPATIONS]
    # Built as "OccupationMater" — schema.md naming drift.
    write_csv(rows, "OccupationMaster", column_rename={"OccupationName": "OccupationMater"})
    return rows


def _random_dob(min_years_ago: int, max_years_ago: int) -> str:
    import datetime
    years_ago = random.randint(min_years_ago, max_years_ago)
    days_jitter = random.randint(0, 364)
    dob = datetime.date.today() - datetime.timedelta(days=years_ago * 365 + days_jitter)
    return dob.isoformat()
