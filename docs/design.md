---
name: KSP Crime Intelligence
description: A conversational crime-database AI for Karnataka State Police — case-file instrument, not SaaS dashboard.
colors:
  ink-950: "#EDE6D3"
  ink-900: "#E3DBC1"
  ink-800: "#DAD0B2"
  ink-700: "#CCC09B"
  line-700: "#B8A87C"
  text-100: "#221F17"
  text-400: "#5C5640"
  text-600: "#8B856A"
  ksp-blue: "#14405E"
  ksp-gold: "#8C7A45"
  stamp-ink: "#7A2A1F"
  signal-red: "#A93D24"
  signal-amber: "#96731F"
  signal-green: "#3D6650"
typography:
  display:
    fontFamily: "IBM Plex Sans, system-ui, sans-serif"
    fontSize: "34px"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "normal"
  headline:
    fontFamily: "IBM Plex Sans, system-ui, sans-serif"
    fontSize: "26px"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "0.01em"
  title:
    fontFamily: "IBM Plex Sans, system-ui, sans-serif"
    fontSize: "20px"
    fontWeight: 600
    lineHeight: 1.2
  body:
    fontFamily: "IBM Plex Sans, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "IBM Plex Sans, system-ui, sans-serif"
    fontSize: "12px"
    fontWeight: 600
    letterSpacing: "0.01em"
  mono:
    fontFamily: "IBM Plex Mono, ui-monospace, Consolas, monospace"
    fontSize: "12px"
    fontWeight: 400
rounded:
  card: "4px"
  input: "4px"
  chip: "2px"
spacing:
  1: "4px"
  2: "8px"
  3: "12px"
  4: "16px"
  6: "24px"
  8: "32px"
  12: "48px"
components:
  button-primary:
    backgroundColor: "{colors.ksp-blue}"
    textColor: "{colors.text-100}"
    rounded: "{rounded.card}"
    padding: "8px 16px"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.text-400}"
    rounded: "{rounded.card}"
    padding: "8px 16px"
  chip-gold:
    backgroundColor: "rgba(198, 162, 77, 0.08)"
    textColor: "{colors.ksp-gold}"
    rounded: "{rounded.chip}"
  chip-blue:
    backgroundColor: "rgba(44, 90, 160, 0.1)"
    textColor: "{colors.ksp-blue}"
    rounded: "{rounded.chip}"
  card-assistant:
    backgroundColor: "{colors.ink-800}"
    textColor: "{colors.text-100}"
    rounded: "{rounded.card}"
    padding: "16px"
  input-field:
    backgroundColor: "{colors.ink-700}"
    textColor: "{colors.text-100}"
    rounded: "{rounded.input}"
    padding: "8px 12px"
---

# Design System: KSP Crime Intelligence

## Overview

**Creative North Star: "The Case File, Not the Console"**

KSP Crime Intelligence is a conversational crime-database AI built for investigators, analysts, supervisors, and policymakers under real institutional stakes. It reads as an instrument, not a toy: precise, calm, high-contrast, built for long dense-information sessions rather than a marketing surface. The product's actual differentiator — never answering confidently on a guess — is the design brief. Every answer carries a citation, a query, and a confidence score, and the UI's job is to make that verification almost physical, the way a real case file carries stamps, tags, and signed annotations.

The visual register is Indian government/police case-file material — buff gazette paper, khaki cloth, brass fittings, sealing-wax ink — deliberately in place of the navy-black-plus-neon/gold-foil look that most AI-generated dashboards default to regardless of brief. That combination was tried and rejected here on purpose: landing on it would undercut the "verification, not vibes" thesis by making the product look templated. The build is paper-first (light theme is `:root` default); an opt-in dark theme exists for night control-room use but is a token swap, not a second design pass. Two canvases — the hotspot map and the investigation board — deliberately stay dark regardless of theme, read as a lit instrument panel inset into the paper page, like a photo or map insert on a physical case-file page.

