# Technical Specification — KSP Crime Database Conversational AI

## Confirmed technical decisions
- **LLM layer**: Catalyst QuickML, self-hosted open-source model (no external API access) — used for intent extraction, SQL generation, narrative paraphrasing, and final-answer generation
- **Graph engine**: NetworkX, run inside a Catalyst Function — chosen over an external Neo4j instance specifically to stay within the "Catalyst-only deployment" mandate
- **Backend runtime**: Python, across all Catalyst Serverless Functions — matches the ML stack (NetworkX, SHAP, embeddings, SDV/Faker, pandas/numpy) without translation overhead
- **Frontend, two-tier**:
  - **Dev/test harness**: Streamlit app, local only, never deployed to Catalyst and not part of the submission — used to poke at each backend function directly as it comes online (schema browser, raw query runner, pipeline inspector) without waiting on the polished UI
  - **Production**: React SPA, hosted via Catalyst Slate / Web Client Hosting — this is the actual deployed, submitted frontend
- **Response format**: every answer returned as a structured envelope (`response_type`: card / chart / map / network / evidence / text, plus a data payload), not plain text — the frontend renders the matching visual component rather than a chat bubble
- **Mapping**: Leaflet + OpenStreetMap tiles, client-side only (Catalyst has no maps service) — still fully Catalyst-deployed since it's a frontend dependency, not external infrastructure
- **Network board rendering**: force-directed graph library (e.g. react-force-graph) rendering the NetworkX graph client-side, using generic avatar icons — never real or fake photorealistic photos of synthetic people
- **Evidence artifacts**: placeholder/stock video, audio, and document files linked via the `Evidence` table (see schema.md) and Catalyst Stratus — demonstrates retrieval/linking capability, not real forensic content analysis
- **Data scale assumption**: ~5,000–20,000 synthetic case records (see idea.md — Scope Decisions)

## Architecture overview

```
User (chat / voice)
   │
   ▼
Catalyst API Gateway
   │
   ▼
Stage 1: Intent Extraction (QuickML LLM)
   │  NL question → structured intent JSON
   │  {entities, filters, time_range, aggregation}
   ▼
Stage 2: Intent Verifier
   │  checks structured intent against original question
   │  → flags dropped/invented filters, ambiguity
   │  → triggers abstention/clarifying question if unresolved
   ▼
Schema-Constrained SQL Generator
   │  grammar-restricted to valid table/column names only
   ▼
Self-Consistency Check
   │  generate query twice, diff results → confidence signal
   ▼
Catalyst Data Store (execution)
   │
   ▼
Post-Execution Sanity Check
   │  validate result shape against expected bounds
   ▼
Answer Generation (QuickML LLM)
   │
   ▼
Entailment Check
   │  every claim in the NL answer verified against retrieved rows
   ▼
Response: answer + cited CaseMasterIDs + generated SQL + confidence score
```

## Catalyst service mapping

| Layer | Component | Catalyst Service |
|---|---|---|
| Frontend | React SPA | Catalyst Slate / Web Client Hosting |
| Backend orchestration | Intent parsing, verification, SQL execution | Catalyst Serverless (Functions), Python |
| Relational data | Full ER schema | Catalyst Data Store |
| Vector / similarity data | Case embeddings for similar-case search | Catalyst NoSQL |
| LLM serving | Intent extraction, generation, RAG | Catalyst QuickML |
| Risk scoring model | Tabular gradient boosting | Catalyst Zia AutoML |
| Voice + Kannada | STT, TTS, translation | Catalyst Zia Services |
| Auth | Role-based access | Catalyst Authentication |
| API layer | Routing/throttling | Catalyst API Gateway |
| PDF export | Conversation history export | Catalyst SmartBrowz |
| CI/CD | Deploy pipeline | Catalyst Pipelines |
| Graph analysis | NetworkX runtime | Catalyst Serverless (Functions), Python |

## Schema notes
The provided ER diagram is the base schema. Two tables are referenced in the Relationship Matrix but have no Table Definition and must be defined by us:
- **Inv_OccuranceTime** — 1:1 with CaseMaster (occurrence time/location detail record)
- **inv_arrestsurrenderaccused** — junction table for the ArrestSurrender ↔ Accused many-to-many relationship; this is the primary table the network/graph layer builds on

**Act/Section master data** must carry both legal codes: IPC (pre-1 July 2024 offences) and BNS (1 July 2024 onward), keyed off `CaseMaster.CrimeRegisteredDate`. Do not hardcode IPC-only sections.

