# Response-Surface Router Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give `/api/query` a deterministic, rule-based classifier that decides which frontend surface an answer renders as — map, interactive accused-network board, main dashboard chart, evidence viewer, a full multi-panel **composite dashboard** (map + trend + crime-type breakdown + hotspots together, for broad "what's the state of crime in X" questions), or the default card/text — instead of the current hardcoded "card if rows else text", so the UI stops looking flat regardless of what was actually asked.

**Architecture:** A new pure-function module, `response_router.py`, combines two signal sources (what the executed plan/rows structurally contain, and what keywords the question uses) to pick a `response_type`. Five of the six values (`card`, `chart`, `map`, `network`, `evidence`, `text`) already exist in `QueryEnvelope`'s schema; a seventh, `dashboard`, is added for broad summary questions that need several visual panels at once rather than one. `pipeline.py`'s `run_query_pipeline` calls the classifier once after `execute_plan()` returns rows. For surfaces needing data the first-pass single-table plan wouldn't have fetched — map needs Latitude/Longitude, network needs a resolved accused/case id for `network.build_case_network`, dashboard needs several parallel aggregate queries — it performs bounded extra fetches (reusing `aggregates.py`'s already-built `get_aggregates`/`get_hotspots`, not new SQL-generation) before finalizing the envelope.

**Tech Stack:** Pure Python, stdlib `re` only. No new dependency. Follows this codebase's existing self-test convention (`_demo()` function with `assert` statements, run via `if __name__ == "__main__":`) rather than introducing pytest, since no other module in `functions/datathon_2026_function/` uses it.

## Global Constraints

- No LLM call anywhere in this classifier — fully rule-based, per explicit user instruction and CLAUDE.md's anti-hallucination stance (a guessed UI surface is still a hallucination).
- Must not alter `QueryEnvelope`'s existing five-field shape (`response_type`, `data`, `cited_case_ids`, `generated_sql`, `confidence_score`) — only widen the `response_type` Literal by one value (`dashboard`) and shape `data` to match whichever surface won.
- The `dashboard` surface must reuse `aggregates.get_aggregates`/`get_hotspots` (already-built, already-tested GET-endpoint logic) for its panels — never a new hand-written SQL plan per panel. Composing existing single-purpose functions, not inventing parallel plan-generation machinery, is what keeps this addition small.
- Must generalize past the 51 questions in `docs/sample_questions.md` — rules are keyword/structural, not a lookup table of known questions.
- No circular import: `response_router.py` must not import `QueryPlan`/`QueryStep` from `pipeline.py` (pipeline.py will import from `response_router.py`, so the reverse would be circular at load time). Use duck-typed `Any` for the plan parameter instead.
- Every new function gets a docstring stating *why*, not *what* — this codebase's actual convention (see `pipeline.py`, `aggregates.py`, `sos_alerts.py`) is a short paragraph when the reasoning needs it, not a strict one-liner; match that, don't compress a real rationale to fit an arbitrary line limit. Private one-line helpers with an obvious purpose from their name+signature (e.g. `_has_geo_columns`) may skip the docstring entirely.
- Follow the "never swallow an exception silently" rule from CLAUDE.md for the two extra-fetch paths (geo backfill, network lookup) — a failure there must degrade to the next-best surface (card) with a logged reason, not crash the whole `/api/query` response.

---

### Task 1: `response_router.py` — classifier module + self-check

**Files:**
- Create: `functions/datathon_2026_function/response_router.py`

**Interfaces:**
- Consumes: nothing from other new modules. Reads `list[dict[str, Any]]` row shapes (same shape `zcql_util.run` returns) and a duck-typed `plan` object whose only used attribute is `plan.steps[-1].group_by` (a string, empty when unset) — matches `pipeline.py`'s existing `QueryStep.group_by: str = ""`.
- Produces (used by Task 2):
  - `ResponseType = Literal["card", "chart", "map", "network", "evidence", "text"]`
  - `needs_geo_backfill(question: str, rows: list[dict[str, Any]]) -> bool`
  - `needs_network_lookup(question: str, rows: list[dict[str, Any]]) -> bool`
  - `needs_dashboard(question: str) -> bool`
  - `extract_district(question: str, known_districts: list[str]) -> str | None`
  - `classify(question: str, plan: Any, rows: list[dict[str, Any]]) -> ResponseType` (now returns `"dashboard"` as a 7th possible value)

