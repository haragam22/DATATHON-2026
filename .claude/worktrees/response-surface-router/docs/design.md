# Design System — KSP Crime Database Conversational AI

## Design philosophy

This is not a generic SaaS dashboard. The audience is investigators, analysts,
supervisors, and policymakers using this under real institutional stakes — the
UI should read as **an instrument, not a toy**: precise, calm, high-contrast,
built for long sessions of dense information, not a marketing surface.

The product's actual differentiator — "never answer confidently on a guess" —
is the design brief. Every answer carries a citation, a query, and a
confidence score. The UI's job is to make that verification visible and
almost physical, the way a real case file carries stamps, tags, and signed
annotations. That's where the one signature element below comes from — it's
not decoration, it's the thesis made visible.

Avoid: generic dark-mode-with-neon-green ("hacker terminal"), generic
light-mode SaaS dashboard blue-on-white, rounded-everything friendly-startup
look. This product is not friendly-startup software — it's investigative
infrastructure.

---

## Token system

### Color — dark, command-center base (primary theme)

| Token | Hex | Use |
|---|---|---|
| `ink-950` | `#0A0F1C` | App background |
| `ink-900` | `#0F1626` | Base panel surface |
| `ink-800` | `#161F35` | Raised surface (cards, sidecars) |
| `ink-700` | `#1F2A45` | Hover/active surface, input fields |
| `line-700` | `#2B3757` | Hairline borders, dividers |
| `text-100` | `#EAEEF7` | Primary text |
| `text-400` | `#96A2C0` | Secondary text, labels, captions |
| `text-600` | `#5C6890` | Disabled/tertiary text |
| `ksp-blue` | `#2C5AA0` | Primary accent — links, primary buttons, active nav, chart series 1 |
| `ksp-gold` | `#C6A24D` | Secondary accent — the stamp/seal, citations, key highlights. Use sparingly, never as a background fill for large areas |
| `signal-red` | `#B8493A` | Errors, high-risk indicators, low confidence |
| `signal-amber` | `#C68A3D` | Medium risk/confidence, warnings |
| `signal-green` | `#4C8067` | High confidence, verified, success states |

Rule: `ksp-gold` appears only on the stamp/seal element, citation chips, and
active-role badges — nowhere else. If it starts showing up as a general
accent color everywhere, that's a sign the palette discipline has slipped.

### Optional light theme (station daytime use)

Invert to `#F5F3ED` background / `#1A2236` text, keep `ksp-blue` and
`ksp-gold` as-is (both still readable on light), swap `line-700` to
`#D8D4C8`. Build dark-first; light mode is a straightforward token swap, not
a separate design pass — don't spend effort re-deriving it from scratch.

### Typography

- **UI / body**: IBM Plex Sans — weights 400/500/600. Chosen because it reads
  as technical/institutional rather than generic-friendly (Inter, Roboto),
  without tipping into novelty.
- **Data / code / citations**: IBM Plex Mono — every generated SQL string,
  case ID, `CrimeNo`, confidence percentage, and coordinate uses this. Mono
  in this context isn't a stylistic flourish, it's a legibility signal: "this
  is raw system output, verifiable, not prose."
- **Headers/section titles**: IBM Plex Sans, weight 600, slightly increased
  letter-spacing (0.01em) at small sizes for a plate/label feel — think
  case-folder tab labels, not a landing-page hero.

Type scale (px, at 1x): 12 (caption/mono data) / 14 (body/UI default) / 16
(emphasized body) / 20 (card titles) / 26 (section headers) / 34 (dashboard
hero numbers only — used rarely, e.g. total active cases on the landing
dashboard).

### Spacing & shape

- Spacing scale: 4 / 8 / 12 / 16 / 24 / 32 / 48 (px) — no arbitrary values.
- Radius: **small and consistent**, 4px on cards/inputs, 2px on chips/badges.
  Do not use large rounded corners (16px+) anywhere — it reads as
  consumer-app-friendly, wrong register for this product.
- Borders over shadows: prefer a 1px `line-700` hairline border to a drop
  shadow for separating surfaces. Reserve shadow (soft, low-opacity, `ink-950`
  at 40%) only for genuinely floating elements — modals, the entity sidecar
  card when it overlays content, dropdown menus.

### Iconography

Line icons only (Lucide or similar), 1.5px stroke, no filled icons except for
status dots. Avatars are always **initials-in-a-ring**, never illustrated
people, never photos — ring color encodes role (see RBAC section). This is a
hard product constraint, not a style choice: no real or fake photorealistic
depictions of people, anywhere, including the investigation board.

---

## The signature element: the verification stamp

Every assistant answer in the chat, and every card/chart/map/network response,
carries a small circular **stamp badge** in its top-right corner — visually
referencing an official document stamp/seal, rendered in outline (not solid
fill) using `ksp-gold`, containing the confidence score as a percentage in
Plex Mono.

- Ring style changes with confidence band, not just the number:
  - ≥80%: solid gold ring, "VERIFIED" micro-label beneath the percentage
  - 50–79%: gold ring, dashed, no micro-label
  - <50%: `signal-red` ring, dashed, "LOW CONFIDENCE" micro-label
- On first render of a high-confidence (≥80%) answer, the stamp does a single
  quick scale+fade-in "stamped down" motion (120ms, ease-out, slight
  overshoot then settle) — the one deliberate animation moment in the app.
  Do not repeat this motion elsewhere; it's earned by being rare.
- Clicking/tapping the stamp expands the explainability panel (cited case
  IDs, generated SQL in a Plex Mono block, confidence score) — the stamp is
  the entry point to explainability, not just a passive badge.
