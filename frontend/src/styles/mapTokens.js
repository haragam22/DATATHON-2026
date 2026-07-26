/**
 * Design tokens as literal hex, for contexts that can't resolve CSS custom
 * properties: Leaflet's Canvas renderer (CircleMarker pathOptions) reads
 * fillStyle/strokeStyle strings directly via ctx.fillStyle = value, which
 * silently ignores an unresolved `var(--x)` string and falls back to
 * Leaflet's own default blue — this is why hotspot markers rendered as
 * plain blue dots instead of the spec'd amber rings.
 *
 * Recharts/inline-style/SVG-attribute contexts are real CSS contexts and
 * resolve var() fine — only hand Canvas-consuming props these literals.
 * Source of truth: src/index.css :root tokens / docs/design.md.
 */
export const KSP_GOLD = '#E8A33D'; // evidence amber — primary accent, hotspot clusters
export const KSP_BLUE = '#16233D'; // ink navy — authority
export const STAMP_INK = '#1F7A8C'; // verification teal — confidence stamp only, never reused here
export const SIGNAL_RED = '#B23A34'; // case red
export const SIGNAL_AMBER = '#E8A33D'; // evidence amber doubles as moderate-risk signal
export const SIGNAL_GREEN = '#3B8F6D'; // verified green
export const HOTSPOT_COLD = '#3D6FA8'; // cold end of the hotspot heat-map gradient
export const INK_950 = '#EAECEF'; // case paper

function lerp(a, b, t) {
  return Math.round(a + (b - a) * t);
}

function hexToRgb(hex) {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

function rgbToHex([r, g, b]) {
  return '#' + [r, g, b].map((v) => v.toString(16).padStart(2, '0')).join('');
}

/**
 * Hotspot heat-map gradient: cold blue -> evidence amber -> case red.
 * @param {number} t density ratio, 0 (coldest) to 1 (hottest)
 */
export function hotspotHeatColor(t) {
  const clamped = Math.max(0, Math.min(1, t));
  const cold = hexToRgb(HOTSPOT_COLD);
  const mid = hexToRgb(KSP_GOLD);
  const hot = hexToRgb(SIGNAL_RED);
  const [a, b] = clamped < 0.5 ? [cold, mid] : [mid, hot];
  const localT = clamped < 0.5 ? clamped / 0.5 : (clamped - 0.5) / 0.5;
  return rgbToHex([lerp(a[0], b[0], localT), lerp(a[1], b[1], localT), lerp(a[2], b[2], localT)]);
}
