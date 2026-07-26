# Sample Questions — Verified Against the Live Backend

Every question below was POSTed live to `POST /api/query` against the running Catalyst local dev
server (`http://localhost:3000/server/datathon_2026_function/api/query`) on **2026-07-25 (Bengaluru
IST)** and confirmed to return a real, non-error, non-empty answer (`data.error` absent, `data.rows`
non-empty, a sane `confidence_score`). All confirmed answers came back as `response_type: "card"`.

`/api/query`'s pipeline only ever emits `"card"` (rows non-empty) or `"text"` (clarification/no-match/
error) — it never emits `chart`/`map`/`network`/`evidence`/`financial` today, so this list does not
invent categories the API doesn't actually support. Those other response types exist only on separate
GET endpoints (`/api/network/<id>`, `/api/similar-cases/<id>`, `/api/aggregates`, `/api/hotspots`,
`/api/entity-context/<id>` [Supervisor+], `/api/risk-score/<id>` [Supervisor+]) which are not driven by
free-text NL and so are out of scope for this "type a question" list.

**Answers may drift** if the underlying synthetic data is regenerated — counts here reflect the dataset
as it existed at verification time.

## Visual — guaranteed map or chart

Verified live on 2026-07-26 against the same running backend. "Visual-guaranteed" here means
the response reliably comes back as a `GenericRowsCard` map (rows carry a `Latitude`/`Longitude`
pair) — it does NOT mean the labels are always human-readable. Every `GROUP BY *_FK` question we
tried (`Top 5 crime categories in Ballari`, `Top 5 castes among complainants`, both already in
this file's existing "Top-N aggregates" section) comes back with raw FK integers as labels, e.g.
`CaseCategoryID_FK: 53418000000052190`, not names — see the root-cause note in the diagnostic
findings for this session; it's systemic to every grouping column ending in `_FK`, not specific
to case status. None of the chart-shaped ("top N by X") queries we tried return readable labels,
so this section only lists the map-shaped ones, which render cleanly regardless:

- `Show me case locations for mapping` (300 rows, lat/lon only)
- `Show the coordinates of registered cases` (300 rows, lat/lon only)
- `Where are cases located in Mysuru district` (70 rows, lat/lon + case detail columns)
- `Show case locations in Ballari district` (49 rows, lat/lon only)
- `Show case locations in Tumakuru district` (66 rows, lat/lon only)
- `Show me locations of murder cases` (149 rows, lat/lon only)
- `Show me locations of theft cases` (141 rows, lat/lon only)
- `Show me locations of robbery cases` (57 rows, lat/lon only)
- `Show me locations of dacoity cases` (66 rows, lat/lon only)
- `Show me locations of kidnapping cases` (173 rows, lat/lon only)

## Case totals and status

- `How many cases are there in total`
- `How many cases are Under Investigation`
- `How many cases have been charge sheeted`
- `How many cases are Closed`
- `How many cases have court hearings`
- `How many cases have been filed under FIR category`
- `How many cases are Charge Sheeted`

## Crime-type counts (no district filter)

- `How many cases involve robbery`
- `How many cases involve theft`
- `How many cases involve murder`
- `How many cases involve dacoity`
- `How many cases involve kidnapping`
- `How many cases involve dowry death`
- `How many cases involve POCSO offences`
- `How many cases involve NDPS offences`

## District-filtered case counts

- `How many cases were registered in Mysuru district`
- `How many cases were registered in Ballari district`
- `How many cases were registered in Tumakuru district`
- `Show cases in Ballari district`

## Crime-type + district combined counts

- `How many murder cases were registered in Ballari district`
- `How many murder cases were registered in Mysuru district`
- `How many theft cases were registered in Mysuru district`
- `How many robbery cases were registered in Mysuru district`
- `How many POCSO cases were registered in Mysuru district`
- `How many NDPS cases were registered in Ballari district`
- `How many dowry death cases were registered in Tumakuru district`
- `How many cases are Under Investigation in Mysuru district`
- `How many cases are Charge Sheeted in Ballari district`
- `How many cases have gravity offence marked heinous in Mysuru district`

## Top-N aggregates

- `Top 5 crime categories in Bengaluru City`
- `Top 5 crime categories in Bengaluru`
- `Top 5 crime categories by number of cases in Mysuru`
- `Top 5 crime categories in Mysuru district`
- `Top 5 crime categories in Ballari district`
- `Top 5 crime categories in Tumakuru district`
- `Top 5 case categories by count`
- `Top 5 castes among complainants`

## Gravity / offence severity

- `How many cases have a gravity offence marked heinous`
- `How many cases have a gravity offence marked non-heinous`

## People — accused, victims, employees

- `How many accused are there in total`
- `How many accused have age above 30`
- `How many victims are female`
- `How many victims are male`
- `How many employees are there`
- `How many acts are active`
- `How many police stations are there`

## Arrests and surrenders

- `How many arrest surrender events are there in total`
- `How many arrest surrender events are voluntary surrenders`
- `How many arrest events happened in Mysuru district`
- `How many arrest events happened in Ballari district`
- `How many arrest surrender events happened in Tumakuru district`

---

**Total verified working: 51 questions.**

## What failed and was dropped (for anyone extending this list)

Roughly 55 additional candidates were tried and dropped because they either errored or returned "no
matching records found":
- Any question needing a table/column not in the LLM's schema-constrained whitelist (e.g. `OccupationMaster`,
  `DesignationMaster`, `Caste` as a table name) — the plan fails validation with "references unknown table".
- Any question filtering a `BIT`/boolean column with a natural-language phrase (e.g. "arrests" vs
  "voluntary surrenders", "police officers", "primary accused", "inactive acts") — ZCQL rejects the
  literal the model guesses ("Invalid input value for X. Please give a correct boolean value").
- Plain listing questions with no filter and no aggregation keyword (e.g. "How many victims are there",
  "How many complainants are there", "Top 5 courts by case count") — these come back as an empty-row
  `text` response with confidence 0.0, i.e. the plan/verifier stage silently produces nothing usable.
- A few big-city ("Bengaluru City") + specific-offence combinations (kidnapping, dacoity, theft) that
  came back "No matching records were found" — plausibly correct if the synthetic data really doesn't
  have that offence/district combination, but not verifiable as non-empty so excluded here.
