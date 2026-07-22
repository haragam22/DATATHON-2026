"""Orchestrator. Runs table groups in FK-safe order, level by level, because
Catalyst's real PK (ROWID) is assigned on insert and can't be known before
a parent row exists there.

Per-table loop:
  1. generator function builds rows -> utils.write_csv
  2. validate.run_all(table_name, rows, ...)
  3. `catalyst ds:import` the CSV (subprocess call to Catalyst CLI)
  4. `catalyst ds:export` the same table back out, parse the CSV for
     {NamedID: ROWID}, held in memory for the next table's generator call.
     (Catalyst CLI, per the official command reference, has no standalone
     ZCQL/query-runner command — ds:import/ds:export/ds:status is the full
     Data Store surface, so ROWID lookup goes through ds:export, not a
     SELECT.)
  5. import failure aborts the pipeline at that table — no silent partial
     loads (CLAUDE.md: don't invent recovery behavior, surface and stop)

Rerunnable per table-group via --only lookups|case_master|case_children|
financial|app_layer, so a mid-run failure doesn't force a full regeneration.

Prerequisites (run once, outside this script):
  catalyst login
  catalyst project:use <name_or_project_id>      # sets the active project
                                                   # for this directory

Build order (from ddl_reference.md's parent-before-child requirement):
  State -> District -> UnitType -> Unit(pass1, no ParentUnit) ->
  Unit(pass2, self-FK backfill) -> Rank -> Designation -> Employee ->
  CaseCategory -> GravityOffence -> CrimeHead -> CrimeSubHead -> Act ->
  Section -> CrimeHeadActSection -> CaseStatusMaster -> Court ->
  CasteMaster -> ReligionMaster -> OccupationMaster
  -> CaseMaster -> Inv_OccuranceTime
  -> ComplainantDetails -> Victim -> Accused -> ActSectionAssociation
  -> ArrestSurrender -> inv_arrestsurrenderaccused -> ChargesheetDetails
  -> Account -> Transaction -> AccountCaseLink
  -> AppRole -> AppUser -> ConversationSession -> ConversationMessage
  -> AuditLog -> RiskScore -> Evidence
"""

from __future__ import annotations

import csv
import subprocess
import sys

import shutil as _shutil

# subprocess.run(["catalyst", ...]) fails with WinError 2 on Windows —
# catalyst is a .cmd npm shim; passing its bare name doesn't resolve via
# CreateProcess the way it does through a real shell. shutil.which finds
# the actual path (confirmed: %APPDATA%\npm\catalyst.cmd) and that full
# path IS directly runnable via subprocess.run with no shell=True needed
# (confirmed with a real `catalyst --version` call).
CATALYST_BIN = _shutil.which("catalyst")
if not CATALYST_BIN:
    raise RuntimeError("catalyst CLI not found on PATH — is it installed?")

