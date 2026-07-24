"""Phase 16 — Aggregate endpoints + hotspots feeding Person A's Leaflet map.

GET /api/aggregates?type=trend|geography|crime-type&date_from=&date_to=&crime_type=
GET /api/hotspots?date_from=&date_to=&crime_type=

ZCQL JOIN and nested SELECT are confirmed unusable on this schema (see
pipeline.py's live-confirmed note: every _FK column is a plain integer, not
a Lookup relationship, so JOIN always fails with "No relationship between
tables"). Same pattern already used by network.py/similar_cases.py: paginate
raw rows out of CaseMaster + the small reference tables, then join/aggregate
in Python. GROUP BY is likewise not relied on anywhere else in this codebase,
so aggregation here is a plain Counter over fetched rows.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

import numpy as np
from sklearn.cluster import DBSCAN

import zcql_util

_PAGE = 200

_VALID_AGGREGATE_TYPES = {"trend", "geography", "crime-type"}


class InvalidAggregateType(Exception):
    pass


def _fetch_all(zcql_service: Any, table: str, columns: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    last_rowid = 0
    cols = ", ".join(["ROWID"] + columns)
    while True:
        batch = zcql_util.run(
            zcql_service,
            f"SELECT {cols} FROM {table} WHERE ROWID > {last_rowid} ORDER BY ROWID ASC LIMIT {_PAGE}",
        )
        if not batch:
            break
        rows.extend(batch)
        last_rowid = int(batch[-1]["ROWID"])
    return rows


def _crime_head_rowids_matching(zcql_service: Any, crime_type: str) -> set[int]:
    heads = _fetch_all(zcql_service, "CrimeHead", ["CrimeGroupName"])
    return {
        int(r["ROWID"]) for r in heads
        if str(r.get("CrimeGroupName", "")).lower() == crime_type.lower()
    }


def _fetch_cases(
    zcql_service: Any, date_from: str | None, date_to: str | None, crime_type: str | None,
) -> list[dict[str, Any]]:
    rows = _fetch_all(zcql_service, "CaseMaster", [
        "CseMasterID", "CrimeRegisteredDate", "Latitude", "Longitude",
        "GravityOffenceID", "CrimeMajorHeadID_FK", "PoliceStationID_FK",
    ])
    if date_from:
        rows = [r for r in rows if str(r.get("CrimeRegisteredDate", "")) >= date_from]
    if date_to:
        rows = [r for r in rows if str(r.get("CrimeRegisteredDate", "")) <= date_to]
    if crime_type:
        matching_rowids = _crime_head_rowids_matching(zcql_service, crime_type)
        rows = [r for r in rows if _to_int(r.get("CrimeMajorHeadID_FK")) in matching_rowids]
    return rows


def _to_int(value: Any, default: int = -1) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def get_aggregates(
    zcql_service: Any, agg_type: str | None, date_from: str | None, date_to: str | None, crime_type: str | None,
) -> dict[str, Any]:
    if agg_type not in _VALID_AGGREGATE_TYPES:
        raise InvalidAggregateType(
            f"type must be one of {sorted(_VALID_AGGREGATE_TYPES)}, got {agg_type!r}"
        )

    cases = _fetch_cases(zcql_service, date_from, date_to, crime_type)

    if agg_type == "trend":
        counts = Counter(str(r.get("CrimeRegisteredDate", ""))[:7] for r in cases)  # YYYY-MM
        series = [{"month": k, "count": v} for k, v in sorted(counts.items())]
        return {"type": "trend", "series": series}

    if agg_type == "crime-type":
        heads = _fetch_all(zcql_service, "CrimeHead", ["CrimeGroupName"])
        head_name_by_rowid = {int(r["ROWID"]): r.get("CrimeGroupName", "Unknown") for r in heads}
        counts = Counter(
            head_name_by_rowid.get(_to_int(r.get("CrimeMajorHeadID_FK")), "Unknown") for r in cases
        )
        series = [{"crime_type": k, "count": v} for k, v in counts.most_common()]
        return {"type": "crime-type", "series": series}

    # geography: CaseMaster.PoliceStationID_FK -> Unit.ROWID -> Unit.DistrictID_FK -> District.ROWID -> District.DistrictName
    units = _fetch_all(zcql_service, "Unit", ["DistrictID_FK"])
    district_rowid_by_unit_rowid = {int(u["ROWID"]): _to_int(u.get("DistrictID_FK")) for u in units}
    districts = _fetch_all(zcql_service, "District", ["DistrictName"])
    district_name_by_rowid = {int(d["ROWID"]): d.get("DistrictName", "Unknown") for d in districts}
    counts = Counter(
        district_name_by_rowid.get(
            district_rowid_by_unit_rowid.get(_to_int(r.get("PoliceStationID_FK")), -1), "Unknown",
        )
        for r in cases
    )
    series = [{"district": k, "count": v} for k, v in counts.most_common()]
    return {"type": "geography", "series": series}


def get_hotspots(
    zcql_service: Any, date_from: str | None, date_to: str | None, crime_type: str | None,
    eps_degrees: float = 0.05, min_samples: int = 3,
) -> dict[str, Any]:
    """DBSCAN over lat/long, cluster score weighted by recency + severity —
    "clustering, not raw density" per backend_ultraplan.md. eps_degrees ~0.05
    is roughly a 5km radius at these latitudes; tune once checked against
    real synthetic point spread.
    ponytail: fixed eps/min_samples, not distance-adaptive. Upgrade if
    real data shows very uneven point density across districts."""
    cases = _fetch_cases(zcql_service, date_from, date_to, crime_type)
    points = [
        (r["CseMasterID"], r["Latitude"], r["Longitude"], r.get("CrimeRegisteredDate", ""), r.get("GravityOffenceID"))
        for r in cases
        if r.get("Latitude") is not None and r.get("Longitude") is not None
    ]
    if not points:
        return {"clusters": []}

    coords = np.array([[float(p[1]), float(p[2])] for p in points])
    labels = DBSCAN(eps=eps_degrees, min_samples=min_samples).fit_predict(coords)

    dates = [str(p[3]) for p in points]
    latest_date = max((d for d in dates if d), default="")

    clusters: dict[int, list[int]] = {}
    for idx, label in enumerate(labels):
        if label == -1:  # DBSCAN noise point, not a hotspot
            continue
        clusters.setdefault(int(label), []).append(idx)

    result = []
    for member_idxs in clusters.values():
        member_coords = coords[member_idxs]
        centroid_lat, centroid_lon = member_coords.mean(axis=0)
        case_ids = [int(points[i][0]) for i in member_idxs]

        recency_scores = [1.0 if dates[i] == latest_date else 0.5 for i in member_idxs]
        severity_scores = [_to_int(points[i][4], default=1) for i in member_idxs]
        max_severity = max(severity_scores) or 1
        weighted = [
            (0.6 * (severity_scores[j] / max_severity)) + (0.4 * recency_scores[j])
            for j in range(len(member_idxs))
        ]
        score = round(len(member_idxs) * (sum(weighted) / len(weighted)), 3)

        result.append({
            "lat": round(float(centroid_lat), 6),
            "lon": round(float(centroid_lon), 6),
            "count": len(member_idxs),
            "score": score,
            "case_ids": sorted(case_ids),
        })
    result.sort(key=lambda c: c["score"], reverse=True)
    return {"clusters": result}


def _demo() -> None:
    """ponytail self-check: aggregation + clustering logic on a small
    synthetic in-memory sample, no live ZCQL involved."""
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
        {"ROWID": 1, "CseMasterID": 101, "CrimeRegisteredDate": "2024-01-15", "Latitude": 12.97, "Longitude": 77.59, "GravityOffenceID": 3, "CrimeMajorHeadID_FK": 1, "PoliceStationID_FK": 1},
        {"ROWID": 2, "CseMasterID": 102, "CrimeRegisteredDate": "2024-01-20", "Latitude": 12.971, "Longitude": 77.591, "GravityOffenceID": 5, "CrimeMajorHeadID_FK": 1, "PoliceStationID_FK": 1},
        {"ROWID": 3, "CseMasterID": 103, "CrimeRegisteredDate": "2024-02-01", "Latitude": 12.972, "Longitude": 77.592, "GravityOffenceID": 2, "CrimeMajorHeadID_FK": 2, "PoliceStationID_FK": 2},
        {"ROWID": 4, "CseMasterID": 104, "CrimeRegisteredDate": "2024-02-10", "Latitude": 15.5, "Longitude": 80.0, "GravityOffenceID": 4, "CrimeMajorHeadID_FK": 2, "PoliceStationID_FK": 2},
    ]
    fake_heads = [
        {"ROWID": 1, "CrimeGroupName": "Crimes Against Body"},
        {"ROWID": 2, "CrimeGroupName": "Crimes Against Property"},
    ]
    fake_units = [{"ROWID": 1, "DistrictID_FK": 1}, {"ROWID": 2, "DistrictID_FK": 2}]
    fake_districts = [{"ROWID": 1, "DistrictName": "Bengaluru"}, {"ROWID": 2, "DistrictName": "Mysuru"}]

    zcql = _FakeZcql({
        "CaseMaster": fake_cases, "CrimeHead": fake_heads,
        "Unit": fake_units, "District": fake_districts,
    })

    trend = get_aggregates(zcql, "trend", None, None, None)
    assert trend["series"] == [{"month": "2024-01", "count": 2}, {"month": "2024-02", "count": 2}], trend

    crime_type = get_aggregates(zcql, "crime-type", None, None, None)
    assert {"crime_type": "Crimes Against Body", "count": 2} in crime_type["series"], crime_type

    geo = get_aggregates(zcql, "geography", None, None, None)
    assert {"district": "Bengaluru", "count": 2} in geo["series"], geo

    hotspots = get_hotspots(zcql, None, None, None, eps_degrees=0.01, min_samples=2)
    assert len(hotspots["clusters"]) == 1, hotspots  # the 3 close points cluster, the far one is noise
    assert hotspots["clusters"][0]["count"] == 3, hotspots

    try:
        get_aggregates(zcql, "bogus", None, None, None)
        raise AssertionError("expected InvalidAggregateType")
    except InvalidAggregateType:
        pass

    print("aggregates._demo: all assertions passed")


if __name__ == "__main__":
    _demo()