- [ ] **Step 1: Write `response_router.py` with the keyword sets, helper predicates, and `classify()`**

```python
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
```

- [ ] **Step 2: Write the `_demo()` self-check at the bottom of the same file**

```python
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
```

- [ ] **Step 3: Run the self-check**

Run: `cd functions/datathon_2026_function && python response_router.py`
Expected output: `response_router._demo: all assertions passed`

- [ ] **Step 4: Byte-compile check**

Run: `cd functions/datathon_2026_function && python -m py_compile response_router.py`
Expected: no output, exit code 0.

- [ ] **Step 5: Commit**

```bash
git add functions/datathon_2026_function/response_router.py
git commit -m "feat: add rule-based response-surface classifier"
```

---

### Task 2: Wire the classifier into `pipeline.py`

**Files:**
- Modify: `functions/datathon_2026_function/pipeline.py:519-576` (the `run_query_pipeline` function's tail, from `rows = execute_plan(...)` through the final `return QueryEnvelope(...)`)

**Interfaces:**
- Consumes: `response_router.classify`, `response_router.needs_geo_backfill`, `response_router.needs_network_lookup` (Task 1). `network.build_case_network(case_id: int, zcql_service: Any) -> dict` — already exists, confirmed by its use in `main.py`'s `/api/network/<id>` route (returns a dict with a `case_ids` key, used there as `graph_data["case_ids"]`).
- Produces: `run_query_pipeline` now returns a `QueryEnvelope` whose `response_type` is `card`, `chart`, `map`, `network`, or `text` per `response_router.classify`, instead of always `card`/`text`. (`dashboard` and `evidence` classification only ever fires inside the `dashboard` early-exit branch added by Task 4, or when a genuine evidence-worded question with a resolved case id comes through this same path — `evidence` needs no separate wiring here since it needs no extra fetch, just the `classify()` call already added.)

This task does NOT yet handle `needs_dashboard(question)` — that's an early-exit *before* plan generation even runs, added separately in Task 4, since a dashboard question skips the single-table plan/execute_plan machinery entirely rather than trying to classify its output after the fact.

- [ ] **Step 1: Read the current tail of `run_query_pipeline` to confirm line numbers before editing**

Run: `sed -n '515,580p' functions/datathon_2026_function/pipeline.py`

Confirm this block is present (variable names must match exactly for the diff in Step 2 to apply):
```python
    rows = execute_plan(zcql_service, plan)
    sanity_confidence = sanity_check_results(rows, intent)

    answer = generate_answer(question, rows)
    entailed = entailment_check(answer, rows)
    if not entailed:
        # One retry with an explicit "stick to the rows" nudge, per
        # CLAUDE.md's entailment-must-pass-before-reaching-user rule.
        answer = generate_answer(
            question + " (Answer using ONLY the exact values in the rows, nothing else.)", rows,
        )
        entailed = entailment_check(answer, rows)

    answer = language.postprocess_answer(answer, detected_language)

    confidence = sanity_confidence * (1.0 if consistent else 0.6) * (1.0 if entailed else 0.4)

    cited_case_ids = sorted({
        int(r["CseMasterID"]) for r in rows if "CseMasterID" in r and str(r["CseMasterID"]).isdigit()
    })

    return QueryEnvelope(
        response_type="card" if rows else "text",
        data={"answer": answer, "rows": rows[:_MAX_RESULT_ROWS], "language": detected_language},
        cited_case_ids=cited_case_ids,
        generated_sql=render_plan_as_sql(plan),
        confidence_score=round(confidence, 3),
    )
```

- [ ] **Step 2: Add the import at the top of `pipeline.py`**

Add alongside the existing local imports (`import language`, `import quickml_client`, `import zcql_util`):
```python
import network
import response_router
```

`network` is already a sibling module in `functions/datathon_2026_function/` (imported today by `main.py`) — confirm with:
Run: `test -f functions/datathon_2026_function/network.py && echo exists`
Expected: `exists`

- [ ] **Step 3: Insert the geo-backfill and network-lookup steps between `execute_plan` and `sanity_check_results`**

Replace:
```python
    rows = execute_plan(zcql_service, plan)
    sanity_confidence = sanity_check_results(rows, intent)
```
with:
```python
    rows = execute_plan(zcql_service, plan)

    if (
        response_router.needs_geo_backfill(question, rows)
        and rows
        and plan.steps[-1].table == "CaseMaster"
        and not plan.steps[-1].group_by
    ):
        # First-pass plan didn't select Latitude/Longitude but the question
        # clearly wants a map -- patch the final step's select to include
        # them and re-run once. Only CaseMaster carries these columns
        # (schema_registry.ALLOWED_SCHEMA), so any other final table can't
        # be backfilled this way. Skipped when group_by is set -- appending
        # raw columns to a GROUP BY select is invalid SQL, and a grouped
        # aggregate query isn't map-shaped data anyway.
        geo_plan = plan.model_copy(deep=True)
        base_select = geo_plan.steps[-1].select.strip()
        if "Latitude" not in base_select:
            geo_plan.steps[-1].select = f"{base_select}, Latitude, Longitude"
        try:
            geo_rows = execute_plan(zcql_service, geo_plan)
        except PipelineError as e:
            logging.getLogger().warning(f"geo backfill failed, keeping original rows: {e}")
        else:
            plan, rows = geo_plan, geo_rows

    network_data: dict[str, Any] | None = None
    if response_router.needs_network_lookup(question, rows):
        first_case_id = next(
            (int(r[col]) for r in rows for col in ("CseMasterID", "CaseMasterID_FK") if col in r and str(r[col]).isdigit()),
            None,
        )
        if first_case_id is not None:
            try:
                network_data = network.build_case_network(first_case_id, zcql_service)
            except Exception as e:  # noqa: BLE001 -- degrade to the next-best surface, never crash /api/query
                logging.getLogger().warning(f"network lookup failed, falling back: {e}")

    sanity_confidence = sanity_check_results(rows, intent)
```

- [ ] **Step 4: Add the `logging` import if not already present**

Run: `grep -n "^import logging" functions/datathon_2026_function/pipeline.py`

If no match, add `import logging` to the top-of-file import block (alongside `import json`, `import re`).

- [ ] **Step 5: Replace the final `return QueryEnvelope(...)` block to use the classifier and shape `data` per surface**

Replace:
```python
    cited_case_ids = sorted({
        int(r["CseMasterID"]) for r in rows if "CseMasterID" in r and str(r["CseMasterID"]).isdigit()
    })

    return QueryEnvelope(
        response_type="card" if rows else "text",
        data={"answer": answer, "rows": rows[:_MAX_RESULT_ROWS], "language": detected_language},
        cited_case_ids=cited_case_ids,
        generated_sql=render_plan_as_sql(plan),
        confidence_score=round(confidence, 3),
    )
```
with:
```python
    cited_case_ids = sorted({
        int(r["CseMasterID"]) for r in rows if "CseMasterID" in r and str(r["CseMasterID"]).isdigit()
    })

    response_type = response_router.classify(question, plan, rows)
    data: dict[str, Any] = {"answer": answer, "rows": rows[:_MAX_RESULT_ROWS], "language": detected_language}
    if response_type == "network":
        if network_data is not None:
            data["network"] = network_data
            cited_case_ids = sorted(set(cited_case_ids) | set(network_data.get("case_ids", [])))
        else:
            response_type = "card"  # lookup failed or no resolvable case id -- degrade, don't crash

    return QueryEnvelope(
        response_type=response_type,
        data=data,
        cited_case_ids=cited_case_ids,
        generated_sql=render_plan_as_sql(plan),
        confidence_score=round(confidence, 3),
    )
```

- [ ] **Step 6: Byte-compile check**

Run: `cd functions/datathon_2026_function && python -m py_compile pipeline.py`
Expected: no output, exit code 0.

- [ ] **Step 7: Run `response_router.py`'s self-check again (regression guard — Task 2 must not have broken Task 1's contract)**