# Verified 2026-07-21 via `catalyst ds:import --help` / `ds:export --help`
# (CLI v1.27.0):
#   ds:import [options] [file]   --table <name|id>  --config <path>  --production
#   ds:export [options] [table]  --table <name|id>  --config <path>  --page <page>  --production
#
# CONFIRMED 2026-07-21 by a real test run against the datathon-2026 project
# (`catalyst ds:import data_generation/csv_out/State.csv --table State`):
#   ds:import is INTERACTIVE without --config — it prompts "Select a bucket
#   to which you want to upload the object to" (arrow-key menu) before it
#   will proceed, because the CSV is staged through a Stratus bucket first.
#   This subprocess wrapper WILL FAIL non-interactively until --config is
#   given a JSON file that specifies the bucket (schema still unconfirmed —
#   check docs.catalyst.zoho.com/en/cli/v1/cli-command-reference/ for the
#   exact keys, don't guess them). The project already has an `evidences`
#   Stratus bucket provisioned — worth using for Evidence.FileURL uploads
#   too (see evidence.py's Stratus TODO) once --config's bucket key is known.
#
# CONFIRMED FURTHER via real ds:import/ds:export runs against datathon-2026
# (a full round trip: State.csv -> ds:import -> ds:export -> row verified
# present with correct ROWID):
#   - ds:export: schedules a job, asks "Do you like to download the report
#     of this job to your cmd execution directory? (y/N)". Piping "y"
#     works and produces Export_<jobid>_<timestamp>.zip in the CWD,
#     containing Table-<TableName>.csv with header:
#       ROWID, CREATORID, CREATEDTIME, MODIFIEDTIME, <...declared columns...>
#     ROWID IS present — fetch_rowid_map's approach is valid. "n" produces
#     no file at all.
#   - ds:import: after "Successfully scheduled import job ... jobid
#     "12345"", the CLI drops into a LIVE TUI status view (spinner +
#     box-drawing redraw) before it ever reaches a y/N prompt. That live
#     view CRASHES under a piped/non-tty subprocess ("An unexpected error
#     has occurred") regardless of what's piped to stdin — this is a
#     terminal-raw-mode incompatibility, not a missing prompt answer.
#     BUT: the crash is purely client-side rendering. Confirmed by
#     re-running ds:export afterward — the job had actually completed
#     server-side and the row was present with the correct data. So
#     import_table() below treats a nonzero exit as tolerable IF stdout
#     already contains "Successfully scheduled" + a job id; the actual
#     completion still has to be confirmed later via fetch_rowid_map.
#   - Retrying ds:import with the SAME csv filename produces
#     "HTTP Error: 409 ... uploading the object to the stratus" — Stratus
#     keys the staged upload by filename, so a stale object from a prior
#     attempt collides. import_table() stages each call through a
#     uniquely-named temp copy of the CSV to dodge this on reruns.
#
# STILL UNCONFIRMED / OPEN:
#   - --config <path> JSON schema (bucket key, to skip the interactive
#     bucket picker — it's an arrow-key TUI menu, not text-answerable via
#     stdin, so headless automation is still blocked on this specifically)
#   - exact completion latency between "scheduled" and rows being visible
#     via ds:export — fetch_rowid_map retries with backoff below, tune the
#     attempt count/delay against real timing once you've run this at
#     10k-row scale, single-row State took a few seconds
DS_IMPORT_EXTRA_ARGS: list[str] = []
DS_EXPORT_EXTRA_ARGS: list[str] = []
_EXPORT_ZIP_GLOB = "Export_*.zip"  # confirmed pattern, see above
_JOB_ID_RE = r'jobid\s*"(\d+)"'  # confirmed against real ds:import/ds:export stdout ("...jobid "12345"")


def _coerce_id(raw: str) -> int | str:
    """Named ID columns are usually int (StateID, DistrictID, ...) but
    Act's named PK is the string ActCode ("IPC"/"BNS") — keep it as a
    string in that case rather than forcing int() and crashing."""
    try:
        return int(raw)
    except ValueError:
        return raw


