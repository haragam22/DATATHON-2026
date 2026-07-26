/**
 * SimilarCasesPanel — Milestone 6: Similar case retrieval panel.
 *
 * GET /api/similar-cases/<case_id>
 * Backend returns: { response_type: "card", data: { similar_cases: [{case_id, similarity}] } }
 *
 * Features:
 *   - Case ID input with instant search
 *   - Similarity percentage badges
 *   - Clickable case cards to load network graph
 */

import { useState, useEffect } from 'react';
import { FileText, Search, Loader, AlertTriangle, ExternalLink, BarChart2 } from 'lucide-react';
import { getSimilarCases, ApiError } from '../../services/api';
import './SimilarCasesPanel.css';

export default function SimilarCasesPanel({ caseId, onSelectCase }) {
  const [inputCaseId, setInputCaseId] = useState(caseId ? String(caseId) : '');
  const [activeCaseId, setActiveCaseId] = useState(caseId || null);
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Sync with external caseId prop changes
  useEffect(() => {
    if (caseId && caseId !== activeCaseId) {
      setInputCaseId(String(caseId));
      setActiveCaseId(caseId);
    }
  }, [caseId]);

  // Fetch similar cases when activeCaseId changes
  useEffect(() => {
    if (!activeCaseId) return;
    let cancelled = false;

    setIsLoading(true);
    setError(null);

    getSimilarCases(activeCaseId)
      .then((envelope) => {
        if (cancelled) return;
        // envelope is { response_type, data: { similar_cases }, ... }
        const cases = envelope?.data?.similar_cases || envelope?.similar_cases || [];
        setResults(cases);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof ApiError ? err.message : 'Failed to load similar cases');
        setResults(null);
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => { cancelled = true; };
  }, [activeCaseId]);

  const handleSearch = (e) => {
    e.preventDefault();
    const id = parseInt(inputCaseId.trim(), 10);
    if (!isNaN(id) && id > 0) {
      setActiveCaseId(id);
    }
  };

  return (
    <div className="similar-cases-panel">
      <div className="similar-cases-panel__header">
        <BarChart2 size={16} className="text-blue" />
        <span className="label-section">Similar Cases</span>
      </div>

      <form onSubmit={handleSearch} className="similar-cases-panel__search">
        <div className="similar-cases-panel__input-wrapper">
          <Search size={14} className="similar-cases-panel__search-icon" />
          <input
            type="number"
            min="1"
            className="similar-cases-panel__input font-mono"
            value={inputCaseId}
            onChange={(e) => setInputCaseId(e.target.value)}
            onFocus={(e) => e.target.select()}
            placeholder="Case ID..."
            aria-label="Case ID for similar cases"
          />
        </div>
        <button
          type="submit"
          className="btn btn-primary font-mono text-xs"
          disabled={isLoading || !inputCaseId}
        >
          {isLoading ? <Loader size={14} className="spin" /> : 'Find'}
        </button>
      </form>

      <div className="similar-cases-panel__body">
        {isLoading && (
          <div className="similar-cases-panel__status">
            <Loader size={20} className="spin text-blue" />
            <span className="font-mono text-xs text-muted">Searching similar cases…</span>
          </div>
        )}

        {error && !isLoading && (
          <div className="similar-cases-panel__status">
            <AlertTriangle size={20} className="text-red" />
            <span className="text-sm text-red">{error}</span>
          </div>
        )}

        {!isLoading && !error && results && results.length === 0 && (
          <div className="similar-cases-panel__status">
            <span className="text-muted text-sm">No similar cases found for Case #{activeCaseId}.</span>
          </div>
        )}

        {!isLoading && !error && results && results.length > 0 && (
          <div className="similar-cases-panel__list">
            {results.map((c, idx) => (
              <SimilarCaseCard
                key={c.case_id ?? idx}
                caseData={c}
                rank={idx + 1}
                onSelect={() => onSelectCase?.(c.case_id)}
              />
            ))}
          </div>
        )}

        {!activeCaseId && !isLoading && !error && (
          <div className="similar-cases-panel__status">
            <span className="text-muted text-sm font-mono">Enter a Case ID to find similar cases.</span>
          </div>
        )}
      </div>
    </div>
  );
}

function SimilarCaseCard({ caseData, rank, onSelect }) {
  const { case_id, similarity } = caseData;
  const pct = similarity != null ? (similarity * 100).toFixed(1) : null;

  // Color the similarity badge by band
  const badgeClass = pct >= 70 ? 'chip-green' : pct >= 40 ? 'chip-blue' : 'chip-muted';

  return (
    <button
      className="similar-case-item surface-raised"
      onClick={onSelect}
      title={`Load Case #${case_id} in Investigation Board`}
    >
      <div className="similar-case-item__rank font-mono text-xs text-faint">#{rank}</div>
      <FileText size={14} className="text-muted" />
      <span className="similar-case-item__id font-mono text-sm">
        Case #{case_id}
      </span>
      {pct != null && (
        <span className={`chip ${badgeClass} font-mono text-xs`}>
          {pct}% match
        </span>
      )}
      <ExternalLink size={12} className="text-faint similar-case-item__arrow" />
    </button>
  );
}
