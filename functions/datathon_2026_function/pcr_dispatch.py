"""PCR (Police Control Room) dispatch simulation — demonstrates emergency
response speed. Stateless by design (confirmed with the user): every call
independently samples fresh "immediate priority" cases and fabricates a
van/ETA, no persistence, no schema.md changes. The 30-second cadence lives
entirely in the frontend's poll interval, not in this module or a Catalyst
Cron job.

"Immediate priority" = a case with a heinous GravityOffence, still active
(not yet closed/chargesheeted) per CaseStatusMaster — reuses the
paginated-fetch-then-Python-join pattern already established in
aggregates.py, since ZCQL JOIN is confirmed unusable on this schema
(pipeline.py's live-confirmed note: every _FK column is a plain integer,
not a Lookup relationship).
"""

from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Any

from aggregates import _fetch_all, _to_int

_DISPATCH_COUNT = 10
_VAN_COUNT = 40
_ETA_MIN_MINUTES = 3
_ETA_MAX_MINUTES = 15

# Heinous-tier gravity labels and active-tier status labels are matched by
# substring against the lookup tables' free-text LookupValue/CaseStatusName
# columns, not a hardcoded ID — those IDs aren't fixed by schema.md and
# depend on synthetic-generation order.
_HEINOUS_MARKERS = ("heinous",)
_ACTIVE_STATUS_MARKERS = ("investigation", "open", "pending", "registered")


def _priority_gravity_rowids(zcql_service: Any) -> set[int]:
    rows = _fetch_all(zcql_service, "GravityOffence", ["LookupValue"])
    return {
        int(r["ROWID"]) for r in rows
        if any(m in str(r.get("LookupValue", "")).lower() for m in _HEINOUS_MARKERS)
        and "non-heinous" not in str(r.get("LookupValue", "")).lower()
    }


def _active_status_rowids(zcql_service: Any) -> set[int]:
    rows = _fetch_all(zcql_service, "CaseStatusMaster", ["CaseStatusName"])
    return {
        int(r["ROWID"]) for r in rows
        if any(m in str(r.get("CaseStatusName", "")).lower() for m in _ACTIVE_STATUS_MARKERS)
    }


def get_active_dispatches(zcql_service: Any) -> list[dict[str, Any]]:
    priority_gravity = _priority_gravity_rowids(zcql_service)
    active_status = _active_status_rowids(zcql_service)

    cases = _fetch_all(zcql_service, "CaseMaster", [
        "CseMasterID", "Latitude", "Longitude", "GravityOffenceID", "CaseStatusID_FK", "CrimeMinorHeadID_FK",
    ])
    candidates = [
        r for r in cases
        if _to_int(r.get("GravityOffenceID")) in priority_gravity
        and _to_int(r.get("CaseStatusID_FK")) in active_status
        and r.get("Latitude") is not None and r.get("Longitude") is not None
    ]
    # Fall back to any case with valid coordinates if the priority filter
    # starves the demo (e.g. sparse synthetic data) — still a real case,
    # just not heinous+active; better than returning an empty dispatch board.
    if not candidates:
        candidates = [r for r in cases if r.get("Latitude") is not None and r.get("Longitude") is not None]
    if not candidates:
        return []

    sample = random.sample(candidates, min(_DISPATCH_COUNT, len(candidates)))
    now = datetime.now(timezone.utc)
    return [
        {
            "case_id": int(r["CseMasterID"]),
            "lat": float(r["Latitude"]),
            "lon": float(r["Longitude"]),
            "van_id": f"PCR-{random.randint(1, _VAN_COUNT):02d}",
            "eta_minutes": random.randint(_ETA_MIN_MINUTES, _ETA_MAX_MINUTES),
            "dispatched_at": now.replace(microsecond=0).isoformat(),
        }
        for r in sample
    ]


def _demo() -> None:
    """ponytail self-check: priority filtering + fallback + sample-size cap,
    no live ZCQL involved."""
    class _FakeZcql:
        def __init__(self, tables: dict[str, list[dict[str, Any]]]):
            self._tables = tables

        def execute_query(self, sql: str):
            table = sql.split("FROM", 1)[1].split()[0]
            rows = self._tables.get(table, [])
            if "ROWID > " in sql:
                floor = int(sql.split("ROWID > ", 1)[1].split()[0])
                rows = [r for r in rows if int(r["ROWID"]) > floor]
            return rows

    fake_cases = [
        {"ROWID": i, "CseMasterID": 100 + i, "Latitude": 12.9 + i * 0.01, "Longitude": 77.5 + i * 0.01,
         "GravityOffenceID": 1 if i % 2 == 0 else 2, "CaseStatusID_FK": 1, "CrimeMinorHeadID_FK": 1}
        for i in range(1, 6)
    ]
    fake_gravity = [{"ROWID": 1, "LookupValue": "Heinous"}, {"ROWID": 2, "LookupValue": "Non-Heinous"}]
    fake_status = [{"ROWID": 1, "CaseStatusName": "Under Investigation"}, {"ROWID": 2, "CaseStatusName": "Closed"}]

    zcql = _FakeZcql({"CaseMaster": fake_cases, "GravityOffence": fake_gravity, "CaseStatusMaster": fake_status})

    dispatches = get_active_dispatches(zcql)
    assert 1 <= len(dispatches) <= _DISPATCH_COUNT, dispatches
    assert all(d["case_id"] in {102, 104} for d in dispatches), dispatches  # only even i -> Heinous
    assert all(d["van_id"].startswith("PCR-") for d in dispatches), dispatches
    assert all(_ETA_MIN_MINUTES <= d["eta_minutes"] <= _ETA_MAX_MINUTES for d in dispatches), dispatches

    # No priority matches at all -> falls back to any case with coordinates, never empty.
    zcql_no_match = _FakeZcql({
        "CaseMaster": fake_cases, "GravityOffence": [{"ROWID": 1, "LookupValue": "Non-Heinous"}],
        "CaseStatusMaster": fake_status,
    })
    fallback = get_active_dispatches(zcql_no_match)
    assert len(fallback) == 5, fallback

    print("pcr_dispatch._demo: all assertions passed")


if __name__ == "__main__":
    _demo()
