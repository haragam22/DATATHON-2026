"""Whitelist of table/column names the SQL generator and guard are allowed
to reference — built-as names (post naming-drift, see docs/schema.md's
drift table), never the originally-documented names, since that's what's
actually queryable in Catalyst Data Store. Covers Part 1 (KSP-original)
tables relevant to case/accused/victim/arrest questions — the core surface
Phase 5/6 targets. Extend as later phases need more tables (financial,
risk score, evidence) rather than whitelisting everything up front.
"""

from __future__ import annotations

ALLOWED_SCHEMA: dict[str, set[str]] = {
    "CaseMaster": {
        "CseMasterID", "CrimeNo", "CaseNo", "CrimeRegisteredDate",
        "PolicePersonID_FK", "PoliceStationID_FK", "CaseCategoryID_FK",
        "GravityOffenceID", "CrimeMajorHeadID_FK", "CrimeMinorHeadID_FK",
        "CaseStatusID_FK", "CourtID_FK", "IncidentFromDate", "IncidentToDate",
        "InfoRecievedPSDate", "Latitude", "Longitude", "BriefFacts",
    },
    "ComplainantDetails": {
        "ComplainantID", "CaseMasterID_FK", "ComplainantName", "AgeYear",
        "OccupationID_FK", "ReligionID_FK", "CasteID_FK", "GenderID",
    },
    "ActSectionAssociation": {
        "CaseMasterID_FK", "ActID_FK", "SectionID_FK", "ActOrderID", "SectionOrderID",
    },
    "Victim": {
        "VictimMasterID", "CaseMasterID_FK", "VictimName", "AgeYear",
        "GenderID", "VictimPolice",
    },
    "Accused": {
        "AccusedMasterID", "CaseMasterID_FK", "AccusedName", "AgeYear",
        "GenderID", "PersonID",
    },
    "ArrestSurrender": {
        "ArrestSurrenderID", "CaseMasterID_FK", "ArrestSurrenderTypeID",
        "ArrestSurrenderDate", "ArrestSurrenderStateId_FK", "ArrestSurrenderDistrictId_FK",
        "PoliceStationID_FK", "IOID_FK", "CourtID_FK", "AccusedMasterID_FK",
        "IsAccused", "IsComplainantAccused",
    },
    "inv_arrestsurrenderaccused": {
        "ArrestSurrenderAccusedID", "ArrestSurrenderID_FK", "AccusedMasterID_FK",
        "RoleInEvent", "CreatedDate",
    },
    "Act": {"ActCode", "ActDescription", "ShortName", "Active"},
    "Section": {"ActCode_FK", "SectionCode", "SectionDescription", "Active"},
    "CrimeHead": {"CrimeHeadID", "CrimeGroupName", "Active"},
    "CrimeSubHead": {"CrimeSubHeadID", "CrimeHeadID_FK", "CrimeHeadName", "SeqID"},
    "CaseStatusMaster": {"CaseStatusID", "CaseStatusName"},
    "CaseCategory": {"CaseCategoryID", "LookupValue"},
    "GravityOffence": {"GravityOffence", "LookupValue"},
    "Court": {"CourtID", "CourtName", "DistrictID_FK", "StateID_FK", "Acitve"},
    "District": {"DistrictID", "DistrictName", "StateID_FK", "Active"},
    "State": {"StateID", "StateName", "NationalityID", "Active"},
    "Unit": {
        "UnitID", "UnitName", "TypeID_FK", "ParentUnit", "NationalityID",
        "StateID_FK", "DistrictID_FK", "Active",
    },
    "Employee": {
        "EmployeeID", "DistrictID_FK", "UnitID_FK", "RankID_FK", "DesignationID_FK",
        "KGID", "FirstName", "EmployeeDOB", "GenderID", "BloodGroupID",
        "PhysicallyChallenged", "AppointmentDate",
    },
    "Inv_OccuranceTime": {
        "OccuranceTimeID", "CaseMasterID_FK", "DayOfWeek", "TimeOfDayBucket",
        "PlaceOfOccuranceType", "PlaceOfOccuranceDescription", "IsOutdoor",
    },
    "ChargesheetDetails": {
        "CSID", "CaseMasterID_FK", "csdate", "cstype", "PolicePersonID_FK",
    },
    "Account": {
        "AccountID", "AccountHolderName", "BankName", "AccountNumberMasked",
        "AccountType", "Active",
    },
    "Transaction": {
        "TransactionID", "FromAccountID_FK", "ToAccountID_FK", "Amount",
        "TransactionDate", "TransactionType", "Flagged",
    },
    "AccountCaseLink": {
        "LinkID", "CaseMasterID_FK", "AccountID_FK", "RoleInCase",
    },
    "Evidence": {
        "EvidenceID", "CaseMasterID_FK", "EvidenceType", "FileURL",
        "Description", "UploadedDate",
    },
}