**Key Characteristics:**
- Paper-first light theme (buff/ledger tones), dark theme opt-in and token-swap only
- Navy (ksp-blue) as the one broad-use accent; brass (ksp-gold) reserved for citations/highlights; sealing-wax red (stamp-ink) reserved solely for the verification stamp
- Small consistent radius (4px cards/inputs, 2px chips), hairline borders over shadows
- IBM Plex Sans for UI, IBM Plex Mono for anything verifiable (SQL, case IDs, coordinates, confidence)
- One recurring signature component (the verification stamp) carries the entire product thesis

## Colors

The palette reads as ink on paper, not glow on black — buff/khaki surfaces with navy, brass, and sealing-wax-red sitting on top the way stamped ink would on a real document.

### Primary
- **Official Navy** (`#14405E`, `ksp-blue`): primary accent — links, primary buttons, active nav state, user chat-bubble fill, focus ring on inputs, chart series 1.

### Secondary
- **Brass** (`#8C7A45`, `ksp-gold`): citation chips, key highlights, active-role badge (Supervisor), hotspot-cluster markers, selected-node glow on the investigation board. Never a general accent and never a large fill area.

### Tertiary
- **Sealing-Wax Ink** (`#7A2A1F`, `stamp-ink`): the verification stamp exclusively — its high- and medium-confidence ring states. Nothing else in the system uses this token.

### Neutral
- **Gazette Paper** (`#EDE6D3`, `ink-950`): app background.
- **Base Panel** (`#E3DBC1`, `ink-900`): base panel surface.
- **Raised Surface** (`#DAD0B2`, `ink-800`): cards, assistant message bubbles, sidecars.
- **Hover Surface** (`#CCC09B`, `ink-700`): hover/active surface, input fields.
- **Hairline Border** (`#B8A87C`, `line-700`): dividers, card borders, scrollbar thumb.
- **Primary Ink** (`#221F17`, `text-100`): body text.
- **Secondary Ink** (`#5C5640`, `text-400`): labels, captions, Investigator role dot.
- **Faint Ink** (`#8B856A`, `text-600`): disabled/tertiary text.
- **Alarm Red** (`#A93D24`, `signal-red`): errors, high-risk indicators, low-confidence stamp ring. Deliberately warmer/more alarm-toned than `stamp-ink` so the two reds are never confused.
- **Caution Amber** (`#96731F`, `signal-amber`): medium risk/confidence, warnings.
- **Verified Green** (`#3D6650`, `signal-green`): success, high confidence, Policymaker role dot.

### Named Rules
**The Brass-Is-Not-A-Stamp Rule.** `ksp-gold` (brass) and `stamp-ink` (sealing-wax red) are visually and semantically distinct on purpose: a real official stamp is red ink on paper, never gold foil. Brass marks "worth noticing" (citations, highlights, active role); stamp-ink marks "this is a verification claim." If either starts appearing outside its lane, palette discipline has slipped.

**The Dark-Canvas Exception Rule.** The hotspot map and the investigation-board force-directed graph stay on a dark canvas (`#15160F`) regardless of active theme. This is a deliberate material exception — an instrument-panel inset on the page — not a missed theme-swap, and it is not to be "fixed" by paperizing those two surfaces.

## Typography

**Body/UI Font:** IBM Plex Sans (with system-ui, sans-serif fallback)
**Mono/Data Font:** IBM Plex Mono (with ui-monospace, Consolas, monospace fallback)

**Character:** Plex Sans reads as technical/institutional rather than generic-friendly (Inter, Roboto) without tipping into novelty. Plex Mono is a legibility signal, not a stylistic flourish — every generated SQL string, case ID, `CrimeNo`, confidence percentage, and coordinate is set in it, marking that content as raw, verifiable system output rather than prose.

### Hierarchy
- **Display** (600, 34px, 1.2 line-height): dashboard hero numbers only (e.g. total active cases). Used rarely.
- **Headline** (600, 26px, 1.2 line-height, 0.01em tracking): section headers.
- **Title** (600, 20px, 1.2 line-height): card titles.
- **Body** (400, 14px, 1.5 line-height): default UI/body text; 16px for emphasized body copy.
- **Label** (600, 12px, 0.01em tracking, uppercase): section labels, tab-plate feel — `.label-section` utility.
- **Mono** (400, 12px): SQL, case IDs, coordinates, confidence percentages — `.data-mono` utility.