## Synthetic data generation methodology
1. **Master/lookup tables first, no LLM involved**: State → District → Unit (using Karnataka's real, public administrative hierarchy) → Employee, Act/Section (IPC + BNS), CrimeHead/CrimeSubHead
2. **Statistical backbone for CaseMaster**: crime-type frequency, seasonal/day-of-week/hour patterns, and district-level volume calibrated against NCRB "Crime in India" published aggregate reports (public, non-case-level data) — generated via numpy/scipy, not an LLM
3. **Referential integrity via generation order**: CaseMaster → Victim/Accused/ComplainantDetails/ArrestSurrender → junction tables, following the FK graph in the Relationship Matrix
4. **LLM used only for `BriefFacts` narrative text**, and only as a paraphraser: a template filled from already-generated structured fields, with the LLM varying phrasing — never inventing a fact not already fixed in the row
5. **Reality-proximity guardrails**: no real FIR text/news/judgments as generation input; names via Faker (Indian locale); jittered lat/long within station jurisdiction bounds; CasteID/ReligionID sampled independently of crime outcome unless explicitly justified otherwise
6. **Validation pass**: CrimeNo format regex (1-digit category + 4-digit district + 4-digit station + 4-digit year + 5-digit serial), date-ordering checks (IncidentFromDate ≤ IncidentToDate ≤ InfoReceivedPSDate ≤ CrimeRegisteredDate ≤ csdate), orphan-FK scan, age plausibility
7. **Recommended tooling**: SDV (Synthetic Data Vault) for multi-table relational generation with FK-integrity preservation, layered on top of the statistical backbone

## Dependencies

**Frontend (Person A / teammate)**
- `react`, `react-dom` — core
- `react-leaflet` + `leaflet` — hotspot map (client-side, no Catalyst maps service exists)
- `react-force-graph-2d` (or `vis-network`) — investigation board rendering
- `recharts` — pattern/trend charts and dashboards
- `react-player` (or native `<video>`/`<audio>`) — evidence playback
- `axios` — API calls to Catalyst API Gateway
- Catalyst Web SDK — auth/session integration with Catalyst Authentication

**Backend (Person B / you), Python**
- `networkx` — graph/network analysis
- `shap` — risk score explanations
- `sdv` and/or `faker` — synthetic data generation
- `pandas`, `numpy` — data processing
- `scipy` — statistical distributions for the synthetic data backbone
- `pydantic` — structured intent JSON validation, schema-constrained parsing
- `jsonschema` — validating LLM output shape before it's trusted downstream
- Catalyst Python SDK — Functions, Data Store, NoSQL, QuickML, Stratus access

## Per-feature technical approach

**1. Conversational Interface** — React chat UI, Stage 1/2 pipeline above, session context held server-side per conversation, Zia Services for STT/TTS and Kannada translation, code-switch handling via language-detection pass before Stage 1, PDF export via SmartBrowz

**2. Network & Relationship Analysis** — NetworkX graph built from `inv_arrestsurrenderaccused` + `ArrestSurrender` + `CaseMaster`, multi-hop query support (e.g., co-accused across cases), rendered client-side as a node-link diagram

**3. Pattern & Trend Analytics** — aggregate query endpoints over CaseMaster (time, geography, crime type), hotspot detection via spatiotemporal clustering (not raw density heatmaps)

**4. Sociological Crime Insights** — correlation queries joining CaseMaster with ComplainantDetails demographic fields, presented with the independent-sampling caveat documented so correlations aren't misread as causal

**5. Offender Profiling** — feature set built from Accused + ArrestSurrender history, risk score via Zia AutoML gradient boosting, SHAP for feature importance, counterfactual generation ("risk drops if X changes")

**6. Investigator Decision Support** — automated case summary generation (LLM over structured case fields), similar-case retrieval via embedding search (Catalyst NoSQL) over BriefFacts + structured MO features

**7. Financial Crime & Transaction Link Analysis** — minimal invented schema (Account, Transaction, AccountCaseLink), one working demo query tracing a money trail; explicitly lighter depth than other features

**8. Crime Forecasting & Early Warning** — folded into the risk-scoring model rather than built as a separate pipeline; alerts are a threshold trigger on top of existing risk scores

**9. Explainable AI** — every answer ships with cited CaseMasterIDs, the generated SQL, and a confidence score derived from the self-consistency check and verifier agreement

**10. RBAC & Governance** — Catalyst Authentication with four roles (Investigator, Analyst, Supervisor, Policymaker) per the PS text, query audit log stored in Catalyst Data Store

**11. Dynamic Follow-Up Questions** — a small additional QuickML call, given the current answer + conversation history, returns 2-4 suggested next questions as structured JSON; frontend renders them as tappable buttons that resubmit as the next message. Not hardcoded, not a separate model.

**12. Entity Auto-Context Fetch** — when Stage 1 resolves a reference to an accused or victim, a parallel call pulls their profile (past cases, risk score, network position) and surfaces it as a sidecar card alongside the main answer — orchestration on top of existing profiling/similar-case infrastructure, not new ML.

**13. Investigation Board Visualization** — the NetworkX graph from feature 2, rendered client-side as a force-directed node-link board (avatars, not photos), triggered contextually from a case or entity in the conversation rather than as a standalone page.

**14. Evidence Linking** — retrieval and display of linked video/audio/image/document artifacts per case, backed by the `Evidence` table and Catalyst Stratus. Placeholder/stock content only — demonstrates the linking and playback capability, not real forensic analysis.

## Backend hallucination-reduction stack (detail)
- **Schema-constrained decoding**: SQL generation grammar-restricted to valid table/column names from the live schema — eliminates hallucinated fields structurally rather than catching them after generation
- **Self-consistency check**: same question run through Stage 1+2 twice at varied sampling settings; disagreement between the two runs becomes a visible confidence signal instead of being silently resolved
- **Post-execution sanity checks**: result shape validated against expected bounds (e.g., an aggregate returning zero rows where the question implies otherwise triggers a re-check) before the answer reaches the user
- **Entailment check on final NL answer**: a lightweight verifier confirms every claim in the generated prose is actually supported by the retrieved rows — applied at the output layer, same verification philosophy as the intent-verifier, one step later in the pipeline
