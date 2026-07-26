# Idea — Intelligent Conversational AI for KSP Crime Database

## Competition context
- Event: Catalyst by Zoho Datathon 2026, in partnership with Karnataka State Police (KSP)
- Problem Statement chosen: **PS1 — Intelligent Conversational AI for the KSP Crime Database**
- Mandatory constraint: full solution must be deployed on Zoho Catalyst — no exceptions
- Data: no real KSP data provided. We receive schema + column headers only. We generate our own synthetic dataset against that schema.
- Team: 2 people, ~10-day build window

## The problem, in plain terms
KSP's crime records exist across ~1,100 police stations, managed largely through manual, Excel-driven processes. There is no way for an investigator, analyst, or policymaker to ask a question in plain language and get a grounded, evidence-backed answer. Crime patterns, offender networks, and socio-demographic signals sit buried in disconnected records instead of surfacing proactively.

## What we're building
A natural-language interface over the KSP crime schema that lets an investigator ask questions the way they'd ask a colleague — and get back an answer that shows its work: the data it's grounded in, the query that produced it, and how confident it is. Underneath that conversational layer sits a set of analytical capabilities (network analysis, offender profiling, predictive risk scoring) that turn the database from a passive record store into an active investigative tool.

The core design principle across the whole system: **never answer confidently on a guess.** Every layer — query understanding, execution, and final answer — has a verification step whose job is to catch and surface uncertainty rather than paper over it.

## Required features (as specified by KSP / Catalyst)
1. Conversational Crime Intelligence Interface — NL chatbot, context-aware follow-ups, English + Kannada, voice, PDF export of conversation history
2. Criminal Network & Relationship Analysis — links between accused, victims, locations, financial accounts; visualization of networks and organized-crime groups
3. Crime Pattern & Trend Analytics — trends across time, geography, crime type, MO; hotspot and emerging-cluster identification
4. Sociological Crime Insights — demographic and socio-economic correlation with crime patterns
5. Criminology-Based Offender Profiling — repeat-offender identification, behavioral analysis, risk scoring
6. Investigator Decision Support — case summaries, timelines, similar-case retrieval, investigative leads
7. Financial Crime & Transaction Link Analysis — money-trail and suspicious-transaction detection
8. Crime Forecasting & Early Warning — predictive hotspot and emerging-pattern alerts
9. Explainable AI & Transparent Analytics — every answer backed by visible data references and reasoning
10. Secure Role-Based Access & Governance — investigator/analyst/supervisor/policymaker roles, audit logging

## Differentiating features we're adding
1. Self red-teaming test suite — adversarial, ambiguous, and injection-style queries run against our own pipeline, defense rate shown as evidence of robustness
2. Abstention over guessing — the system asks a clarifying question on ambiguous intent instead of silently picking an interpretation
3. Calibrated confidence indicator per answer, not a binary answer/no-answer
4. MO similarity search — embedding-based "similar past cases" retrieval
5. Counterfactual explanations on risk scores ("this drops to medium-risk if X changes"), not just static feature-importance bars
6. Code-switched query handling — mixed Kannada + English input, matching how officers actually speak
7. Live citation of case IDs and the generated query shown alongside every answer
8. Dual BNS/IPC legal-code handling based on `CrimeRegisteredDate`, instead of defaulting to IPC everywhere
9. Rich, visualized responses (cards, charts, maps, network boards) instead of plain chatbot text — the interface should feel like a dashboard, not a text box
10. Evidence linking — retrieval and playback of video/audio/document artifacts tied to a case (placeholder/stock content, since no real forensic evidence exists in a synthetic dataset)
11. Dynamic, context-based follow-up questions, not hardcoded suggestions
12. Entity auto-context — whenever a person is mentioned, their history/profile surfaces automatically alongside the answer
13. Investigation board — a force-directed network visualization ("who's connected to whom") triggered contextually from a case, using generic avatar icons rather than real or fake photos
14. Interactive Karnataka hotspot map, not just aggregate charts, for the pattern/trend requirement

## Explicit scope decisions
- **Synthetic data scale**: designed for ~5,000–20,000 case records for the prototype (production-realistic patterns, hackathon-realistic volume), documented as designed to scale further
- **Financial crime module**: minimal — a small invented schema (accounts, transfers, one link table) with a working demo query, intentionally lighter in depth than the core conversational and network layers
- **Depth allocation**: every required feature is present and functional; engineering depth concentrates on the conversational core, network analysis, explainability, and RBAC, since those are what will actually be probed in judging and demo

## Why this approach wins
Most teams will ship a fluent NL→SQL bot that answers confidently and wrongly on ambiguous input. Our differentiation isn't a longer feature list — it's a system that knows when it doesn't know, shows its evidence for everything it does say, and has been adversarially tested against itself before a judge ever tries to break it.