- On an abstention/clarifying-question response, there is no stamp — an
  outlined question-mark chip in its place, same size/position, `text-400`
  color. Absence of a stamp is itself meaningful: the system isn't claiming
  anything yet.

---

## Layout concepts

### Chat interface

```
┌─ Sidebar (sessions) ─┬────────── Chat area ──────────┐
│                       │  ┌──────────────────────┐    │
│  [+ New session]      │  │ user message          │    │
│                       │  └──────────────────────┘    │
│  ● Session — today    │       ┌────────────────────┐ │
│  ○ Session — 7/24     │       │ assistant response  │ │
│  ○ Session — 7/22     │       │ [envelope renderer]  │ │
│                       │       │              ⊙ 87%   │ │  <- stamp
│  [role badge: INV]    │       └────────────────────┘  │
│                       │       [follow-up] [follow-up] │
│                       │  ┌──────────────────────┐     │
│                       │  │ input + send          │     │
│                       │  └──────────────────────┘     │
└───────────────────────┴───────────────────────────────┘
```

Assistant bubbles are full-width-ish cards, not narrow chat-bubble shapes —
this app's answers are dashboards-in-miniature (charts, maps, network
snippets), not short text. Don't force them into a rounded speech-bubble
container; use the card token treatment (ink-800 surface, line-700 border,
4px radius).

### Landing dashboard

```
┌─────────────────────────────────────────────┐
│  KSP CRIME INTELLIGENCE          [role] [⚙]  │
├───────────────┬───────────────┬─────────────┤
│  Active cases │  Trend (7d)   │  Risk alerts │
│  34,281  ▲2%  │  [sparkline]  │  [count]     │
├───────────────┴───────────────┴─────────────┤
│                                               │
│         [ Karnataka hotspot map ]            │
│         (Leaflet, dark tile theme,           │
│          gold cluster markers)               │
│                                               │
├───────────────────────────────────────────────┤
│  Patrol recommendation feed                    │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │ card    │ │ card    │ │ card    │          │
│  └─────────┘ └─────────┘ └─────────┘          │
└─────────────────────────────────────────────┘
```

The hotspot map uses a dark custom Leaflet tile style (CARTO dark or similar
free OSM-derived dark tileset — client-side only, no paid API) with hotspot
clusters as gold-ringed circles sized by case count, not raw heat blobs — the
product spec is spatiotemporal clustering, and the map should look like it,
not like a generic heatmap plugin default.

### Investigation board

Force-directed graph, `ink-950` canvas. Nodes: circle, initials avatar,
ring colored by role (accused = `signal-red` ring, victim = `ksp-blue` ring,
associate/witness = `text-400` ring). Edges: thin `line-700`, labeled with
relationship type in 10px Plex Mono on hover only (don't clutter the graph
with permanent edge labels at rest). Selected node gets a `ksp-gold` glow
ring — reuse of the accent for "currently under investigation focus," which
is a real semantic use, not decoration.

### Explainability panel

Collapsed by default under the stamp click, slides open beneath the answer
(not a modal — keep the answer visible while reading its evidence). Three
rows: cited case IDs as small mono chips (clicking one opens case detail),
generated SQL in a syntax-muted mono block with a copy button, confidence
score with the same stamp visual repeated small at 1x scale.

### Evidence viewer

Every evidence tile carries a persistent diagonal watermark-style label —
`SYNTHETIC / PLACEHOLDER` in `text-600` at low opacity across the tile
corner — reinforcing in the UI itself (not just in copy) that this is not
real forensic content. This is a constraint made visible, matching the same
logic as the confidence stamp: the interface should show its own limits, not
just its answers.

---

## RBAC visual treatment

Role badge (top-right, always visible): small rounded-rect chip, 2px radius,
outlined not filled, text label + role-colored dot.

| Role | Dot color |
|---|---|
| Investigator | `text-400` (neutral — broadest but base-level role) |
| Analyst | `ksp-blue` |
| Supervisor | `ksp-gold` |
| Policymaker | `signal-green` |

Gated tabs/actions for a role that lacks scope are **not hidden entirely** —
show them dimmed/disabled with a small lock icon and a tooltip ("Requires
Supervisor access") rather than silently disappearing. Silently hiding
functionality reads as a bug; showing-but-locking reads as intentional
governance, which is the actual product feature (RBAC is explainability too —
show the boundary, don't hide it).

---

## Motion

Minimal, purposeful, never ambient/looping:

- Stamp "verified" animation on first high-confidence render (described above) — the one signature motion moment.
- Panel expand/collapse (explainability, entity sidecar): 150ms ease-out height transition, no bounce.
- New chat message: simple 100ms fade+8px slide-up, nothing more.
- No page-load hero animations, no scroll-triggered reveals — this isn't a
  marketing site, sessions are long and repeated, ambient motion becomes
  annoying fast for daily-use software.
- Respect `prefers-reduced-motion` — disable the stamp animation and message
  slide-in, keep only opacity fades.

---

## Do / Don't summary

**Do**: dense information laid out with real hierarchy, mono type for
anything verifiable, the stamp as the one recurring signature, hairline
borders over shadows, dimmed-and-locked over hidden for RBAC, dark tiles on
the map, initials-in-a-ring avatars.

**Don't**: rounded-everything consumer aesthetic, neon hacker-green dark
mode, drop shadows everywhere, hiding gated features outright, illustrated or
photorealistic people anywhere, decorative animation, gold used as a general
accent instead of reserved for verification/citation moments.