### Named Rules
**The Verifiable-Means-Mono Rule.** Anything that is a direct, checkable system output (SQL, case IDs, coordinates, confidence scores) is set in IBM Plex Mono. Anything that is prose or UI chrome is set in IBM Plex Sans. The typeface itself is part of the explainability signal — never use mono for stylistic effect on non-verifiable content.

## Layout

Assistant answers render as full-width cards (`ink-800` surface, `line-700` hairline border, 4px radius), not narrow chat-bubble shapes, because answers are dashboards-in-miniature (charts, maps, network snippets) rather than short text. User messages stay compact and right-aligned (`ksp-blue` fill, max 70% width) to visually separate the two roles without breaking the card idiom for the assistant side.

Spacing scale (px, no arbitrary values): 4 / 8 / 12 / 16 / 24 / 32 / 48. New chat messages enter with a 100ms fade + 8px slide-up; panels (explainability, entity sidecar) expand/collapse with a 150ms ease-out transition and no bounce. `prefers-reduced-motion` disables both, keeping only opacity fades.

## Elevation & Depth

The system is flat-by-default: a 1px `line-700` hairline border is preferred over a drop shadow for separating surfaces (cards, panels). Shadow is reserved for genuinely floating elements — modals, the entity sidecar overlay, dropdown menus — using a soft, low-opacity ink-tinted shadow rather than a hard black shadow, keeping depth readable as "paper lifted off paper," not a glowing screen effect.

### Shadow Vocabulary
- **Float** (`box-shadow: 0 4px 24px rgba(34, 31, 23, 0.14), 0 1px 4px rgba(34, 31, 23, 0.1)`): modals, entity sidecar overlay, dropdowns. In dark theme this shifts to an ink-950-toned shadow (`rgba(10, 15, 28, 0.55)` / `rgba(10, 15, 28, 0.4)`) rather than pure black.

### Named Rules
**The Flat-By-Default Rule.** Surfaces are flat at rest, separated by hairline borders. Shadow appears only for elements that are genuinely floating above the page (modal, overlay, dropdown) — it signals "this is not part of the page flow," not general polish.

## Shapes

Radius is small and consistent: 4px on cards, inputs, and buttons; 2px on chips and badges. Nothing in the system uses 16px+ radius — that register belongs to consumer/friendly-startup software and is explicitly rejected here as the wrong register for investigative infrastructure. Icons are line icons only (Lucide, 1.5px stroke); avatars are always initials-in-a-ring, ring color keyed to role, never illustrated or photorealistic people anywhere in the product, including the investigation board — this is a hard product constraint (synthetic-data credibility), not a style preference.

## Components

### Buttons
- **Shape:** 4px radius (`--radius-card`), 1px border.
- **Primary:** `ksp-blue` background, `text-100` text, `8px 16px` padding (`.btn-primary`).
- **Hover:** primary lightens to `#3568bb`; ghost/icon buttons pick up `ink-700` hover surface and `line-700` border.
- **Ghost:** transparent background, `text-400` text, `line-700` border — used for secondary actions.

### Chips
- **Style:** outlined (1px `currentColor` border), transparent-to-tinted background (e.g. brass at 8% opacity), 2px radius, mono type, `text-xs`.
- **Variants:** `chip-gold` (citations/highlights), `chip-blue` (neutral system tags), `chip-red` (alerts), `chip-green` (verified/success), `chip-muted` (inactive).

### Cards / Containers
- **Corner Style:** 4px radius.
- **Background:** `ink-800` (raised surface).
- **Shadow Strategy:** none at rest; see Elevation & Depth for the floating-element exception.
- **Border:** 1px `line-700` hairline.
- **Internal Padding:** 16px (`--space-4`).

