# Implementation Plan — Phase by Phase

Phases are intentionally small. Each has a clear owner, what it needs before it can start, and what "done" looks like.

**Confirmed team split**: Person B (you) owns all backend and architecture. Person A (teammate) owns all frontend. Unlike earlier drafts, this is no longer a starting assumption — it's the actual division. Worth naming the risk that comes with it: each side is now a single point of failure with no overlap. If Person A hits a wall on the network-board rendering or the map integration, there's no backup — plan slack time accordingly, especially since Person A's load has grown with this round of additions (dashboard rendering, video/audio players, force-directed graph board, map integration, dynamic structured-response rendering, on top of everything already planned).

**Two-tier frontend note**: a throwaway Streamlit app is used during development purely for fast internal testing of backend pieces. It is never deployed to Catalyst and is not part of the submission. The React app is the actual deployed, submitted product.

**Hard rule**: Phase 23 (deployment integration) is a feature freeze. Nothing new starts after it, regardless of what's left on the list. Phase 24 (packaging) gets the final day, protected, no exceptions.

---

### Phase 0 — Environment & Catalyst Setup
**Owner**: Both
**Requirements**: Catalyst account created, datathon credits claimed
**Deliverables**: Catalyst project scaffolded (Functions, Data Store, NoSQL, QuickML, Stratus enabled), GitHub repo initialized, both members have local dev access and can deploy a "hello world" function

### Phase 1 — Schema Finalization
**Owner**: Person B
**Requirements**: Phase 0 complete; original ER diagram; schema.md
**Deliverables**: Full DDL for Catalyst Data Store, including `Inv_OccuranceTime`, `inv_arrestsurrenderaccused`, and the Evidence table; schema loaded into Catalyst Data Store empty

### Phase 2 — Streamlit Dev/Test Harness
**Owner**: Person B
**Requirements**: Phase 0 complete; Phase 1 schema available for reference
**Deliverables**: A local Streamlit app (not deployed, internal tool only) with a schema browser, a panel to inspect synthetic data, a raw-query runner hitting Catalyst Functions directly as they come online, and a panel to fire test questions at the pipeline and see raw JSON/SQL/results. Used continuously through Phase 22; retired at the Phase 23 freeze.

### Phase 3 — Synthetic Data Generation Pipeline
**Owner**: Person B
**Requirements**: Phase 1 schema; NCRB aggregate reference stats; Faker/SDV installed
**Deliverables**: Scripts generating lookup tables, CaseMaster, and all child tables; validation report passing (FK integrity, CrimeNo regex, date ordering); dataset loaded into Catalyst Data Store; spot-checkable via the Phase 2 harness

### Phase 4 — BriefFacts Narrative Generation
**Owner**: Person B
**Requirements**: Phase 3 structured data; QuickML LLM deployed
**Deliverables**: Template-based narrative generator + LLM paraphrasing pass producing BriefFacts text for all cases; spot-checked sample for fact-faithfulness

### Phase 5 — Stage 1: Intent Extraction
**Owner**: Person B
**Requirements**: QuickML LLM access; schema reference document
**Deliverables**: Function taking NL question → structured intent JSON; tested against a sample query set of ~20 questions via the Streamlit harness

### Phase 6 — Stage 2: Verifier + Schema-Constrained SQL Generation
**Owner**: Person B
**Requirements**: Phase 5 output; live schema
**Deliverables**: Verifier function flagging intent/question mismatches and triggering clarifying questions on ambiguity; SQL generator constrained to valid schema fields

### Phase 7 — Production React Frontend (Chat UI Shell)
**Owner**: Person A
**Requirements**: Phase 0 complete; Phases 5–6 have a working API to call
**Deliverables**: The base deployable chat interface, calling the pipeline through API Gateway — plain but functional, this is the frontend that ships in the submission

### Phase 8 — Rich Response Rendering Framework
**Owner**: Person A
**Requirements**: Phase 7 shell working
**Deliverables**: Every backend answer arrives as a structured envelope (`response_type`: card/chart/map/network/evidence/text + data payload); the frontend renders the matching component instead of a plain text bubble. This is the foundation every later visual feature (Phases 12, 14, 16) plugs into — build it once, reuse everywhere.

### Phase 9 — Explainability Layer
**Owner**: Person A (with Person B support)
**Requirements**: Phases 6 and 8 working end to end
**Deliverables**: UI shows cited CaseMasterIDs, the generated SQL, and a confidence indicator alongside every answer, using the Phase 8 rendering framework

