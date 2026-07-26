"""Rule-based response-surface classifier for /api/query -- decides which
frontend surface (map, interactive accused network board, main dashboard
chart, evidence viewer, or the default card/text) an answer should render
as. Deterministic, no LLM call: CLAUDE.md's anti-hallucination stance
applies just as much to "what UI should show this" as to the SQL itself --
guessing the surface with an LLM would be one more place to hallucinate.

Two signal sources are combined, never either alone:
- STRUCTURAL: what the executed plan/rows actually contain (robust to
  rephrasing -- "murder cases near Mysuru" and "where did murders happen in
  Mysuru" hit the same structural signal even though their keywords differ).
- KEYWORD: what the question explicitly asks for, for cases the structure
  can't see yet (e.g. "show on a map" when the first-pass plan didn't
  select Latitude/Longitude -- pipeline.py patches the plan and re-executes
  when this fires, see needs_geo_backfill()).

Rule order is priority order -- first match wins. Extend the keyword sets
here as real usage surfaces new phrasings; this is meant to generalize past
docs/sample_questions.md's 51 verified questions, not just replay them.

No QueryPlan import from pipeline.py on purpose -- pipeline.py imports this
module, so importing back would be circular. `plan` is duck-typed: only
`plan.steps[-1].group_by` is read.
"""

from __future__ import annotations

from typing import Any, Literal

ResponseType = Literal["card", "chart", "map", "network", "evidence", "text", "dashboard"]

_DASHBOARD_KEYWORDS = (
    "state of crime", "crime situation", "crime overview", "overview of crime",
    "how is crime in", "how is the crime in", "crime report for", "summary of crime",
    "crime summary", "full picture", "everything about crime in", "crime scenario",
    "crime status in", "give me a report on",
)

_MAP_KEYWORDS = (
    "map", "location", "locations", "coordinate", "coordinates", "where is",
    "where are", "hotspot", "hotspots", "near", "nearby", "geograph",
)
_NETWORK_KEYWORDS = (
    "network", "connection", "connections", "connected", "linked", "link",
    "associate", "associates", "co-accused", "coaccused", "gang", "related to",
    "relationship between", "who else",
)
_CHART_KEYWORDS = (
    "trend", "trends", "over time", "compare", "comparison", "distribution",
    "breakdown", "by month", "by year", "by district", "pattern", "patterns",
)
_EVIDENCE_KEYWORDS = (
    "evidence", "video", "photo", "photos", "document", "documents",
    "footage", "recording", "attachment",
)

_GEO_COLUMNS = {"Latitude", "Longitude"}
_CASE_ID_COLUMNS = {"CseMasterID", "CaseMasterID_FK"}
_ACCUSED_ID_COLUMNS = {"AccusedMasterID", "AccusedMasterID_FK"}
_ARREST_LINK_COLUMNS = {"ArrestSurrenderID", "ArrestSurrenderAccusedID"}


def _any_keyword(question: str, keywords: tuple[str, ...]) -> bool:
    q = question.lower()
    return any(kw in q for kw in keywords)


def _has_geo_columns(rows: list[dict[str, Any]]) -> bool:
    if not rows:
        return False
    return _GEO_COLUMNS.issubset(rows[0].keys())


def _has_case_id(rows: list[dict[str, Any]]) -> bool:
    if not rows:
        return False
    return bool(set(rows[0].keys()) & _CASE_ID_COLUMNS)


def _resolved_accused_link(rows: list[dict[str, Any]]) -> bool:
    """True if rows already carry both an accused id and an arrest/surrender
    linkage column -- the structural signal that this result is really
    about how people connect, not just a flat list of cases."""
    if not rows:
        return False
    cols = set(rows[0].keys())
    return bool(cols & _ACCUSED_ID_COLUMNS) and bool(cols & (_ARREST_LINK_COLUMNS | _CASE_ID_COLUMNS))


def needs_dashboard(question: str) -> bool:
    """True when the question is a broad summary ask ("what's the state of
    crime in Mysuru") rather than a specific fact -- pipeline.py uses this
    to skip the single-table plan entirely and assemble a multi-panel
    composite instead (map + trend + crime-type breakdown + hotspots),
    since no single GROUP BY query answers "how is crime here" honestly."""
    return _any_keyword(question, _DASHBOARD_KEYWORDS)


def extract_district(question: str, known_districts: list[str]) -> str | None:
    """Best-effort district name match for scoping a dashboard (or any
    composite fetch) to one place -- case-insensitive substring match
    against the real District.DistrictName rows the caller fetched, never
    a hardcoded city list, so this works for every district in the data,
    not just the ones in docs/sample_questions.md's examples."""
    q = question.lower()
    for name in known_districts:
        if name.lower() in q:
            return name
    return None


