/**
 * PcrDispatchPanel — Feature 2: Automated PCR dispatch simulation.
 *
 * GET /api/pcr-dispatch — stateless, backend samples a fresh set of
 * "immediate priority" cases and fabricates a van/ETA each call. The 30s
 * cadence lives entirely here (setInterval), not on the server.
 *
 * ponytail: separate small Leaflet instance from HotspotMap.jsx rather
 * than a shared map component — duplicated MapContainer/TileLayer config.
 * Extract into a shared KarnatakaMap base component if a third map (SOS
 * pins) needs the same shell.
 */

import { useState, useEffect } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, Tooltip } from 'react-leaflet';
import { Loader, AlertTriangle, Truck } from 'lucide-react';
import { getPcrDispatch, ApiError } from '../../services/api';
import { SIGNAL_AMBER } from '../../styles/mapTokens';
import 'leaflet/dist/leaflet.css';
import './PcrDispatchPanel.css';

const KARNATAKA_CENTER = [15.3173, 75.7139];
const DEFAULT_ZOOM = 7;
const POLL_INTERVAL_MS = 30_000;

export default function PcrDispatchPanel() {
  const [dispatches, setDispatches] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    const fetchDispatches = () => {
      setIsLoading(true);
      setError(null);
      getPcrDispatch()
        .then((envelope) => {
          if (cancelled) return;
          setDispatches(envelope?.data?.dispatches || []);
        })
        .catch((err) => {
          if (cancelled) return;
          setError(err instanceof ApiError ? err.message : 'Failed to load PCR dispatch data');
        })
        .finally(() => {
          if (!cancelled) setIsLoading(false);
        });
    };

    fetchDispatches();
    const intervalId = setInterval(fetchDispatches, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
  }, []);

  return (
    <div className="pcr-dispatch-panel surface-raised">
      <div className="pcr-dispatch-panel__header">
        <div className="flex items-center gap-2">
          <Truck size={16} className="text-gold" />
          <span className="label-section">PCR Dispatch — Live Simulation</span>
        </div>
        <span className="font-mono text-xs text-faint">
          {isLoading ? 'Refreshing…' : `${dispatches.length} vans en route`} · every 30s
        </span>
      </div>

      <div className="pcr-dispatch-panel__body">
        <div className="pcr-dispatch-panel__canvas">
          {error && (
            <div className="pcr-dispatch-panel__overlay">
              <AlertTriangle size={20} className="text-red" />
              <span className="text-sm text-red">{error}</span>
            </div>
          )}
          <MapContainer center={KARNATAKA_CENTER} zoom={DEFAULT_ZOOM} scrollWheelZoom={false} className="pcr-dispatch-panel__leaflet">
            <TileLayer
              attribution='&copy; <a href="https://carto.com/">CARTO</a>'
              url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
            />
            {dispatches.map((d) => (
              <CircleMarker
                key={`${d.case_id}-${d.van_id}`}
                center={[d.lat, d.lon]}
                radius={9}
                pathOptions={{ color: SIGNAL_AMBER, fillColor: SIGNAL_AMBER, fillOpacity: 0.6, weight: 2 }}
              >
                <Tooltip direction="top" offset={[0, -8]} opacity={0.95}>
                  <div className="font-mono text-xs">
                    <strong>{d.van_id}</strong> → Case #{d.case_id} · ETA {d.eta_minutes}m
                  </div>
                </Tooltip>
                <Popup>
                  <div className="font-mono text-xs">
                    <div><strong>{d.van_id}</strong></div>
                    <div>Case #{d.case_id}</div>
                    <div>ETA: {d.eta_minutes} min</div>
                    <div>Dispatched: {new Date(d.dispatched_at).toLocaleTimeString()}</div>
                  </div>
                </Popup>
              </CircleMarker>
            ))}
          </MapContainer>
        </div>

        <ul className="pcr-dispatch-panel__list">
          {isLoading && dispatches.length === 0 && (
            <li className="pcr-dispatch-panel__empty">
              <Loader size={14} className="spin" /> Loading dispatches…
            </li>
          )}
          {dispatches.map((d) => (
            <li key={`${d.case_id}-${d.van_id}`} className="pcr-dispatch-panel__row">
              <span className="font-mono text-xs text-gold">{d.van_id}</span>
              <span className="text-xs text-100">Case #{d.case_id}</span>
              <span className="font-mono text-xs text-muted">ETA {d.eta_minutes}m</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
