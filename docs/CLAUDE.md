# CLAUDE.md — Agent Instructions for the KSP Crime Database Conversational AI Project

This file is the operating manual for any agent (or person) working in this repo. Read it before making any change. If something you need to decide isn't covered here or in the linked docs, **stop and ask — don't invent it.**

## Project context
Built for Catalyst by Zoho Datathon 2026, PS1: Intelligent Conversational AI for the KSP Crime Database. Team of 2, ~10-day build window. Full vision, feature list, architecture, schema, and phase plan live in four sibling docs — always check these before making an architectural call:
- `idea.md` — vision, required features, differentiators, scope decisions
- `technical.md` — architecture, stack, per-feature technical approach
- `schema.md` — canonical database schema (KSP-original + gap-fill + our additions)
- `implementation.md` — phase-by-phase plan, owners, requirements, deliverables

## Hard constraints — never violate these
- **Deployment is 100% on Zoho Catalyst, no exceptions.** No external Neo4j instance, no external LLM API hosting, no non-Catalyst frontend hosting for the production build. This is a competition rule, not a preference.
- **LLM = Catalyst QuickML, self-hosted open-source model only.** No calls to Anthropic/OpenAI/or any external LLM API anywhere in the deployed system.
- **Graph engine = NetworkX inside a Catalyst Function.** Not Neo4j, not any externally-hosted graph DB.
- **Backend language = Python** for every Catalyst Serverless Function.
- **Frontend is two-tier**: React SPA via Catalyst Slate/Web Client Hosting is the deployed, submitted product. Streamlit is a local dev/test harness only — it is never deployed and never part of the submission.
- **Legal codes**: `Act`/`Section` master data must carry both IPC (pre-1 July 2024 offences) and BNS (1 July 2024 onward), keyed off `CaseMaster.CrimeRegisteredDate`. Never default to IPC-only for anything registered after that date — this is a real, current legal fact, not a stylistic choice.
- **Synthetic data only.** Never seed generation with real FIR text, real news coverage of real crimes, or real court judgments.
- **`CasteID`/`ReligionID` in `ComplainantDetails`** are sampled independently of crime outcome during data generation unless explicitly told otherwise — don't let the model "discover" a correlation that generation carelessly baked in.
- **Evidence is placeholder/stock content only.** There is no real crime scene footage or audio in a synthetic dataset. The Evidence feature demonstrates retrieval and linking, never claim or imply real forensic content analysis.
- **No real or fake photorealistic photos of synthetic people, anywhere — including the investigation board.** Use generic avatar icons. Generating convincing fake "booking photos" of nonexistent people is a credibility risk in front of a police jury, not a feature.
- **Map integration is a client-side library (Leaflet/OpenStreetMap), not a Catalyst service** — Catalyst doesn't offer one. This is still fully Catalyst-deployed since it's a frontend dependency, not external infrastructure.

## Schema rules
- `schema.md` is canonical. Part 1 (KSP-original tables) is fixed — don't rename or restructure it. Parts 2 and 3 (gap-fill and our additions) can be refined as implementation reveals better choices.
- `inv_arrestsurrenderaccused` is the backbone of the network/graph layer (Phase 9). Treat any change to it as high-risk — validate before merging.
- Any new table introduced in code must be added to `schema.md` in the same change. Schema doc and actual DB must never drift apart.

## Backend pipeline rules (this is the whole differentiation strategy — don't shortcut it)
- SQL generation is always schema-constrained — restricted to valid table/column names from the live schema. Never let it run as unconstrained free-text generation.
- Every user-facing answer must carry: cited `CaseMasterID`s, the generated SQL, and a confidence score. Not optional — this is the explainability requirement, not a nice-to-have.
- Ambiguous intent → the system asks a clarifying question. It never silently picks an interpretation.
- Self-consistency check (query generated twice, diffed) and post-execution sanity check (result shape validated against expected bounds) are required pipeline steps, not add-ons to cut under time pressure.
- Entailment check on the final NL answer (every claim verified against retrieved rows) runs before any answer reaches the user.

