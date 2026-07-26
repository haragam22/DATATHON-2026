/**
 * ExplainabilityPanel — Evidence & Verification Panel.
 *
 * Collapses/expands beneath assistant responses when the verification stamp is clicked.
 * Shows:
 *   1. Cited Case IDs — mono chips (clicking triggers case view handler)
 *   2. Generated SQL — syntax-muted IBM Plex Mono block with Copy button
 *   3. Confidence Score — 1x stamp repeat & confidence breakdown
 */

import { useState } from 'react';
import { Copy, Check, FileText, Database, ShieldCheck } from 'lucide-react';
import VerificationStamp from './VerificationStamp';
import './ExplainabilityPanel.css';

export default function ExplainabilityPanel({ envelope, onSelectCaseId }) {
  const [copied, setCopied] = useState(false);

  if (!envelope) return null;

  const {
    cited_case_ids = [],
    generated_sql = null,
    confidence_score = null,
    data,
  } = envelope;

  const isAbstention = Boolean(data?.clarifying_question);

  const handleCopySql = () => {
    if (!generated_sql) return;
    navigator.clipboard.writeText(generated_sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="explainability-panel surface-raised">
      <div className="explainability-panel__header">
        <span className="label-section text-gold">SYSTEM EXPLAINABILITY & CITATIONS</span>
      </div>

      <div className="explainability-panel__content">
        {/* Row 1: Cited Cases */}
        <div className="explainability-row">
          <div className="explainability-row__label text-xs text-muted">
            <FileText size={13} strokeWidth={1.5} />
            <span>CITED CASE RECORDS ({cited_case_ids.length})</span>
          </div>
          {cited_case_ids.length > 0 ? (
            <div className="explainability-row__chips">
              {cited_case_ids.map((caseId) => (
                <button
                  key={caseId}
                  className="chip chip-blue font-mono explainability-case-chip"
                  onClick={() => onSelectCaseId?.(caseId)}
                  title={`View details for Case #${caseId}`}
                >
                  Case #{caseId}
                </button>
              ))}
            </div>
          ) : (
            <span className="text-xs text-faint font-mono">
              No specific case records cited for this query.
            </span>
          )}
        </div>

        {/* Row 2: Generated SQL */}
        <div className="explainability-row">
          <div className="explainability-row__header">
            <div className="explainability-row__label text-xs text-muted">
              <Database size={13} strokeWidth={1.5} />
              <span>EXECUTED ZCQL QUERY</span>
            </div>
            {generated_sql && (
              <button
                className="btn btn-ghost explainability-copy-btn font-mono text-xs"
                onClick={handleCopySql}
                title="Copy SQL query to clipboard"
              >
                {copied ? (
                  <>
                    <Check size={12} className="text-green" />
                    <span>Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy size={12} />
                    <span>Copy SQL</span>
                  </>
                )}
              </button>
            )}
          </div>
          {generated_sql ? (
            <pre className="explainability-sql font-mono text-xs surface-base">
              <code>{generated_sql}</code>
            </pre>
          ) : (
            <span className="text-xs text-faint font-mono">
              No SQL query executed (direct rule or pipeline abstention).
            </span>
          )}
        </div>

        {/* Row 3: Confidence Score Breakdown */}
        <div className="explainability-row explainability-row--score">
          <div className="explainability-row__label text-xs text-muted">
            <ShieldCheck size={13} strokeWidth={1.5} />
            <span>CONFIDENCE SCORE BREAKDOWN</span>
          </div>
          <div className="explainability-score-box">
            <VerificationStamp
              confidenceScore={confidence_score}
              isAbstention={isAbstention}
            />
            <div className="explainability-score-desc text-xs text-muted">
              {isAbstention ? (
                <p>
                  System abstained from answering to prevent hallucination. Clarification requested.
                </p>
              ) : confidence_score >= 0.8 ? (
                <p>
                  High confidence match based on strict database constraints & verified schemas.
                </p>
              ) : confidence_score >= 0.5 ? (
                <p>
                  Medium confidence. Results retrieved via semantic search and schema mapping.
                </p>
              ) : (
                <p className="text-red">
                  Low confidence. Please cross-verify cited case IDs manually before taking action.
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
