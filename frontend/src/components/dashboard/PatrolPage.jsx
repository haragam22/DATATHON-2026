/**
 * PatrolPage — Feature 3: Patrolling Hotspots Dashboard tab.
 *
 * Reuses GET /api/hotspots (aggregates.py::get_hotspots) as-is — it already
 * DBSCAN-clusters incidents and sorts by a recency+severity-weighted score
 * descending, which *is* a patrol-priority ranking already. This tab adds
 * nothing new backend-side; it just presents the same data as a ranked
 * "where to send patrol" list next to the existing map, rather than the
 * Dashboard's map-only framing.
 */

import { useState, useEffect } from 'react';
import { ShieldAlert, Loader, AlertTriangle, MapPin } from 'lucide-react';
import HotspotMap from './HotspotMap';
import { getHotspots, ApiError } from '../../services/api';
import './PatrolPage.css';

const TOP_N = 10;

export default function PatrolPage() {
  const [clusters, setClusters] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);
    getHotspots()
      .then((envelope) => {
        if (cancelled) return;
        setClusters(envelope?.data?.clusters || []);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof ApiError ? err.message : 'Failed to load patrol recommendations');
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  const ranked = clusters.slice(0, TOP_N);

  return (
    <div className="patrol-page">
      <div className="patrol-page__grid">
        <div className="patrol-page__map-panel">
          <HotspotMap />
        </div>

        <div className="patrol-page__list-panel surface-raised">
          <div className="patrol-page__list-header">
            <div className="flex items-center gap-2">
              <ShieldAlert size={16} className="text-gold" />
              <span className="label-section">Patrol Priority Ranking</span>
            </div>
            <span className="font-mono text-xs text-faint">Score = severity + recency weighted density</span>
          </div>

          {isLoading && (
            <div className="patrol-page__status">
              <Loader size={16} className="spin text-blue" /> Loading…
            </div>
          )}
          {error && !isLoading && (
            <div className="patrol-page__status">
              <AlertTriangle size={16} className="text-red" /> <span className="text-red">{error}</span>
            </div>
          )}

          <ol className="patrol-page__list">
            {ranked.map((c, idx) => (
              <li key={idx} className="patrol-page__row">
                <span className="patrol-page__rank font-mono text-gold">#{idx + 1}</span>
                <div className="patrol-page__row-body">
                  <span className="text-sm text-100 font-semibold">
                    <MapPin size={12} className="text-gold" /> {c.district}
                  </span>
                  <span className="text-xs text-muted">
                    {c.crime_type} · {c.count} incidents · score {c.score}
                  </span>
                </div>
              </li>
            ))}
          </ol>
        </div>
      </div>
    </div>
  );
}