### Phase 10 — Dynamic Follow-Up Question Generation
**Owner**: Person B (backend), Person A (buttons)
**Requirements**: Phase 9 working
**Deliverables**: Small QuickML call generating 2-4 context-based follow-up questions per answer; rendered as tappable buttons that resubmit as the next message — not hardcoded

### Phase 11 — Network & Graph Analysis (backend)
**Owner**: Person B
**Requirements**: `inv_arrestsurrenderaccused` populated; NetworkX available in a Catalyst Function
**Deliverables**: Multi-hop query support (e.g. "other cases linked to this accused's known associates"), returned via the Phase 8 envelope as a `network` response type

### Phase 12 — Investigation Board Visualization (frontend)
**Owner**: Person A
**Requirements**: Phase 11 backend graph output; Phase 8 rendering framework
**Deliverables**: Force-directed node-link board rendering the Phase 11 graph, generic avatar icons (never real or fake photos), triggered contextually from a case or entity in the conversation

### Phase 13 — Similar-Case Retrieval
**Owner**: Person B
**Requirements**: Embedding model via QuickML; Catalyst NoSQL configured
**Deliverables**: "Similar past cases" feature returning ranked matches for a given case, using BriefFacts + structured MO features

### Phase 14 — Entity Auto-Context Fetch
**Owner**: Person B (backend), Person A (sidecar card UI)
**Requirements**: Phases 11 and 13 working
**Deliverables**: Whenever Stage 1 resolves a reference to an accused/victim, a parallel call pulls their profile (past cases, risk score, network position) and surfaces it as a sidecar card alongside the main answer

### Phase 15 — Risk Scoring, SHAP, Counterfactuals
**Owner**: Person B
**Requirements**: Labeled synthetic offender feature set; Zia AutoML configured
**Deliverables**: Risk score endpoint; SHAP explanation attached to each score; counterfactual output surfaced via the Phase 8 envelope

### Phase 16 — Pattern, Trend & Sociological Dashboards + Hotspot Map
**Owner**: Person A (rendering), Person B (aggregate endpoints)
**Requirements**: Aggregate query endpoints from Phase 3 data; Leaflet/OSM integrated
**Deliverables**: Dashboard views for crime trends and socio-economic overlays; an actual interactive Karnataka map (district/station boundaries, live hotspot overlay), not just aggregate charts; independent-sampling caveat documented in the UI copy

### Phase 17 — RBAC & Audit Logging
**Owner**: Person A
**Requirements**: Catalyst Authentication configured
**Deliverables**: Role-gated access for Investigator/Analyst/Supervisor/Policymaker roles; every query written to an audit log

### Phase 18 — Kannada, Voice & Code-Switching
**Owner**: Whoever is free first
**Requirements**: Zia Services (STT/TTS/translation) enabled
**Deliverables**: Voice query in English and Kannada; mixed-language input routed correctly through Stage 1. Ship as a real but honestly-scoped feature — a translation-layer pass, not a claim of deep native Kannada NLU, since neither of you can independently verify Kannada output quality.

### Phase 19 — Minimal Financial Crime Module
**Owner**: Person A
**Requirements**: None beyond Phase 1 schema access
**Deliverables**: Small invented schema (Account, Transaction, AccountCaseLink); one working demo query tracing a money trail linked to a case

### Phase 20 — Evidence Linking Module
**Owner**: Person B (backend/storage), Person A (video/audio player components)
**Requirements**: Phase 1 Evidence table; Catalyst Stratus configured
**Deliverables**: Retrieval and display of linked video/audio/image/document artifacts per case, using placeholder/stock files — demonstrates the capability, not real forensic content

### Phase 21 — PDF Conversation Export
**Owner**: Person A
**Requirements**: Catalyst SmartBrowz enabled
**Deliverables**: Chat history exportable as a PDF from the UI

### Phase 22 — Self Red-Team Test Suite
**Owner**: Person B
**Requirements**: Phases 5–6 stable
**Deliverables**: Adversarial/ambiguous/injection-style query set run against the pipeline; defense-rate report suitable for a demo slide

### Phase 23 — Full Deployment Integration (FEATURE FREEZE)
**Owner**: Both
**Requirements**: All prior phases at working-prototype quality
**Deliverables**: End-to-end app deployed on Catalyst (Functions + Web Client Hosting + API Gateway + Domain Mapping); the Phase 7 React frontend is the live, submitted UI; the Streamlit harness is retired; no new feature work begins after this phase closes

### Phase 24 — Packaging & Demo Rehearsal
**Owner**: Both
**Requirements**: Phase 23 complete
**Deliverables**: GitHub repo cleaned up with README; demo video recorded; submission template deck filled in; live-pitch query script rehearsed — dashboard-first opening, chatbot depth second, one deliberate abstention example
