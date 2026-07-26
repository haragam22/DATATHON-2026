/**
 * EnvelopeDispatcher — the core architectural piece (Milestone 2).
 *
 * Takes an envelope { response_type, data, cited_case_ids, generated_sql,
 * confidence_score, follow_up_questions } and dispatches to the matching
 * renderer component.
 *
 * Every visual feature (chart, map, network, evidence) is just another
 * case in this dispatch — not a separate system.
 */

import ResponseText from './ResponseText';
import ResponseCard from './ResponseCard';
import ResponseChart from './ResponseChart';
import ResponseMap from './ResponseMap';
import ResponseNetwork from './ResponseNetwork';
import ResponseEvidence from './ResponseEvidence';
import ResponseFinancial from './ResponseFinancial';

const RENDERERS = {
  text: ResponseText,
  card: ResponseCard,
  chart: ResponseChart,
  map: ResponseMap,
  network: ResponseNetwork,
  evidence: ResponseEvidence,
  financial: ResponseFinancial,
};

export default function EnvelopeDispatcher({ envelope }) {
  if (!envelope) return null;

  const { response_type, data } = envelope;

  // Pipeline error (200 with data.error) — render as text with error flag
  if (data?.error) {
    return <ResponseText envelope={envelope} isError />;
  }

  const Renderer = RENDERERS[response_type];

  if (!Renderer) {
    // Unknown response_type — render raw data as text fallback
    console.warn(
      `[EnvelopeDispatcher] Unknown response_type: "${response_type}". Falling back to text.`
    );
    return <ResponseText envelope={envelope} />;
  }

  return <Renderer envelope={envelope} />;
}