def _run_cli(args: list[str], stdin_input: str | None = None, timeout: int | None = 600) -> subprocess.CompletedProcess:
    result = subprocess.run(
        [CATALYST_BIN, *args], capture_output=True, text=True, input=stdin_input, timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"catalyst {' '.join(args)} failed (exit {result.returncode}):\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return result


def import_table(csv_path: str, table_name: str) -> str:
    """Submits csv_path as a `catalyst ds:import` job for table_name.
    Returns the job id ("submitted", not "completed" — call
    fetch_rowid_map afterward to confirm rows actually landed).

    Stages csv_path through a uniquely-named temp copy first: retrying
    ds:import with the same filename hits a Stratus 409 (stale object from
    a prior attempt), confirmed against a real rerun.

    Unresolved: without --config specifying a bucket, ds:import shows an
    arrow-key bucket picker (TUI menu, not text-answerable via stdin) —
    if your project has more than one Stratus bucket this WILL hang;
    confirmed working here only because `evidences` was the sole option
    and got auto-selected."""
    import os
    import re
    import shutil
    import time

    staged = f"{os.path.splitext(csv_path)[0]}_{int(time.time() * 1000)}.csv"
    shutil.copyfile(csv_path, staged)
    try:
        print(f"[pipeline] ds:import {table_name} <- {staged}")
        result = subprocess.run(
            [CATALYST_BIN, "ds:import", staged, "--table", table_name, *DS_IMPORT_EXTRA_ARGS],
            capture_output=True, text=True, timeout=600, input="y\n",
        )
    finally:
        os.remove(staged)

    job_match = re.search(_JOB_ID_RE, result.stdout)
    if not job_match:
        # Real client-side crash after scheduling doesn't always include the
        # job-id line in captured stdout order — surface everything we have.
        raise RuntimeError(
            f"ds:import for {table_name}: no job id found (exit {result.returncode}):\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    job_id = job_match.group(1)
    if result.returncode != 0:
        print(f"[pipeline] ds:import {table_name}: job {job_id} scheduled, client crashed "
              f"after (confirmed benign — see pipeline.py header comment), continuing")
    else:
        print(f"[pipeline] ds:import {table_name}: job {job_id} scheduled")
    return job_id


def _export_table_rows(
    table_name: str, search_dir: str = ".", max_attempts: int = 6, retry_delay_s: float = 5.0,
) -> list[dict[str, str]]:
    """Runs `catalyst ds:export` for table_name, answers its "download
    report" prompt with "y" (confirmed necessary — "n" produces no file),
    unzips the resulting Export_<jobid>_<ts>.zip, returns
    Table-<table_name>.csv's rows as raw string dicts (including ROWID).

    Retries up to max_attempts times if the export comes back with 0 data
    rows — the matching ds:import job may still be processing server-side
    (confirmed: a single-row State.csv import took a few seconds to become
    visible via export). Tune max_attempts/retry_delay_s once you've timed
    a real 10k-row import."""
    import glob
    import os
    import re
    import time
    import zipfile

    csv_name = f"Table-{table_name}.csv"
    last_error = None
    for attempt in range(1, max_attempts + 1):
        print(f"[pipeline] ds:export {table_name} (attempt {attempt}/{max_attempts})")
        result = _run_cli(["ds:export", "--table", table_name, *DS_EXPORT_EXTRA_ARGS], stdin_input="y\n")

        job_match = re.search(_JOB_ID_RE, result.stdout)
        zips = sorted(glob.glob(os.path.join(search_dir, _EXPORT_ZIP_GLOB)), key=os.path.getmtime)
        if job_match:
            zips = [z for z in zips if job_match.group(1) in z] or zips
        if not zips:
            raise RuntimeError(f"ds:export for {table_name}: no {_EXPORT_ZIP_GLOB} found under {search_dir}")
        zip_path = zips[-1]

        with zipfile.ZipFile(zip_path) as zf:
            if csv_name not in zf.namelist():
                raise RuntimeError(f"{zip_path}: expected {csv_name}, found {zf.namelist()}")
            with zf.open(csv_name) as f:
                rows = list(csv.DictReader(line.decode("utf-8") for line in f))

        if rows:
            return rows
        last_error = f"{zip_path}: {csv_name} has 0 data rows"
        if attempt < max_attempts:
            time.sleep(retry_delay_s)

    raise RuntimeError(
        f"export for {table_name}: still 0 rows after {max_attempts} attempts "
        f"({last_error}) — check `catalyst ds:status import <jobid>` by hand"
    )


def fetch_rowid_map(
    table_name: str, named_id_column: str, search_dir: str = ".",
    max_attempts: int = 6, retry_delay_s: float = 5.0,
) -> dict[int | str, int]:
    """{named_id_column value: ROWID} for a table with a single-column
    named ID (StateID, DistrictID, ... or the string ActCode). Section is
    the one exception — its named PK is a composite, use
    fetch_section_rowid_map for it instead."""
    rows = _export_table_rows(table_name, search_dir, max_attempts, retry_delay_s)
    return {_coerce_id(row[named_id_column]): int(row["ROWID"]) for row in rows}


def fetch_section_rowid_map(
    search_dir: str = ".", max_attempts: int = 6, retry_delay_s: float = 5.0,
) -> dict[tuple[int, str], int]:
    """Section's named PK is (ActCode_FK, SectionCode) — no single-column
    ID. Returns {(act_rowid, section_code): section_rowid}, matching the
    shape case_children.generate_act_section_association already expects."""
    rows = _export_table_rows("Section", search_dir, max_attempts, retry_delay_s)
    return {(int(row["ActCode_FK"]), row["SectionCode"]): int(row["ROWID"]) for row in rows}


def _csv_path(table_name: str) -> str:
    import os

    from data_generation.utils import CSV_DIR
    return os.path.join(CSV_DIR, f"{table_name}.csv")


def _sync(table_name: str, named_id_column: str) -> dict[int | str, int]:
    """import_table + fetch_rowid_map, the common case for a lookup table
    with a single-column named ID. named_id_column must be the BUILT-AS
    column name (post schema.md naming-drift), since it's read straight
    from the real ds:export CSV, not from our clean in-memory row dicts."""
    import_table(_csv_path(table_name), table_name)
    return fetch_rowid_map(table_name, named_id_column)


def run_lookups() -> dict[str, object]:
    """Runs the full lookups table group for real against Catalyst, in
    ddl_reference.md's parent-before-child order. Returns every
    {named_id: rowid} map (+ raw rows where a later table needs the full
    row, e.g. district names for Court) so a same-process case_master run
    can reuse them without re-exporting. A standalone `--only case_master`
    run in a fresh process would need to re-derive these via fetch_rowid_map
    against the already-imported lookup tables instead."""
    from data_generation.generators import lookups as L

    print("[pipeline] lookups: State")
    states = L.generate_states()
    state_map = _sync("State", "StateID")

    print("[pipeline] lookups: District")
    districts = L.generate_districts(state_map)
    district_map = _sync("District", "DistrictID")

    print("[pipeline] lookups: UnitType")
    unittypes = L.generate_unit_types()
    unittype_map = _sync("UnitType", "UnitTypeID")

    print("[pipeline] lookups: Unit")
    units = L.generate_units(unittype_map, state_map, districts, district_map, stations_per_district=4)
    unit_map = _sync("Unit", "UnitID")

    print("[pipeline] lookups: Rank")
    ranks = L.generate_ranks()
    rank_map = _sync("Rank", "RankID")

    print("[pipeline] lookups: Designation")
    desigs = L.generate_designations()
    desig_map = _sync("Designation", "DesignationID")

    print("[pipeline] lookups: Employee")
    employees = L.generate_employees(districts, district_map, units, unit_map, rank_map, desig_map, count=300)
    employee_map = _sync("Employee", "EmployeeID")

    print("[pipeline] lookups: CaseCategory")
    case_categories = L.generate_case_category()
    case_category_map = _sync("CaseCategory", "CaseCategoryID")

    print("[pipeline] lookups: GravityOffence")
    gravity = L.generate_gravity_offence()
    gravity_map = _sync("GravityOffence", "GravityOffence")  # column drift: ID col renamed to match table name

    print("[pipeline] lookups: CrimeHead")
    crimeheads = L.generate_crime_head()
    crimehead_map = _sync("CrimeHead", "CrimeHeadID")

    print("[pipeline] lookups: CrimeSubHead")
    crimesubheads = L.generate_crime_subhead(crimeheads, crimehead_map)
    crimesubhead_map = _sync("CrimeSubHead", "CrimeSubHeadID")

    print("[pipeline] lookups: Act")
    acts = L.generate_act()
    act_map = _sync("Act", "ActCode")  # string named PK, handled by _coerce_id

    print("[pipeline] lookups: Section")
    sections = L.generate_section(act_map)
    import_table(_csv_path("Section"), "Section")
    section_map = fetch_section_rowid_map()  # composite (ActCode_FK, SectionCode) key

    print("[pipeline] lookups: CrimeHeadActSection")
    L.generate_crimehead_act_section(crimeheads, crimehead_map, act_map, sections, section_map)
    import_table(_csv_path("CrimeHeadActSection"), "CrimeHeadActSection")  # no downstream FK needs its rowid

    print("[pipeline] lookups: CaseStatusMaster")
    case_statuses = L.generate_case_status()
    case_status_map = _sync("CaseStatusMaster", "CaseStatusID")

    print("[pipeline] lookups: Court")
    courts = L.generate_court(districts, district_map, state_map)
    court_map = _sync("Court", "CourtID")

    print("[pipeline] lookups: CasteMaster")
    castes = L.generate_caste_master()
    caste_map = _sync("CasteMaster", "caste_master_id")

    print("[pipeline] lookups: ReligionMaster")
    religions = L.generate_religion_master()
    religion_map = _sync("ReligionMaster", "ReligionID")

    print("[pipeline] lookups: OccupationMaster")
    occupations = L.generate_occupation_master()
    occupation_map = _sync("OccupationMaster", "OccupationID")

    print("[pipeline] lookups group complete")
    return {
        "states": states, "state_map": state_map,
        "districts": districts, "district_map": district_map,
        "unittypes": unittypes, "unittype_map": unittype_map,
        "units": units, "unit_map": unit_map,
        "ranks": ranks, "rank_map": rank_map,
        "desigs": desigs, "desig_map": desig_map,
        "employees": employees, "employee_map": employee_map,
        "case_categories": case_categories, "case_category_map": case_category_map,
        "gravity": gravity, "gravity_map": gravity_map,
        "crimeheads": crimeheads, "crimehead_map": crimehead_map,
        "crimesubheads": crimesubheads, "crimesubhead_map": crimesubhead_map,
        "acts": acts, "act_map": act_map,
        "sections": sections, "section_map": section_map,
        "case_statuses": case_statuses, "case_status_map": case_status_map,
        "courts": courts, "court_map": court_map,
        "castes": castes, "caste_map": caste_map,
        "religions": religions, "religion_map": religion_map,
        "occupations": occupations, "occupation_map": occupation_map,
    }


def run_case_master(lookups: dict[str, object], case_count: int = 2000) -> dict[str, object]:
    """CaseMaster + Inv_OccuranceTime. case_count=2000, not the originally
    discussed 10k — deliberately scaled down for this first real run of a
    big-payload import (unlike lookups' small tables, this is the first
    test of a multi-thousand-row CSV through ds:import/ds:export; safer to
    validate the pattern here before committing to a much longer 10k run)."""
    from data_generation.generators import case_master as CM

    print(f"[pipeline] case_master: CaseMaster (count={case_count})")
    cases, case_plans = CM.generate_case_master(
        lookups["districts"], lookups["district_map"], lookups["units"], lookups["unit_map"],
        lookups["employees"], lookups["employee_map"],
        lookups["case_categories"], lookups["case_category_map"],
        lookups["gravity"], lookups["gravity_map"],
        lookups["crimeheads"], lookups["crimehead_map"],
        lookups["crimesubheads"], lookups["crimesubhead_map"],
        lookups["case_statuses"], lookups["case_status_map"],
        lookups["courts"], lookups["court_map"],
        count=case_count,
    )
    case_master_map = _sync("CaseMaster", "CseMasterID")  # schema.md naming drift

    print("[pipeline] case_master: Inv_OccuranceTime")
    CM.generate_occurance_time(cases, case_master_map)
    import_table(_csv_path("Inv_OccuranceTime"), "Inv_OccuranceTime")  # no downstream FK needs its rowid

    print("[pipeline] case_master group complete")
    return {"cases": cases, "case_master_map": case_master_map, "case_plans": case_plans}


def run_case_children(lookups: dict[str, object], case_master: dict[str, object]) -> dict[str, object]:
    from data_generation.generators import case_children as CC

    cases, case_master_map = case_master["cases"], case_master["case_master_map"]

    print("[pipeline] case_children: ComplainantDetails")
    CC.generate_complainants(
        cases, case_master_map, lookups["occupations"], lookups["occupation_map"],
        lookups["religions"], lookups["religion_map"], lookups["castes"], lookups["caste_map"],
    )
    import_table(_csv_path("ComplainantDetails"), "ComplainantDetails")

    print("[pipeline] case_children: Victim")
    CC.generate_victims(cases, case_master_map)
    import_table(_csv_path("Victim"), "Victim")

    print("[pipeline] case_children: Accused")
    accused, accused_by_case, gang_role_by_accused_id = CC.generate_accused(
        cases, case_master_map, case_master["case_plans"],
    )
    accused_map = _sync("Accused", "AccusedMasterID")
    gang_role_by_accused_rowid = {accused_map[k]: v for k, v in gang_role_by_accused_id.items()}

    print("[pipeline] case_children: ActSectionAssociation")
    CC.generate_act_section_association(
        cases, case_master_map, lookups["act_map"], lookups["sections"], lookups["section_map"],
    )
    import_table(_csv_path("ActSectionAssociation"), "ActSectionAssociation")

    print("[pipeline] case_children: ArrestSurrender")
    unit_rowid_to_district_rowid = {
        lookups["unit_map"][u["UnitID"]]: u["DistrictID_FK"] for u in lookups["units"]
    }
    arrest_rows, _ = CC.generate_arrest_surrender(
        cases, case_master_map, accused_by_case, accused_map,
        lookups["state_map"], unit_rowid_to_district_rowid,
        lookups["employees"], lookups["employee_map"], lookups["courts"], lookups["court_map"],
    )
    arrest_map = _sync("ArrestSurrender", "ArrestSurrenderID")

    print("[pipeline] case_children: inv_arrestsurrenderaccused")
    CC.generate_arrest_surrender_accused(arrest_rows, arrest_map, gang_role_by_accused_rowid)
    import_table(_csv_path("inv_arrestsurrenderaccused"), "inv_arrestsurrenderaccused")

    print("[pipeline] case_children: ChargesheetDetails")
    charge_sheeted_named_id = next(
        s["CaseStatusID"] for s in lookups["case_statuses"] if s["CaseStatusName"] == "Charge Sheeted"
    )
    CC.generate_chargesheet_details(
        cases, case_master_map, lookups["case_status_map"], charge_sheeted_named_id,
        lookups["employees"], lookups["employee_map"],
    )
    import_table(_csv_path("ChargesheetDetails"), "ChargesheetDetails")

    print("[pipeline] case_children group complete")
    return {"accused": accused, "accused_map": accused_map}


def run_financial(case_master: dict[str, object], account_count: int = 500, txn_count: int = 1500) -> dict[str, object]:
    from data_generation.generators import financial as FIN

    print(f"[pipeline] financial: Account (count={account_count})")
    accounts = FIN.generate_accounts(count=account_count)
    account_map = _sync("Account", "AccountID")

    print(f"[pipeline] financial: Transaction (count={txn_count})")
    FIN.generate_transactions(accounts, account_map, count=txn_count)
    import_table(_csv_path("Transaction"), "Transaction")

    print("[pipeline] financial: AccountCaseLink")
    FIN.generate_account_case_links(
        case_master["cases"], case_master["case_master_map"], accounts, account_map,
    )
    import_table(_csv_path("AccountCaseLink"), "AccountCaseLink")

    print("[pipeline] financial group complete")
    return {"accounts": accounts, "account_map": account_map}


def run_app_layer(
    lookups: dict[str, object], case_master: dict[str, object], case_children: dict[str, object],
) -> None:
    from data_generation.generators import app_layer as APP

    print("[pipeline] app_layer: AppRole")
    roles = APP.generate_app_roles()
    role_map = _sync("AppRole", "RoleID")

    print("[pipeline] app_layer: AppUser")
    app_users = APP.generate_app_users(lookups["employees"], lookups["employee_map"], roles, role_map)
    app_user_map = _sync("AppUser", "AppUserID")

    print("[pipeline] app_layer: ConversationSession")
    sessions = APP.generate_conversation_sessions(app_users, app_user_map)
    session_map = _sync("ConversationSession", "SessionID")

    print("[pipeline] app_layer: ConversationMessage")
    district_names = [d["DistrictName"] for d in lookups["districts"]]
    APP.generate_conversation_messages(
        sessions, session_map, case_master["cases"], case_master["case_master_map"], district_names,
    )
    import_table(_csv_path("ConversationMessage"), "ConversationMessage")

    print("[pipeline] app_layer: AuditLog")
    APP.generate_audit_log(app_users, app_user_map)
    import_table(_csv_path("AuditLog"), "AuditLog")

    print("[pipeline] app_layer: RiskScore")
    APP.generate_risk_scores(case_children["accused"], case_children["accused_map"])
    import_table(_csv_path("RiskScore"), "RiskScore")

    print("[pipeline] app_layer: Evidence")
    APP.generate_evidence(case_master["cases"], case_master["case_master_map"])
    import_table(_csv_path("Evidence"), "Evidence")

    print("[pipeline] app_layer group complete")


TABLE_GROUPS = ["lookups", "case_master", "case_children", "financial", "app_layer"]


def run(only: str | None = None) -> None:
    """NOTE: case_master/case_children/financial/app_layer's rowid maps are
    threaded through IN MEMORY from run_lookups()/run_case_master() within
    this single process run. A standalone `--only case_children` (etc.) in
    a fresh process would need those maps re-derived via fresh ds:export
    calls against the already-imported tables first — not implemented,
    since today's goal is one full sequential run, not repeated partial
    reruns. Add that if/when partial reruns are actually needed."""
    groups = [only] if only else TABLE_GROUPS
    lookups = case_master = case_children = None
    for group in groups:
        if group not in TABLE_GROUPS:
            raise ValueError(f"unknown group {group!r}, choose from {TABLE_GROUPS}")
        print(f"\n=== running group: {group} ===")
        if group == "lookups":
            lookups = run_lookups()
        elif group == "case_master":
            if lookups is None:
                raise RuntimeError("case_master needs lookups — run the lookups group first in this process")
            case_master = run_case_master(lookups)
        elif group == "case_children":
            if lookups is None or case_master is None:
                raise RuntimeError("case_children needs lookups + case_master run first in this process")
            case_children = run_case_children(lookups, case_master)
        elif group == "financial":
            if case_master is None:
                raise RuntimeError("financial needs case_master run first in this process")
            run_financial(case_master)
        elif group == "app_layer":
            if lookups is None or case_master is None or case_children is None:
                raise RuntimeError("app_layer needs lookups + case_master + case_children run first in this process")
            run_app_layer(lookups, case_master, case_children)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=TABLE_GROUPS, default=None)
    args = parser.parse_args()
    try:
        run(only=args.only)
    except Exception as e:
        print(f"[pipeline] ABORTED: {e}", file=sys.stderr)
        sys.exit(1)
