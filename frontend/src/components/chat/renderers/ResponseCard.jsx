/**
 * ResponseCard — renders card response_type.
 * Used by similar-cases, entity-context, and general structured data.
 *
 * Renders key-value pairs from the data object and special-cases
 * known shapes like similar_cases arrays.
 */

import { FileText } from 'lucide-react';
import ResponseMap from './ResponseMap';
import './ResponseRenderers.css';

const LAT_KEY_RE = /^lat(itude)?$/i;
const LON_KEY_RE = /^lon(g|gitude)?$/i;
const COUNT_KEY_RE = /count/i;

function findKey(row, re) {
  return Object.keys(row).find((k) => re.test(k));
}

export default function ResponseCard({ envelope }) {
  const { data } = envelope;

  if (!data) return <div className="response-card">No data</div>;

  // Pipeline's actual NL-query shape: { answer, rows, language }. Detect the
  // rows' real content instead of dumping them as a raw JSON blob — a map
  // when they carry coordinates, a bar list when they're a plain
  // category+count breakdown, a table otherwise.
  if (Array.isArray(data.rows)) {
    return <GenericRowsCard answer={data.answer} rows={data.rows} />;
  }

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

function GenericRowsCard({ answer, rows }) {
  if (rows.length === 0) {
    return (
      <div className="response-card">
        {answer && <p className="response-card__answer">{answer}</p>}
        <p className="text-muted text-sm">No matching records found.</p>
      </div>
    );
  }

  const firstRow = rows[0];
  const latKey = findKey(firstRow, LAT_KEY_RE);
  const lonKey = findKey(firstRow, LON_KEY_RE);
  const keys = Object.keys(firstRow);

  // Coordinates present -> render as a map, not a table of numbers.
  // A visual carries its own information — skip the LLM prose entirely
  // (it's usually just the same coordinates restated as a sentence).
  if (latKey && lonKey) {
    const countKey = findKey(firstRow, COUNT_KEY_RE);
    const clusters = rows
      .filter((r) => r[latKey] != null && r[lonKey] != null)
      .map((r) => ({
        lat: Number(r[latKey]),
        lon: Number(r[lonKey]),
        count: countKey ? Number(r[countKey]) || 1 : 1,
      }));
    return (
      <div className="response-card">
        <p className="response-card__caption text-muted text-xs">
          {clusters.length} location{clusters.length !== 1 ? 's' : ''}
        </p>
        <ResponseMap envelope={{ data: { clusters } }} />
      </div>
    );
  }

  // Exactly one numeric column + one label column -> a simple bar list.
  // Same principle: the bars already show every value, so the caption
  // stays short rather than repeating each row back as a sentence.
  if (keys.length === 2) {
    const numericKey = keys.find((k) => rows.every((r) => !isNaN(parseFloat(r[k]))));
    const labelKey = keys.find((k) => k !== numericKey);
    if (numericKey && labelKey) {
      const values = rows.map((r) => parseFloat(r[numericKey]));
      const max = Math.max(...values);
      return (
        <div className="response-card">
          <p className="response-card__caption text-muted text-xs">
            {rows.length} result{rows.length !== 1 ? 's' : ''}, by {formatKey(numericKey)}
          </p>
          <ul className="response-card__barlist">
            {rows.map((r, i) => (
              <li key={i} className="response-card__barlist-row">
                <span className="response-card__barlist-label font-mono text-xs">
                  {formatKey(labelKey)} {r[labelKey]}
                </span>
                <div className="response-card__barlist-track">
                  <div
                    className="response-card__barlist-fill"
                    style={{ width: `${(values[i] / max) * 100}%` }}
                  />
                </div>
                <span className="response-card__barlist-value font-mono text-xs">{r[numericKey]}</span>
              </li>
            ))}
          </ul>
        </div>
      );
    }
  }

  // Fallback: a real table, not a raw JSON dump
  return (
    <div className="response-card">
      {answer && <p className="response-card__answer">{answer}</p>}
      <div className="response-card__table-wrap">
        <table className="response-card__table font-mono text-xs">
          <thead>
            <tr>
              {keys.map((k) => (
                <th key={k}>{formatKey(k)}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i}>
                {keys.map((k) => (
                  <td key={k}>{String(r[k])}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

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
