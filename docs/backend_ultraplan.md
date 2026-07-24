# Backend Ultraplan — Phases 0–21 (Person B / you)

## Context

This is the KSP Crime Database Conversational AI project (Zoho Catalyst Datathon 2026, PS1). Team of two: you (Person B) own all backend + architecture, your teammate (Person A) owns all frontend. `docs/implementation.md` defines 24 phases; this doc consolidates **every backend deliverable through Phase 21** — including the backend half of phases nominally owned by Person A — into one build-order plan, so you can work from this single doc instead of re-deriving context each session. Phase 22 (Self Red-Team Test Suite) is the natural next phase after this scope but is intentionally excluded here since it wasn't asked for — pick it up as a follow-up once 0–21 are solid.

**Resolved while planning (confirmed with you):**
- `implementation.md`'s phase numbers are authoritative. `schema.md` and `CLAUDE.md` contain stale phase-number references from an earlier renumbering (schema.md tags financial-crime as "Phase 15", RBAC as "Phase 13", risk-scoring as "Phase 11", conversation tables as "Phase 5, 16" — the real numbers per implementation.md are 19, 17, 15, and 7-10/21 respectively). **This is a real doc-drift bug, not resolved here** — flag it as a cleanup task, don't silently rewrite the docs.
- Phases 17 (RBAC/audit), 19 (financial crime), and 21 (PDF export) are labeled "Owner: Person A" in implementation.md but each needs real backend logic (audit-log writes, a demo query, conversation-history assembly). Those backend pieces are included below; Person A builds only the UI on top.

## Current repo status (checked before writing this plan)

| Phase | Deliverable | Status |
|---|---|---|
| 0 | Catalyst scaffold | Done — `catalyst.json`, `.catalystrc`, `functions/datathon_2026_function/` exist |
| 1 | Schema finalization | Done — `schema.md` confirmed against `iac:export` 2026-07-20, naming-drift table captured |
| 2 | Streamlit harness | Scaffolded only — `streamlit_harness/app.py` (97 lines) + `catalyst_client.py` (43 lines). Needs a panel added per new Function as it ships |
| 3 | Synthetic data pipeline | Built — `data_generation/pipeline.py` orchestrates lookups → case_master → case_children → financial → app_layer via real `ds:import`/`ds:export`. `validate.py` exists. **Unverified: a full end-to-end run has actually completed and passed validation at scale.** `case_count=2000`, deliberately scaled down from the 5k–20k target in idea.md — revisit before final submission |
| 4 | BriefFacts narratives | **Not done.** `generators/narratives.py` (251 lines) exists as a starting point but the phase isn't complete — only Phase 3 is confirmed done. Finish the template + QuickML paraphrase pass and spot-check fact-faithfulness before moving on |
| 5–21 | Everything else | **Not started.** `functions/datathon_2026_function/main.py` is still the literal "Hello from main.py" scaffold stub |

Also already built and reusable: `generators/evidence.py` (Evidence table + Stratus `evidences` bucket referenced), `generators/financial.py` (Account/Transaction/AccountCaseLink), `generators/app_layer.py` (AppRole/AppUser/ConversationSession/ConversationMessage/AuditLog/RiskScore synthetic seed data). These are **data generators**, not live endpoints — don't confuse a generator that seeds `RiskScore` with synthetic ground truth for the Phase 15 live SHAP inference endpoint; they're different things.

## The core architectural decision

Phases 5 and 6, plus the self-consistency/sanity/entailment steps `technical.md` specifies as mandatory pipeline stages (not optional), collapse into **one orchestrating endpoint**: `POST /api/query`. This is "the endpoint" — Stage 1 (intent extraction) → Stage 2 (verifier) → schema-constrained SQL generation → self-consistency check → execute against Data Store → post-execution sanity check → answer generation → entailment check, all server-side in one Catalyst Function call, per the pipeline diagram in `technical.md`. Person A's Phase 7 chat shell calls this one endpoint and gets back the full structured envelope. Later phases either extend this envelope (Phase 10 follow-ups, Phase 9 explainability fields) or add sibling endpoints that plug into the same envelope shape (Phase 11 network, Phase 15 risk, Phase 16 aggregates, etc.).

**Response envelope** (pin this down as a pydantic model immediately — it's the wire contract Person A's Phase 8 rendering framework builds against, so define it before Phase 5/6 is fully done, not after):
```
{
  response_type: "card" | "chart" | "map" | "network" | "evidence" | "text",
  data: {...},                    # shape depends on response_type
  cited_case_ids: [int],
  generated_sql: str,
  confidence_score: float,
  follow_up_questions: [str]      # added in Phase 10, optional until then
}
```

## Recommended build order (dependency-driven, not phase-number order)