def needs_geo_backfill(question: str, rows: list[dict[str, Any]]) -> bool:
    """True when the question clearly wants a map but the executed plan's
    rows don't carry Latitude/Longitude yet -- pipeline.py uses this to
    patch the final step's select and re-run execute_plan once before
    falling back to a plain card."""
    return _any_keyword(question, _MAP_KEYWORDS) and not _has_geo_columns(rows)


def needs_network_lookup(question: str, rows: list[dict[str, Any]]) -> bool:
    """True when the question wants the accused/relationship board --
    pipeline.py uses this to call network.build_case_network for the first
    resolved case id in rows, rather than trying to force a graph shape out
    of the plan/execute_plan machinery meant for flat rows."""
    return _any_keyword(question, _NETWORK_KEYWORDS) or _resolved_accused_link(rows)


def classify(question: str, plan: Any, rows: list[dict[str, Any]]) -> ResponseType:
    """Final surface decision -- call after execute_plan (and after any
    needs_geo_backfill/needs_network_lookup-triggered re-fetch pipeline.py
    already performed, so `rows` here reflects the final result set).

    dashboard is checked first and independently of `rows`/`plan` -- a
    broad summary question is decided by intent alone (pipeline.py never
    even runs the normal single-table plan for these, see Task 4), so it
    must win before any narrower map/chart/network keyword inside the same
    sentence ("state of crime near Mysuru" contains "near", a map keyword)
    accidentally downgrades it to a single-panel surface."""
    if needs_dashboard(question):
        return "dashboard"

    if not rows:
        return "text"

    if _has_geo_columns(rows):
        return "map"

    if needs_network_lookup(question, rows):
        return "network"

    final_step = plan.steps[-1]
    distinct_rows = {tuple(sorted(r.items())) for r in rows}
    multi_group_aggregate = bool(final_step.group_by) and len(distinct_rows) > 1
    if multi_group_aggregate or _any_keyword(question, _CHART_KEYWORDS):
        return "chart"

    if _any_keyword(question, _EVIDENCE_KEYWORDS) and _has_case_id(rows):
        return "evidence"

    return "card"


def _demo() -> None:
    """ponytail self-check: each surface's trigger condition, no live
    ZCQL/LLM involved. Also spot-checks against docs/sample_questions.md's
    documented behavior -- every plain count/list question there must still
    classify as 'card', and every map-shaped one must classify as 'map'."""

    class _FakeStep:
        def __init__(self, group_by: str = ""):
            self.group_by = group_by

    class _FakePlan:
        def __init__(self, group_by: str = ""):
            self.steps = [_FakeStep(group_by)]

    plain_plan = _FakePlan()
    assert classify("How many cases are there in total", plain_plan, [{"COUNT(CseMasterID)": 300}]) == "card"

    geo_rows = [{"CseMasterID": 1, "Latitude": 12.9, "Longitude": 77.5}]
    assert classify("Show me case locations for mapping", plain_plan, geo_rows) == "map"
    assert needs_geo_backfill("Show me case locations for mapping", [{"CseMasterID": 1}])
    assert not needs_geo_backfill("How many cases are there", [{"CseMasterID": 1}])

    network_rows = [{"CseMasterID": 1, "AccusedMasterID": 5, "ArrestSurrenderID": 9}]
    assert classify("Who is connected to this case's accused", plain_plan, network_rows) == "network"
    assert needs_network_lookup("Show the network for this accused", [])

    grouped_plan = _FakePlan(group_by="PoliceStationID_FK")
    grouped_rows = [
        {"PoliceStationID_FK": 1, "COUNT(CseMasterID)": 10},
        {"PoliceStationID_FK": 2, "COUNT(CseMasterID)": 5},
    ]
    assert classify("Top 5 police stations by number of cases", grouped_plan, grouped_rows) == "chart"

    single_group_rows = [{"PoliceStationID_FK": 1, "COUNT(CseMasterID)": 10}]
    assert classify("How many cases at this station", grouped_plan, single_group_rows) == "card"

    evidence_rows = [{"CseMasterID": 1}]
    assert classify("Show me the evidence video for this case", plain_plan, evidence_rows) == "evidence"

    assert classify("anything", plain_plan, []) == "text"

    assert needs_dashboard("What is the state of crime in Mysuru")
    assert needs_dashboard("Give me a crime overview for Ballari")
    assert not needs_dashboard("How many cases are there in total")
    # dashboard wins even when a narrower keyword ("near", a map keyword)
    # also appears in the same sentence -- priority order confirmed live.
    assert classify("What is the state of crime near Mysuru", plain_plan, geo_rows) == "dashboard"

    districts = ["Mysuru", "Ballari", "Tumakuru", "Bengaluru Urban"]
    assert extract_district("What is the state of crime in Mysuru district", districts) == "Mysuru"
    assert extract_district("How many cases in total", districts) is None

    print("response_router._demo: all assertions passed")


if __name__ == "__main__":
    _demo()