## Development process
- Follow `implementation.md` phase order. Don't start a phase before its stated requirements are met — most failures in a tight timeline come from skipping ahead and hitting a missing dependency.
- Phase ownership (Person A / Person B) is a starting assumption in the docs — reassign based on actual skills, but keep ownership explicit in commits/PRs so both people know who's driving what.
- Use the Streamlit harness (Phase 2) continuously for manual testing — don't wait on the React frontend to sanity-check a backend piece.
- **Phase 18 (deployment integration) is a hard feature freeze. No exceptions, no "just one more feature."** Phase 19 (packaging) is protected — nothing but README, video, deck, and demo rehearsal happens there.

## Submission non-negotiables
- Deployment via Catalyst is mandatory without exception, per datathon rules.
- GitHub repo must be public, with a README, before the deadline.
- Demo video and deployed link must both be public.
- Use the official submission template — not a custom format.

## Anti-hallucination rules — apply to every change, not just architecture decisions
- **Never invent a Catalyst service, API method, library function, or config key that hasn't been confirmed to exist.** If you're not sure it exists, say so plainly and ask or flag it as unverified — don't present a guess as fact.
- **Never invent column names, table names, or types not in `schema.md`.** If a task needs a field that isn't there, propose adding it explicitly and update `schema.md` in the same change — don't assume it and move on.
- **Never fill a missing credential, API key, or config value with something that looks real.** Use an obvious placeholder (e.g. `<SET_ME>`) and flag it for the user — a plausible-looking fake value is worse than an obvious gap.
- **Don't mark a feature "done" if it's stubbed, mocked, or partial.** Say explicitly what's real and what's placeholder. This matters especially for Phase 15 (financial crime module), which is deliberately lighter-depth by design — don't let it quietly become "fully built" in status updates when it isn't.
- **If a synthetic data assumption changes** (scale, distribution, generation method), reflect it back into `schema.md`/`technical.md` — don't let the docs and the actual data drift apart.
- **Never trust generated SQL or generated intent JSON on its own.** It only becomes safe to execute after it's passed through the schema-constrained decoder and the Stage 2 verifier — treat those as mandatory gates, not optional checks to skip when short on time.

## Code quality standards
- Python everywhere on the backend: type hints on function signatures, docstrings on public functions, one responsibility per function — a schema-validation function shouldn't also execute queries.
- No premature optimization, but avoid clearly wasteful patterns: no N+1 queries against Catalyst Data Store, no loading full tables into memory when a filtered query would do, no recomputing risk scores or embeddings on every request when the `RiskScore`/`CaseEmbedding` tables in `schema.md` exist precisely to cache them.
- Validate inputs explicitly at function boundaries, especially anything touching LLM-generated output.
- Handle errors explicitly — don't swallow exceptions silently, especially inside the pipeline (Stage 1/2, self-consistency check, sanity check, entailment check). A silent failure there quietly defeats the entire hallucination-reduction design, which is the project's core differentiator.
- Write a test alongside any component that affects correctness — the schema-constrained decoder, the verifier, the self-consistency check, the entailment check — since these are exactly what get demoed as differentiators and need to hold up under adversarial input (see Phase 17), not just the happy path.
- Keep commits scoped to one phase or feature at a time, referencing the phase number from `implementation.md`.

## When in doubt
This project has already hit several real forks where guessing wrong would have meant rewriting official docs later — LLM access, graph engine choice, backend language, data scale, financial crime module scope. Treat any new one the same way: surface it explicitly and ask, rather than resolving it silently and moving on. Concretely, ask first whenever you'd otherwise: pick a new library or dependency not already in `technical.md`, change an already-agreed tech choice, invent a schema field, guess at a missing config value, or reinterpret a requirement from `idea.md` in a way that changes its scope.