1. **Finish Phase 4 — BriefFacts Narrative Generation** before anything else below. Only Phase 3 is confirmed complete; Phase 4 is still open. Template generator + QuickML paraphrasing pass producing BriefFacts text for all cases, spot-checked for fact-faithfulness. Phase 5 depends on Phase 3's structured data and QuickML being live, but doing Phase 4 first keeps the data pipeline fully closed out before moving into the conversational pipeline.
2. **Envelope contract** — write the pydantic model above, share with Person A immediately so Phase 8 can start in parallel with your Phase 5/6 work.
4. **Phase 5 — Intent Extraction**: Function, NL question → structured intent JSON (`{entities, filters, time_range, aggregation}`) via QuickML, `pydantic`-validated. Test via ~20-question sample set through the Streamlit harness.
5. **Phase 6 — Verifier + SQL Gen**: extends the same pipeline — intent/question mismatch verifier triggering clarifying questions, schema-constrained SQL generator (grammar-restricted to live `schema.md` fields, never free-text). Ship even a stub `/api/query` fast — Phase 7 is blocked waiting on it.
6. Self-consistency check, post-execution sanity check, entailment check — these are mandatory pipeline steps per `CLAUDE.md`, not add-ons; build them into `/api/query` before calling Phase 6 "done."
7. **Phase 10 — Follow-up questions**: cheap add-on, extend `/api/query`'s response with a small QuickML call filling `follow_up_questions`. No new endpoint needed.
8. **Phase 11 — Network & Graph Analysis**: NetworkX over `inv_arrestsurrenderaccused` (already populated once Phase 3's pipeline has run). New response path with `response_type: "network"`.
9. **Phase 13 — Similar-Case Retrieval**: needs an embedding backfill step first (BriefFacts + MO features → Catalyst NoSQL `CaseEmbedding`-style records per `schema.md`) — add this as a new stage in `data_generation/pipeline.py`, same pattern as the existing table groups. Then a retrieval endpoint/response path.
10. **Phase 14 — Entity Auto-Context**: depends on 8 + 9 above. Parallel call fired whenever Stage 1 resolves an accused/victim reference; expose both as an internal helper inside `/api/query` and a standalone `/api/entity-context/{accused_id}` for sidecar refresh.
11. **Phase 15 — Risk Scoring, SHAP, Counterfactuals**: needs Zia AutoML configured + a labeled synthetic offender feature set built from `Accused` + `ArrestSurrender` history (data already exists). New endpoint `/api/risk-score/{accused_id}`, writes results into the `RiskScore` table's `TopFeaturesJSON`/`CounterfactualJSON` columns (schema already has them).
12. **Phase 16 — Aggregate endpoints + hotspots**: `/api/aggregates` (trend/geography/crime-type over `CaseMaster`) and `/api/hotspots` (spatiotemporal clustering, not raw density) feeding Person A's Leaflet map.
13. **Phase 17 — RBAC & Audit (backend half)**: role-scope enforcement via Catalyst Authentication wrapping every Function, plus an `AuditLog` row written on every query (`QueryText`, `GeneratedSQL`, `Timestamp`, `ResultRowCount`) — hook into `/api/query`'s completion path.
14. **Phase 19 — Financial Crime (backend half)**: schema + synthetic data already done (`financial.py`). Add one demo endpoint/response path tracing a money trail linked to a case — deliberately minimal per `idea.md`, don't over-build.
15. **Phase 20 — Evidence Linking (backend half)**: `/api/evidence/{case_id}` returning linked artifact URLs from Stratus. Confirm the open TODO in `pipeline.py` (Stratus upload flow for `evidence.py`'s placeholder files) is actually resolved — don't mark this done until FileURL values are verified real, not assumed.
16. **Phase 21 — PDF Export (backend half)**: `/api/conversation/{session_id}/export` assembling `ConversationMessage` history for SmartBrowz. Requires live conversation logging — a `ConversationMessage` row written per real turn during `/api/query`, not just the synthetic seed data `app_layer.py` currently generates.
17. **Phase 18 — Kannada/Voice** (whoever's free first): STT/TTS/translation via Zia Services, language-detection pass ahead of Stage 1, code-switch routing. If it lands on you, it's a preprocessing addition in front of `/api/query`, not a new pipeline.

Phases 2 (harness) and the doc-drift cleanup run continuously alongside all of the above, not as one-time steps.

## Verification approach

- Every new Function: exercise it through the Streamlit harness (raw-query panel + a panel per pipeline stage) before considering it done — per `CLAUDE.md`, don't wait on the React frontend to sanity-check backend work.
- Validate every response against the pydantic envelope model + `jsonschema` before it's trusted as "shaped correctly."
- Phase 5/6: run the ~20-question sample set and confirm clarifying-question triggering on ambiguous input, not just the happy path.
- Phase 3: re-run `data_generation/validate.py`'s full report (FK integrity, CrimeNo regex, date ordering) after any generator change, and confirm the full pipeline (`python -m data_generation.pipeline`) completes end-to-end at least once before treating Phase 3 as closed.
- Write a test alongside the schema-constrained decoder, verifier, self-consistency check, and entailment check specifically — these are the differentiators that get adversarially probed later (Phase 22), so they need to hold up under bad input now, not just pass a demo run.

## Open flags (don't resolve silently — revisit explicitly)

- `schema.md`/`CLAUDE.md` phase-number drift (see Context) — needs an actual doc edit pass, not covered by this plan.
- Phase 3's `case_count=2000` vs the 5k–20k target in `idea.md` — decide before final data generation run.
- `pipeline.py`'s unresolved `--config` bucket-key TODO for non-interactive `ds:import` — currently works only because there's a single Stratus bucket; will break if a second bucket is ever added.
- Confirm Phase 4's narrative generation actually calls QuickML (not just templates) before marking it done.