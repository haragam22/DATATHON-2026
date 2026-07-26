# Frontend Specification — KSP Crime Database Conversational AI

Owner: Person A (teammate). This is your dedicated reference — everything you need to build without having to cross-reference the backend-oriented docs constantly. `technical.md` still has the full architecture if you need it; this file is scoped to what you're actually building.

## Views / pages
1. **Landing dashboard** — the opening screen. District-level hotspot map, recent trend charts, patrol-recommendation feed. This is the demo's opening beat, not an afterthought — see idea.md for why.
2. **Chat interface** — the conversational core. Rich, envelope-driven responses, not a plain text thread.
3. **Case detail view** — opened from a chat answer or a dashboard drill-down. Shows case summary, evidence, and an entry point into the investigation board.
4. **Investigation board** — full-screen force-directed network view, opened contextually (e.g. a "map the network" button from a case or chat answer).
5. **Role-gated views** — what's visible/actionable differs by role (Investigator / Analyst / Supervisor / Policymaker). Route guards based on the authenticated user's role.

## The response envelope — your core contract with the backend
Every backend answer arrives as:
```
{
  "response_type": "text" | "card" | "chart" | "map" | "network" | "evidence",
  "payload": { ...type-specific data... },
  "answer_text": "the natural language answer",
  "cited_case_ids": ["CM1023", "CM4471"],
  "confidence_score": 0.0-1.0,
  "generated_sql": "SELECT ...",
  "follow_up_questions": ["...", "...", "..."]
}
```
Build one renderer component per `response_type` and dispatch on that field. This is the single most important piece of frontend architecture — every visual feature (map, chart, network, evidence) is just another case in that dispatch, not a separate system.

## Component inventory
- **ChatWindow** — message list + input, holds conversation state
- **MessageBubble** — dispatches to the right renderer based on `response_type`
- **ResponseCard / ResponseChart / ResponseMap / ResponseNetwork / ResponseEvidence** — one renderer per envelope type
- **FollowUpButtons** — renders `follow_up_questions` as tappable buttons that resubmit as the next message; never hardcode these, they come from the backend per-turn
- **EntitySidecarCard** — auto-appears when the backend resolves a person reference (accused/victim), shows their profile/history without being asked
- **InvestigationBoard** — force-directed graph, generic avatar icons (initials/icons, never real or fake photos — see constraints below)
- **HotspotMap** — Leaflet map with district/station boundaries and a live hotspot overlay
- **EvidencePlayer** — video/audio playback component, works off placeholder/stock files linked via the backend's Evidence records
- **ExplainabilityPanel** — shows cited case IDs, generated SQL, confidence indicator, expandable/collapsible so it doesn't clutter the primary answer
- **RoleGate** — wraps routes/components, checks the authenticated role before rendering
- **PDFExportButton** — triggers conversation history export

## State management
- Conversation history held in React state/context, mirrored to the backend `ConversationMessage` table so a refresh doesn't lose context
- Auth/session state via the Catalyst Authentication SDK, role read from the `AppUser`/`AppRole` mapping
- Don't reach for Redux/global state libraries unless the app genuinely outgrows context — for a 10-day build, keep state management as simple as it can be

## Constraints — these are not optional, they were decided for real reasons
- **No real or fake photorealistic photos of people, anywhere, including the investigation board.** Generic avatar icons only. See `schema.md` notes for why.
- **Evidence playback uses placeholder/stock files only.** Don't build or imply any real video/audio content analysis — there is no real forensic data to analyze.
- **The hotspot map is Leaflet + OpenStreetMap, client-side only.** No paid maps API, no external map-hosting service — Catalyst doesn't offer one, and this keeps the whole app within the Catalyst-only deployment rule.
- **Kannada support is a translation-layer feature, not a claim of deep native NLU** — say so honestly in the UI/demo, since neither of you can independently verify Kannada output quality.

## Build order (mirrors implementation.md, frontend-only view)
1. Chat shell (Phase 7)
2. Response rendering framework — build this before any individual visual feature (Phase 8)
3. Explainability panel (Phase 9)
4. Follow-up buttons (Phase 10)
5. Investigation board (Phase 12)
6. Entity sidecar card (Phase 14, UI half)
7. Dashboards + hotspot map (Phase 16)
8. RBAC gating (Phase 17)
9. Evidence player (Phase 20)
10. PDF export (Phase 21)

Full owner/requirement/deliverable detail for each phase lives in `implementation.md` — this is just the frontend-only sequence extracted for quick reference.