def render_schema_for_prompt() -> str:
    """Flat `Table(col1, col2, ...)` listing handed to QuickML as the only
    vocabulary it's allowed to generate SQL against — the schema-constrained
    part of schema-constrained SQL generation (CLAUDE.md: never let SQL gen
    run as unconstrained free-text)."""
    lines = []
    for table, cols in ALLOWED_SCHEMA.items():
        lines.append(f"{table}({', '.join(sorted(cols))})")
    return "\n".join(lines)


# Direct FK edges only — from schema.md's Part 1 relationship matrix.
# ZCQL rejects a JOIN between two tables with no declared relationship
# (confirmed live: "No relationship between tables District and
# CaseMaster" — District only reaches CaseMaster via Unit or Court, no
# direct edge). Every multi-hop question needs the intermediate table
# named explicitly as its own JOIN, never skipped.
FK_EDGES: list[tuple[str, str, str, str]] = [
    ("CaseMaster", "PoliceStationID_FK", "Unit", "UnitID"),
    ("CaseMaster", "CourtID_FK", "Court", "CourtID"),
    ("CaseMaster", "CaseCategoryID_FK", "CaseCategory", "CaseCategoryID"),
    ("CaseMaster", "GravityOffenceID", "GravityOffence", "GravityOffence"),
    ("CaseMaster", "CrimeMajorHeadID_FK", "CrimeHead", "CrimeHeadID"),
    ("CaseMaster", "CrimeMinorHeadID_FK", "CrimeSubHead", "CrimeSubHeadID"),
    ("CaseMaster", "CaseStatusID_FK", "CaseStatusMaster", "CaseStatusID"),
    ("CaseMaster", "PolicePersonID_FK", "Employee", "EmployeeID"),
    ("CrimeSubHead", "CrimeHeadID_FK", "CrimeHead", "CrimeHeadID"),
    ("ComplainantDetails", "CaseMasterID_FK", "CaseMaster", "CseMasterID"),
    ("ComplainantDetails", "OccupationID_FK", "OccupationMaster", "OccupationID"),
    ("ComplainantDetails", "ReligionID_FK", "ReligionMaster", "ReligionID"),
    ("ComplainantDetails", "CasteID_FK", "CasteMaster", "caste_master_id"),
    ("Victim", "CaseMasterID_FK", "CaseMaster", "CseMasterID"),
    ("Accused", "CaseMasterID_FK", "CaseMaster", "CseMasterID"),
    ("ArrestSurrender", "CaseMasterID_FK", "CaseMaster", "CseMasterID"),
    ("ArrestSurrender", "AccusedMasterID_FK", "Accused", "AccusedMasterID"),
    ("ArrestSurrender", "ArrestSurrenderStateId_FK", "State", "StateID"),
    ("ArrestSurrender", "ArrestSurrenderDistrictId_FK", "District", "DistrictID"),
    ("ArrestSurrender", "PoliceStationID_FK", "Unit", "UnitID"),
    ("ArrestSurrender", "IOID_FK", "Employee", "EmployeeID"),
    ("ArrestSurrender", "CourtID_FK", "Court", "CourtID"),
    ("inv_arrestsurrenderaccused", "ArrestSurrenderID_FK", "ArrestSurrender", "ArrestSurrenderID"),
    ("inv_arrestsurrenderaccused", "AccusedMasterID_FK", "Accused", "AccusedMasterID"),
    ("ActSectionAssociation", "CaseMasterID_FK", "CaseMaster", "CseMasterID"),
    ("ActSectionAssociation", "ActID_FK", "Act", "ActCode"),
    ("ActSectionAssociation", "SectionID_FK", "Section", "SectionCode"),
    ("Court", "DistrictID_FK", "District", "DistrictID"),
    ("Court", "StateID_FK", "State", "StateID"),
    ("Unit", "DistrictID_FK", "District", "DistrictID"),
    ("Unit", "StateID_FK", "State", "StateID"),
    ("Employee", "DistrictID_FK", "District", "DistrictID"),
    ("District", "StateID_FK", "State", "StateID"),
    ("ChargesheetDetails", "CaseMasterID_FK", "CaseMaster", "CseMasterID"),
    ("Inv_OccuranceTime", "CaseMasterID_FK", "CaseMaster", "CseMasterID"),
    ("AccountCaseLink", "CaseMasterID_FK", "CaseMaster", "CseMasterID"),
    ("AccountCaseLink", "AccountID_FK", "Account", "AccountID"),
    ("Transaction", "FromAccountID_FK", "Account", "AccountID"),
    ("Transaction", "ToAccountID_FK", "Account", "AccountID"),
    ("Evidence", "CaseMasterID_FK", "CaseMaster", "CseMasterID"),
]

ADJACENT_TABLES: dict[str, set[str]] = {}
for _a, _, _b, _ in FK_EDGES:
    ADJACENT_TABLES.setdefault(_a, set()).add(_b)
    ADJACENT_TABLES.setdefault(_b, set()).add(_a)


def render_relationships_for_prompt() -> str:
    lines = [f"{a}.{ca} -> {b}.{cb}" for a, ca, b, cb in FK_EDGES]
    return "\n".join(lines)