### Inputs / Fields
- **Style:** `ink-700` background, 1px `line-700` border, 4px radius, `8px 12px` padding.
- **Focus:** border shifts to `ksp-blue`, no glow/ring.
- **Placeholder:** `text-600` (faint ink).

### Navigation
Role badge sits top-right, always visible: 2px-radius outlined chip with a role-colored dot plus text label. Sidebar sessions list uses filled/hollow dot markers (today vs. earlier) rather than heavier active-state styling.

### RBAC Role Badges
- Investigator: `text-400` dot (neutral, broadest/base role)
- Analyst: `ksp-blue` dot
- Supervisor: `ksp-gold` dot
- Policymaker: `signal-green` dot

Gated features are never hidden outright: `RoleGate` renders the underlying content dimmed with a lock icon and a "Requires [Role] Access" tooltip/badge rather than removing it from the layout.

### Verification Stamp (signature component)
A circular seal badge in the top-right corner of every assistant answer (`VerificationStamp.jsx`), showing the confidence score in IBM Plex Mono inside a ring whose style is keyed to confidence band, not just the number:
- **≥80%:** solid `stamp-ink` ring, "VERIFIED" micro-label, a one-time 120ms scale+fade "stamped down" animation (slight overshoot then settle) on first render — the single deliberate animation moment in the app, never repeated elsewhere.
- **50–79%:** dashed `stamp-ink` ring, score only, no animation.
- **<50%:** dashed `signal-red` ring, "LOW CONF" micro-label — a distinct, more alarm-toned red from `stamp-ink` so "verified-but-medium" and "not verified" never read as the same color.
- **Abstention/no score:** no stamp at all — an outlined question-mark chip (`text-400`) in its place. The absence of a stamp is itself meaningful: the system isn't claiming anything yet.

Clicking/tapping the stamp toggles the explainability panel (cited case IDs, generated SQL in a mono block, confidence score) — the stamp is the entry point to explainability, not a passive badge.

### Envelope Dispatcher (architectural pattern)
Every assistant response is an envelope (`{ response_type, data, cited_case_ids, generated_sql, confidence_score, follow_up_questions }`) routed by `EnvelopeDispatcher` to one of seven typed renderers (text, card, chart, map, network, evidence, financial). New response types are added as another dispatch case, not a parallel rendering system — this keeps the stamp, citation, and card treatment uniform across every visual feature the product ships.

## Do's and Don'ts

### Do:
- **Do** use `stamp-ink` (#7A2A1F) exclusively for the verification stamp's high/medium confidence rings — never elsewhere.
- **Do** use `ksp-gold` (#8C7A45) only for citations, highlights, the active/Supervisor role badge, and hotspot-cluster markers — never as a general accent or large fill.
- **Do** prefer a 1px `line-700` hairline border over a drop shadow for separating surfaces; reserve shadow for modals, overlays, and dropdowns.
- **Do** set anything verifiable (SQL, case IDs, coordinates, confidence scores) in IBM Plex Mono.
- **Do** keep the hotspot map and investigation-board graph on a dark canvas regardless of theme — the deliberate instrument-panel-on-paper exception.
- **Do** show gated/RBAC-restricted features dimmed with a lock icon and tooltip rather than hiding them.
- **Do** use initials-in-a-ring avatars only, ring color keyed to role.

### Don't:
- **Don't** use radius above 4px on cards/inputs or above 2px on chips/badges anywhere in the system.
- **Don't** use the navy + saturated-blue + gold-foil combination — this is the generic AI-dashboard signature the system was deliberately built to avoid.
- **Don't** repeat the stamp's "stamped down" animation anywhere else; it is earned by being rare.
- **Don't** hide gated functionality outright — silently disappearing controls read as a bug, not governance.
- **Don't** render illustrated or photorealistic people anywhere, including the investigation board — synthetic-data credibility constraint, not a style preference.
- **Don't** carry the dark chat-bubble legacy background (`rgba(15, 22, 38, 0.6)` on `.v-stamp`) forward as a pattern elsewhere — it is a known leftover from the pre-paper dark palette, not a token to reuse (see summary note below).
