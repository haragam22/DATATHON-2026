/**
 * EntitySidecar — Milestone 7: Entity context side panel.
 *
 * GET /api/entity-context/<accused_id>
 * Backend returns:
 *   { data: { accused_id, name, past_case_ids, risk_score, network_position: { connected_accused_count, connected_case_count } } }
 *
 * Per design.md:
 *   - Slides open beneath / beside the answer (not a modal — keep context visible)
 *   - 150ms ease-out height transition, no bounce
 *   - Past case IDs as mono chips (clicking opens that case in the investigation board)
 *   - Risk score (from RiskScore table if populated, otherwise null)
 *   - Network position stats
 *   - Initials avatar with signal-red ring (accused)
 */

import { useState, useEffect } from 'react';
import { X, User, AlertTriangle, Loader, FileText, Shield, Network, ChevronRight } from 'lucide-react';
import { getEntityContext, ApiError } from '../../services/api';
import RoleGate from '../common/RoleGate';
import './EntitySidecar.css';

export default function EntitySidecar({ accusedId, accusedName, onClose, onSelectCase }) {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!accusedId) return;
    let cancelled = false;

    setIsLoading(true);
    setError(null);

    getEntityContext(accusedId)
      .then((envelope) => {
        if (cancelled) return;
        // envelope is { response_type, data: {accused_id, name, past_case_ids, risk_score, network_position}, ... }
        setData(envelope?.data ?? envelope);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof ApiError ? err.message : 'Failed to load entity context');
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => { cancelled = true; };
  }, [accusedId]);

  if (!accusedId) return null;

  const displayName = data?.name || accusedName || `Accused #${accusedId}`;
  const initials = getInitials(displayName);

  return (
    <div className="entity-sidecar surface-raised animate-slide-in">
      {/* Header */}
      <div className="entity-sidecar__header">
        <div className="entity-sidecar__avatar">
          <span className="entity-sidecar__avatar-ring" aria-hidden="true">
            {initials}
          </span>
        </div>
        <div className="entity-sidecar__name-block">
          <span className="font-mono text-sm font-semibold text-gold">{displayName}</span>
          <span className="font-mono text-xs text-faint">
            AccusedMasterID: {accusedId}
          </span>
        </div>
        <button
          className="btn-icon entity-sidecar__close"
          onClick={onClose}
          title="Close"
          aria-label="Close entity sidecar"
        >
          <X size={16} />
        </button>
      </div>

      {/* Body */}
      <div className="entity-sidecar__body">
        {isLoading && (
          <div className="entity-sidecar__status">
            <Loader size={20} className="spin text-blue" />
            <span className="font-mono text-xs text-muted">Loading entity context…</span>
          </div>
        )}

        {error && !isLoading && (
          <div className="entity-sidecar__status">
            <AlertTriangle size={20} className="text-red" />
            <span className="text-sm text-red">{error}</span>
          </div>
        )}

        {!isLoading && !error && data && (
          <>
            {/* Past Cases */}
            <SidecarSection icon={FileText} title="Prior Case History">
              {data.past_case_ids?.length > 0 ? (
                <div className="entity-sidecar__chips">
                  {data.past_case_ids.map((cid) => (
                    <button
                      key={cid}
                      className="chip chip-gold font-mono text-xs"
                      onClick={() => onSelectCase?.(cid)}
                      title={`Load Case #${cid}`}
                    >
                      Case #{cid} <ChevronRight size={10} />
                    </button>
                  ))}
                </div>
              ) : (
                <span className="text-xs text-muted">No prior cases found.</span>
              )}
            </SidecarSection>

            {/* Network Position */}
            <SidecarSection icon={Network} title="Network Position">
              <div className="entity-sidecar__stats">
                <StatItem
                  label="Connected Accused"
                  value={data.network_position?.connected_accused_count ?? '—'}
                />
                <StatItem
                  label="Connected Cases"
                  value={data.network_position?.connected_case_count ?? '—'}
                />
              </div>
            </SidecarSection>

            {/* Risk Score (Supervisor+ Gated) */}
            <RoleGate scope="risk-score" requiredRoleLabel="Supervisor">
              <SidecarSection icon={Shield} title="Risk Assessment">
                {data.risk_score ? (
                  <div className="entity-sidecar__risk">
                    <div className="entity-sidecar__risk-score">
                      <span className="font-mono text-lg font-semibold">
                        {typeof data.risk_score.RiskScoreValue === 'number'
                          ? data.risk_score.RiskScoreValue.toFixed(2)
                          : data.risk_score.RiskScoreValue ?? '—'}
                      </span>
                      {data.risk_score.ModelVersion && (
                        <span className="font-mono text-xs text-faint">
                          Model: {data.risk_score.ModelVersion}
                        </span>
                      )}
                    </div>
                    {data.risk_score.TopFeaturesJSON && (
                      <div className="entity-sidecar__features">
                        <span className="label-section text-xs">Top Features</span>
                        <FeatureList rawFeatures={data.risk_score.TopFeaturesJSON} />
                      </div>
                    )}
                  </div>
                ) : (
                  <span className="text-xs text-muted">
                    No risk score computed for this entity.
                  </span>
                )}
              </SidecarSection>
            </RoleGate>
          </>
        )}
      </div>
    </div>
  );
}

// ── Sub-components ──

function SidecarSection({ icon: Icon, title, children }) {
  return (
    <div className="entity-sidecar__section">
      <div className="entity-sidecar__section-title">
        <Icon size={14} className="text-muted" />
        <span className="label-section text-xs">{title}</span>
      </div>
      <div className="entity-sidecar__section-body">
        {children}
      </div>
    </div>
  );
}

function StatItem({ label, value }) {
  return (
    <div className="entity-sidecar__stat">
      <span className="font-mono text-lg font-semibold text-100">{value}</span>
      <span className="text-xs text-muted">{label}</span>
    </div>
  );
}

function getInitials(name) {
  if (!name) return '?';
  return name.split(/\s+/).filter(Boolean).map((w) => w[0]).slice(0, 2).join('').toUpperCase();
}

function FeatureList({ rawFeatures }) {
  let features = [];
  try {
    features = typeof rawFeatures === 'string' ? JSON.parse(rawFeatures) : rawFeatures;
    if (!Array.isArray(features)) {
      if (typeof features === 'object' && features !== null) {
        features = Object.entries(features).map(([k, v]) => ({
          feature: k,
          impact: typeof v === 'object' ? v.impact : v,
        }));
      } else {
        features = [];
      }
    }
  } catch (e) {
    features = [];
  }

  if (!features || features.length === 0) {
    return <span className="text-xs text-faint">No feature breakdown available.</span>;
  }

  return (
    <div className="entity-sidecar__feature-list">
      {features.map((item, idx) => {
        const name = item.feature ? item.feature.replace(/_/g, ' ') : `Feature #${idx + 1}`;
        const impact = typeof item.impact === 'number' ? item.impact : (item.value ?? 0);
        const isPositive = impact > 0;
        return (
          <div key={idx} className="entity-sidecar__feature-row">
            <span className="font-mono text-xs text-muted entity-sidecar__feature-name">
              {name}
            </span>
            <span className={`chip font-mono text-xs ${isPositive ? 'chip-red' : 'chip-blue'}`}>
              {isPositive ? `+${impact.toFixed(3)}` : impact.toFixed(3)}
            </span>
          </div>
        );
      })}
    </div>
  );
}

