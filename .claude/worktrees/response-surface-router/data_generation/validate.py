"""Validation gates, run after each table's CSV is generated (and again
after ds:import + ROWID-map fetch, before the pipeline moves to the next
table group). Per CLAUDE.md: not optional, catch a bad generator before
10k rows are in.
"""

from __future__ import annotations

import datetime
import re
from typing import Any

CRIME_NO_RE = re.compile(r"^\d{18}$")  # 1 category + 4 district + 4 station + 4 year + 5 serial


def validate_crime_no(crime_no: str) -> bool:
    return bool(CRIME_NO_RE.match(crime_no))


def _parse(value: str) -> datetime.datetime:
    """Accepts either a date-only or full-datetime ISO string; date-only is
    treated as end-of-day so `date <= datetime` ordering checks are honest
    about the granularity mismatch instead of failing on string prefixes."""
    if len(value) == 10:
        d = datetime.date.fromisoformat(value)
        return datetime.datetime.combine(d, datetime.time.max)
    return datetime.datetime.fromisoformat(value)


def validate_date_ordering(case_master_row: dict[str, Any]) -> list[str]:
    violations = []
    incident_from = _parse(case_master_row["IncidentFromDate"])
    incident_to = _parse(case_master_row["IncidentToDate"])
    info_received = _parse(case_master_row["InfoReceivedPSDate"])
    registered = _parse(case_master_row["CrimeRegisteredDate"])
    cmid = case_master_row.get("CaseMasterID")

    if not incident_from <= incident_to:
        violations.append(f"CaseMasterID {cmid}: IncidentFromDate > IncidentToDate")
    if not incident_to <= info_received:
        violations.append(f"CaseMasterID {cmid}: IncidentToDate > InfoReceivedPSDate")
    if not info_received <= registered:
        violations.append(f"CaseMasterID {cmid}: InfoReceivedPSDate > CrimeRegisteredDate")
    return violations


def validate_orphan_fks(
    rows: list[dict[str, Any]], fk_columns: dict[str, dict[Any, Any]], table_name: str
) -> list[str]:
    """fk_columns: {column_name: parent_rowid_map}. A blank/empty FK value
    is treated as a legitimate nullable FK, not an orphan."""
    violations = []
    for row in rows:
        for col, parent_map in fk_columns.items():
            val = row.get(col)
            if val in (None, "", "None"):
                continue
            if val not in set(parent_map.values()):
                violations.append(
                    f"{table_name}: row {row.get('ROWID', row)} has orphan {col}={val}"
                )
    return violations


def validate_age_plausibility(
    rows: list[dict[str, Any]], age_column: str = "AgeYear",
    min_age: int = 7, max_age: int = 100,
) -> list[str]:
    violations = []
    for row in rows:
        age = row.get(age_column)
        if age is None:
            continue
        if not (min_age <= age <= max_age):
            violations.append(f"row {row}: {age_column}={age} outside [{min_age}, {max_age}]")
    return violations


def run_all(table_name: str, rows: list[dict[str, Any]], **kwargs: Any) -> None:
    """kwargs:
      fk_columns: dict[str, dict] -- passed to validate_orphan_fks
      age_column: str -- passed to validate_age_plausibility
      is_case_master: bool -- run CrimeNo + date-ordering checks
    Raises ValueError with all violations joined, if any.
    """
    violations: list[str] = []

    if kwargs.get("is_case_master"):
        for row in rows:
            if not validate_crime_no(row["CrimeNo"]):
                violations.append(f"CaseMasterID {row.get('CaseMasterID')}: bad CrimeNo {row['CrimeNo']!r}")
            violations.extend(validate_date_ordering(row))

    fk_columns = kwargs.get("fk_columns")
    if fk_columns:
        violations.extend(validate_orphan_fks(rows, fk_columns, table_name))

    age_column = kwargs.get("age_column")
    if age_column:
        violations.extend(validate_age_plausibility(rows, age_column))

    if violations:
        preview = "\n".join(violations[:20])
        more = f"\n...and {len(violations) - 20} more" if len(violations) > 20 else ""
        raise ValueError(f"{table_name}: {len(violations)} validation violation(s):\n{preview}{more}")
