/**
 * VerificationStamp — Signature element for KSP Crime Intelligence.
 *
 * Appears in the top-right corner of assistant responses.
 * Displays confidence score in IBM Plex Mono with confidence-banded ring style:
 *   - ≥80%: solid ksp-gold ring, "VERIFIED" micro-label, "stamped down" animation
 *   - 50–79%: dashed ksp-gold ring, score only
 *   - <50%: dashed signal-red ring, "LOW CONFIDENCE" micro-label
 *   - Abstention: outlined question-mark chip, text-400 color
 *
 * Clicking toggles the explainability panel.
 */

import { HelpCircle, ChevronDown, ChevronUp } from 'lucide-react';
import './VerificationStamp.css';

export default function VerificationStamp({
  confidenceScore,
  isAbstention = false,
  isExpanded = false,
  onToggleExpand,
}) {
  // Abstention state (clarifying question, no confidence score)
  if (isAbstention || confidenceScore == null) {
    return (
      <button
        className="v-stamp v-stamp--abstention"
        onClick={onToggleExpand}
        title="Clarifying question — Click to view session details"
        aria-expanded={isExpanded}
        aria-label="Clarifying question details"
      >
        <HelpCircle size={16} strokeWidth={1.5} color="var(--text-400)" />
        <span className="v-stamp__abstention-text font-mono text-xs text-muted">
          CLARIFYING
        </span>
        {onToggleExpand && (
          <span className="v-stamp__chevron">
            {isExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          </span>
        )}
      </button>
    );
  }

  // Normalize score to percentage (0..100)
  const scorePercent = Math.round(
    confidenceScore <= 1 ? confidenceScore * 100 : confidenceScore
  );

  // Band determination
  let band = 'high'; // >= 80
  if (scorePercent < 50) {
    band = 'low';
  } else if (scorePercent < 80) {
    band = 'medium';
  }

  return (
    <button
      className={`v-stamp v-stamp--${band} ${
        isExpanded ? 'v-stamp--expanded' : ''
      }`}
      onClick={onToggleExpand}
      title={`Confidence: ${scorePercent}% — Click to view SQL & citations`}
      aria-expanded={isExpanded}
      aria-label={`Confidence score ${scorePercent}%. Click for explainability.`}
    >
      <div className="v-stamp__seal">
        <span className="v-stamp__score font-mono">{scorePercent}%</span>
        {band === 'high' && <span className="v-stamp__label">VERIFIED</span>}
        {band === 'low' && <span className="v-stamp__label">LOW CONF</span>}
      </div>
      {onToggleExpand && (
        <span className="v-stamp__chevron">
          {isExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
        </span>
      )}
    </button>
  );
}
