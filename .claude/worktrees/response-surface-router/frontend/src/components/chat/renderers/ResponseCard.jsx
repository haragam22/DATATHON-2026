/**
 * ResponseCard — renders card response_type.
 * Used by similar-cases, entity-context, and general structured data.
 *
 * Renders key-value pairs from the data object and special-cases
 * known shapes like similar_cases arrays.
 */

import { FileText } from 'lucide-react';
import './ResponseRenderers.css';

export default function ResponseCard({ envelope }) {
  const { data } = envelope;

  if (!data) return <div className="response-card">No data</div>;

  // Special case: similar_cases array
  if (Array.isArray(data.similar_cases)) {
    return (
      <div className="response-card">
        <div className="response-card__header label-section">
          Similar Cases
        </div>
        <div className="response-card__grid">
          {data.similar_cases.map((c, i) => (
            <SimilarCaseCard key={c.case_id ?? i} caseData={c} />
          ))}
        </div>
        {data.similar_cases.length === 0 && (
          <p className="text-muted text-sm">No similar cases found.</p>
        )}
      </div>
    );
  }

  // Special case: past_case_ids (entity context)
  if (Array.isArray(data.past_case_ids)) {
    return (
      <div className="response-card">
        <div className="response-card__header label-section">
          Entity History
        </div>
        <div className="response-card__chips">
          {data.past_case_ids.map((id) => (
            <span key={id} className="chip chip-blue font-mono">
              Case #{id}
            </span>
          ))}
        </div>
        {data.past_case_ids.length === 0 && (
          <p className="text-muted text-sm">No prior history found.</p>
        )}
      </div>
    );
  }

  // Generic: render data keys as a definition-list card
  const { session_id, ...displayData } = data;
  const entries = Object.entries(displayData).filter(
    ([, v]) => v !== null && v !== undefined
  );

  if (entries.length === 0) {
    return <div className="response-card text-muted text-sm">No data to display.</div>;
  }

  return (
    <div className="response-card">
      <dl className="response-card__dl">
        {entries.map(([key, value]) => (
          <div key={key} className="response-card__field">
            <dt className="response-card__label label-section">{formatKey(key)}</dt>
            <dd className="response-card__value">
              {typeof value === 'object' ? (
                <pre className="response-card__json font-mono text-xs">
                  {JSON.stringify(value, null, 2)}
                </pre>
              ) : (
                <span>{String(value)}</span>
              )}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

// ── Sub-components ──

function SimilarCaseCard({ caseData }) {
  const { case_id, similarity_score, crime_no, brief_facts, ...rest } = caseData;
  return (
    <div className="similar-case-card surface-raised">
      <div className="similar-case-card__header">
        <FileText size={14} strokeWidth={1.5} />
        <span className="font-mono text-xs">
          {crime_no ? `CrimeNo ${crime_no}` : `Case #${case_id}`}
        </span>
        {similarity_score != null && (
          <span className="chip chip-blue">
            {(similarity_score * 100).toFixed(0)}% match
          </span>
        )}
      </div>
      {brief_facts && (
        <p className="similar-case-card__brief text-sm text-muted">
          {brief_facts.slice(0, 200)}
          {brief_facts.length > 200 ? '…' : ''}
        </p>
      )}
      {Object.keys(rest).length > 0 && (
        <div className="similar-case-card__extra text-xs text-faint font-mono">
          {Object.entries(rest).map(([k, v]) => (
            <span key={k}>
              {formatKey(k)}: {String(v)}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Helpers ──

function formatKey(key) {
  return key
    .replace(/_/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}