Run: `cd functions/datathon_2026_function && python response_router.py`
Expected output: `response_router._demo: all assertions passed`

- [ ] **Step 8: Commit**

```bash
git add functions/datathon_2026_function/pipeline.py
git commit -m "feat: wire response-surface classifier into /api/query pipeline"
```

---

### Task 3: Static generalization check against `docs/sample_questions.md`

**Files:**
- Create (temporary, not committed): none — this is a read-only verification task run from the shell.

**Interfaces:**
- Consumes: `response_router._any_keyword`, `response_router._MAP_KEYWORDS`, `response_router._NETWORK_KEYWORDS`, `response_router._CHART_KEYWORDS`, `response_router._EVIDENCE_KEYWORDS` (Task 1) and the question list embedded in `docs/sample_questions.md`.
- Produces: a pass/fail confirmation that none of the 51 already-verified questions in `docs/sample_questions.md` accidentally trip the network/chart/evidence keyword sets (which would change their documented `card`/`map` behavior without a corresponding structural signal to justify it — a regression, since those 51 were hand-verified live and their existing behavior is the known-good baseline).

- [ ] **Step 1: Write a one-off check script**

Create `functions/datathon_2026_function/_check_sample_questions.py` (temporary — deleted in Step 3, not committed):
```python
"""One-off static check: none of docs/sample_questions.md's 51 hand-verified
questions should trip the network/chart/evidence keyword sets without also
being one of the already-documented map-shaped ones -- a keyword-only false
positive here would silently change a known-good question's response_type
with no structural signal backing it up.
"""
import re

import response_router

with open("../../docs/sample_questions.md", encoding="utf-8") as f:
    text = f.read()

questions = re.findall(r"^- `([^`]+)`", text, re.MULTILINE)
assert len(questions) >= 51, f"expected >=51 questions, found {len(questions)}"

map_section_questions = set(re.findall(r"^- `([^`]+)`.*$", text.split("## Case totals")[0], re.MULTILINE))

unexpected = []
for q in questions:
    is_map_listed = q in map_section_questions
    if response_router._any_keyword(q, response_router._NETWORK_KEYWORDS):
        unexpected.append((q, "network"))
    if response_router._any_keyword(q, response_router._EVIDENCE_KEYWORDS):
        unexpected.append((q, "evidence"))
    if response_router._any_keyword(q, response_router._CHART_KEYWORDS):
        unexpected.append((q, "chart"))
    if response_router._any_keyword(q, response_router._MAP_KEYWORDS) != is_map_listed:
        unexpected.append((q, f"map-mismatch (keyword_hit={not is_map_listed})"))

if unexpected:
    print("UNEXPECTED KEYWORD HITS:")
    for q, kind in unexpected:
        print(f"  [{kind}] {q}")
else:
    print(f"All {len(questions)} sample questions classify with no unexpected keyword hits.")
```

- [ ] **Step 2: Run it**

Run: `cd functions/datathon_2026_function && python _check_sample_questions.py`
Expected: `All 51 sample questions classify with no unexpected keyword hits.`

If it prints `UNEXPECTED KEYWORD HITS`, inspect each listed question: either the keyword set is too broad (tighten it in `response_router.py`'s `_NETWORK_KEYWORDS`/`_EVIDENCE_KEYWORDS`/`_CHART_KEYWORDS`/`_MAP_KEYWORDS`) or the question genuinely should now classify differently (rare — only if the question text itself contains a word like "district" triggering `_CHART_KEYWORDS`'s `"by district"`; if so, narrow that phrase to require the full `"by district"` substring, not just `"district"`, which the current set already does correctly — verify no accidental partial match before deciding to change anything).

- [ ] **Step 3: Delete the temporary script (it is not a permanent test — Task 1's `_demo()` is the permanent regression guard)**

Run: `rm functions/datathon_2026_function/_check_sample_questions.py`

- [ ] **Step 4: Confirm no stray file remains**

Run: `git status --porcelain functions/datathon_2026_function/_check_sample_questions.py`
Expected: no output (file gone, nothing to commit).

---

### Task 4: Composite `dashboard` surface for broad "state of crime" questions

A single GROUP BY query can't honestly answer "what's the state of crime in Mysuru" — that needs several panels at once (trend over time, crime-type breakdown, geographic hotspots) shown together, not one chart. This task adds an early-exit branch in `run_query_pipeline` that skips the normal single-table plan entirely for these questions and assembles a composite from `aggregates.py`'s already-built, already-tested `get_aggregates`/`get_hotspots` functions.

**Files:**
- Modify: `functions/datathon_2026_function/pipeline.py` — add imports, a module-level district-name cache, a new `_build_dashboard_envelope` function, and the early-exit branch in `run_query_pipeline`.

**Interfaces:**
- Consumes: `response_router.needs_dashboard(question: str) -> bool`, `response_router.extract_district(question: str, known_districts: list[str]) -> str | None` (Task 1). `aggregates.get_aggregates(zcql_service, agg_type, date_from, date_to, crime_type) -> dict` and `aggregates.get_hotspots(zcql_service, date_from, date_to, crime_type, eps_degrees=0.05, min_samples=3) -> dict` — both already exist and are already used by `main.py`'s `/api/aggregates` and `/api/hotspots` routes; `get_aggregates(..., "geography", ...)` returns `{"type": "geography", "series": [{"district": str, "count": int}, ...]}` and `get_hotspots(...)` returns `{"clusters": [{"lat": float, "lon": float, "count": int, "score": float, "district": str, "crime_type": str, "case_ids": list[int]}, ...]}` (confirmed from `aggregates.py`'s own `_demo()` self-check assertions).
- Produces: `run_query_pipeline` returns a `QueryEnvelope` with `response_type="dashboard"` and `data` shaped as:
  ```python
  {
      "answer": str,
      "district": str | None,           # resolved scope, or None for state-wide
      "trend": list[dict],              # [{"month": "2024-01", "count": 12}, ...]
      "crime_type_breakdown": list[dict],  # [{"crime_type": "...", "count": N}, ...]
      "hotspots": list[dict],           # filtered cluster list, same shape as get_hotspots
      "language": str,
  }
  ```
  for any question `response_router.needs_dashboard` matches, before the normal card/chart/map/network/text path ever runs.

- [ ] **Step 1: Confirm `aggregates.py`'s function signatures and return shapes match what this task assumes**

Run: `grep -n "^def get_aggregates\|^def get_hotspots" functions/datathon_2026_function/aggregates.py`
Expected:
```
def get_aggregates(
def get_hotspots(
```
Then re-read `aggregates.py`'s `_demo()` function (already in the file) to confirm the exact keys used in the assertions (`series`, `month`, `crime_type`, `district`, `clusters`, `count`) match the shapes documented above — if `aggregates.py` has changed since this plan was written, update the shapes in this task's docstrings to match reality before writing code against them.

- [ ] **Step 2: Add the district-name cache and imports to `pipeline.py`**

Add near the top of `pipeline.py`, alongside the other module-level state (there is none yet in this file besides constants — add this as a new small block after `_MAX_RESULT_ROWS = 500`):
```python
import aggregates

_district_names_cache: list[str] | None = None


def _get_district_names(zcql_service: Any) -> list[str]:
    """Cached at first use, same one-query-then-reuse pattern as
    risk_model.py's _model_cache -- district names don't change within a
    function's warm lifetime, so re-fetching per request would be a
    wasteful repeated query for a value that's effectively static."""
    global _district_names_cache
    if _district_names_cache is None:
        rows = zcql_util.run(zcql_service, "SELECT DistrictName FROM District")
        _district_names_cache = [r["DistrictName"] for r in rows if r.get("DistrictName")]
    return _district_names_cache
```

- [ ] **Step 3: Write `_build_dashboard_envelope`**

Add this function directly above `run_query_pipeline`:
```python
def _build_dashboard_envelope(question: str, zcql_service: Any, detected_language: str) -> QueryEnvelope:
    """Assembles the multi-panel 'state of crime' composite from
    aggregates.py's existing single-purpose functions rather than
    generating a new SQL plan -- a broad summary question is really three
    already-solved narrower questions (trend, crime-type breakdown,
    hotspots) asked at once, not a new query-generation problem."""
    known_districts = _get_district_names(zcql_service)
    district = response_router.extract_district(question, known_districts)

    trend = aggregates.get_aggregates(zcql_service, "trend", None, None, None)["series"]
    crime_type_breakdown = aggregates.get_aggregates(zcql_service, "crime-type", None, None, None)["series"]
    hotspots = aggregates.get_hotspots(zcql_service, None, None, None)["clusters"]

    if district:
        hotspots = [c for c in hotspots if c.get("district", "").lower() == district.lower()]

    summary_rows = [
        {"panel": "trend", "data": trend[:12]},
        {"panel": "crime_type_breakdown", "data": crime_type_breakdown[:10]},
        {"panel": "hotspots", "data": hotspots[:10]},
    ]
    scope_phrase = f" in {district}" if district else " statewide"
    answer = generate_answer(f"{question} (summarize the crime picture{scope_phrase})", summary_rows)
    entailed = entailment_check(answer, summary_rows)
    if not entailed:
        answer = generate_answer(
            f"{question} (Answer using ONLY the exact values in the rows, nothing else.)", summary_rows,
        )
        entailed = entailment_check(answer, summary_rows)
    answer = language.postprocess_answer(answer, detected_language)

    all_case_ids = sorted({cid for c in hotspots for cid in c.get("case_ids", [])})
    confidence = 1.0 if (trend and crime_type_breakdown) else 0.6
    confidence *= 1.0 if entailed else 0.4

    return QueryEnvelope(
        response_type="dashboard",
        data={
            "answer": answer,
            "district": district,
            "trend": trend,
            "crime_type_breakdown": crime_type_breakdown,
            "hotspots": hotspots,
            "language": detected_language,
        },
        cited_case_ids=all_case_ids,
        generated_sql="",  # composite of pre-built aggregate/hotspot queries, not one plan -- see aggregates.py for those
        confidence_score=round(confidence, 3),
    )
```

- [ ] **Step 4: Add the early-exit branch in `run_query_pipeline`, immediately after intent verification and before plan generation**

Replace:
```python
    plan, consistent = generate_plan_with_self_consistency(question, intent)
    validate_plan(plan)  # re-validate the chosen candidate, not just both branches above
```
with:
```python
    if response_router.needs_dashboard(question):
        return _build_dashboard_envelope(question, zcql_service, detected_language)

    plan, consistent = generate_plan_with_self_consistency(question, intent)
    validate_plan(plan)  # re-validate the chosen candidate, not just both branches above
```

- [ ] **Step 5: Update `QueryEnvelope`'s `response_type` Literal to include `"dashboard"`**

Find (near the top of `pipeline.py`, in the `QueryEnvelope` class):
```python
class QueryEnvelope(BaseModel):
    response_type: Literal["card", "chart", "map", "network", "evidence", "text"]
```
Replace with:
```python
class QueryEnvelope(BaseModel):
    response_type: Literal["card", "chart", "map", "network", "evidence", "text", "dashboard"]
```

- [ ] **Step 6: Byte-compile check**

Run: `cd functions/datathon_2026_function && python -m py_compile pipeline.py`
Expected: no output, exit code 0.

- [ ] **Step 7: Write and run a mocked integration check (no live ZCQL/QuickML — confirms the branch wires together, not that live data is correct)**

Create `functions/datathon_2026_function/_check_dashboard.py` (temporary — deleted in Step 9, not committed):
```python
"""One-off wiring check: run_query_pipeline's dashboard branch assembles a
QueryEnvelope with response_type='dashboard' and all four panels present,
using fakes for both ZCQL and QuickML so no live service is needed. This
confirms the plumbing, not real crime data -- run the live version in
docs/sample_questions.md's style once the local Catalyst server is up.
"""
import pipeline


class _FakeZcql:
    def execute_query(self, sql: str):
        if "District" in sql and "DistrictName" in sql:
            return [{"DistrictName": "Mysuru"}, {"DistrictName": "Ballari"}]
        if "FROM CaseMaster" in sql:
            return [
                {"ROWID": 1, "CseMasterID": 1, "CrimeRegisteredDate": "2024-01-15", "Latitude": 12.9, "Longitude": 77.5, "GravityOffenceID": 1, "CrimeMajorHeadID_FK": 1, "PoliceStationID_FK": 1},
            ]
        if "FROM CrimeHead" in sql:
            return [{"ROWID": 1, "CrimeGroupName": "Crimes Against Body"}]
        if "FROM Unit" in sql:
            return [{"ROWID": 1, "DistrictID_FK": 1}]
        if "FROM District" in sql:
            return [{"ROWID": 1, "DistrictName": "Mysuru"}]
        return []


def _fake_chat(messages, **kwargs):
    system = messages[0]["content"]
    if "Extract structured intent" in system:
        return '{"entities": ["Mysuru"], "filters": {}, "time_range": null, "aggregation": null}'
    if "check whether an extracted intent" in system.lower():
        return '{"match": true}'
    if "Answer the user" in system:
        return "Crime in Mysuru shows a steady trend with body crimes most common."
    if "Check whether every factual claim" in system:
        return '{"entailed": true}'
    raise AssertionError(f"unexpected prompt in dashboard check: {system!r}")


pipeline.quickml_client.chat = _fake_chat
pipeline.language.detect_language = lambda text: "en"

envelope = pipeline.run_query_pipeline("What is the state of crime in Mysuru", _FakeZcql())
assert envelope.response_type == "dashboard", envelope.response_type
assert "trend" in envelope.data and "crime_type_breakdown" in envelope.data and "hotspots" in envelope.data
assert envelope.data["district"] == "Mysuru", envelope.data["district"]
print("dashboard wiring check: all assertions passed")
```

- [ ] **Step 8: Run it**

Run: `cd functions/datathon_2026_function && python _check_dashboard.py`
Expected: `dashboard wiring check: all assertions passed`

If it fails on the fake QuickML prompt matching (`unexpected prompt in dashboard check`), read the actual system prompt text it printed and adjust the `_fake_chat` `if` conditions in Step 7 to match `pipeline.py`'s real `_INTENT_SYSTEM_PROMPT`/`_VERIFIER_SYSTEM_PROMPT`/`_ANSWER_SYSTEM_PROMPT`/`_ENTAILMENT_SYSTEM_PROMPT` wording exactly — this is a wiring check, not a prompt-content check, so keep the fakes lenient (substring match) rather than trying to replicate the real prompts word for word.

- [ ] **Step 9: Delete the temporary check script**

Run: `rm functions/datathon_2026_function/_check_dashboard.py`
Run: `git status --porcelain functions/datathon_2026_function/_check_dashboard.py`
Expected: no output.

- [ ] **Step 10: Run response_router.py's self-check once more (final regression guard for this plan)**

Run: `cd functions/datathon_2026_function && python response_router.py`
Expected output: `response_router._demo: all assertions passed`

- [ ] **Step 11: Commit**

```bash
git add functions/datathon_2026_function/pipeline.py
git commit -m "feat: add composite dashboard surface for broad state-of-crime questions"
```

---

## Post-plan note for the next session

Two items from the earlier ZCQL-compliance audit still need a **live** Catalyst call to resolve (documented in `pipeline.py`'s comments but not verifiable offline in this environment):
1. Whether `District`/`Unit`/etc.'s Catalyst-assigned `ROWID` actually equals the CSV-imported `_FK` integer values other tables store to reference them (the single highest-risk unverified assumption in the whole pipeline).
2. Whether ZCQL's `'YYYY-MM-DD'` date-literal format also works unmodified for DATETIME columns (`IncidentFromDate`, `InfoRecievedPSDate`, `csdate`), or needs a time component.

Run both checks against the live/local Catalyst function before the demo — not part of this plan since neither can be scripted without live access.

Third item: `docs/sample_questions.md` states `/api/query` has only ever emitted `card`/`text` in practice so far — this plan makes `chart`/`map`/`network`/`evidence`/`dashboard` real possibilities for the first time. This is a **backend-only** plan (response_type + data shape); the React frontend needs a renderer for each new `response_type` value (a map component, the accused-network board, chart panels, a 4-panel dashboard layout) before these are visible to a user — confirm with whoever owns the frontend whether those renderers already exist or need building, since this plan does not build them.
