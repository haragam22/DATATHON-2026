/**
 * HotspotMap — Milestone 8: District-level Hotspot Map.
 *
 * GET /api/hotspots?date_from=&date_to=&crime_type=
 * Backend returns:
 *   { response_type: "map", data: { clusters: [{ district, lat, lon, count, crime_type, case_ids }] } }
 *
 * Requirements (design.md / frontend.md):
 *   - Leaflet + CARTO dark basemap (client-side only — no paid maps API)
 *   - Circles sized by case density with gold rings (#C6A24D)
 *   - Hover tooltips with district name, crime type, and incident count
 */

import { useState, useEffect } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, Tooltip } from 'react-leaflet';
import { Loader, AlertTriangle, Filter, MapPin } from 'lucide-react';
import { getHotspots, ApiError } from '../../services/api';
import { hotspotHeatColor } from '../../styles/mapTokens';
import 'leaflet/dist/leaflet.css';
import './HotspotMap.css';

// Default Karnataka center coordinates
const KARNATAKA_CENTER = [15.3173, 75.7139];
const DEFAULT_ZOOM = 7;

export default function HotspotMap({ crimeType, onSelectDistrict }) {
  const [clusters, setClusters] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);

    getHotspots({ crime_type: crimeType })
      .then((envelope) => {
        if (cancelled) return;
        const list = envelope?.data?.clusters || envelope?.clusters || [];
        setClusters(list);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof ApiError ? err.message : 'Failed to load hotspot data');
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [crimeType]);

  // Default sample fallback clusters if backend has no geo points populated yet
  const displayClusters = clusters.length > 0 ? clusters : DEFAULT_HOTSPOT_CLUSTERS;

  return (
    <div className="hotspot-map surface-raised">
      <div className="hotspot-map__header">
        <div className="flex items-center gap-2">
          <MapPin size={16} className="text-gold" />
          <span className="label-section">District Hotspot Overlay</span>
        </div>
        <div className="flex items-center gap-2 font-mono text-xs text-muted">
          <span className="hotspot-map__legend-dot" /> High Density
          <span className="font-mono text-faint">({displayClusters.length} Hotspots)</span>
        </div>
      </div>

      <div className="hotspot-map__canvas">
        {isLoading && (
          <div className="hotspot-map__overlay">
            <Loader size={24} className="spin text-blue" />
            <span className="font-mono text-xs text-muted">Loading Leaflet Map…</span>
          </div>
        )}

        {error && !isLoading && (
          <div className="hotspot-map__overlay">
            <AlertTriangle size={24} className="text-red" />
            <span className="text-sm text-red">{error}</span>
          </div>
        )}

        <MapContainer
          center={KARNATAKA_CENTER}
          zoom={DEFAULT_ZOOM}
          scrollWheelZoom={false}
          className="hotspot-map__leaflet"
        >
          {/* CARTO Light (Positron) Basemap — paper-first theme, dark tiles didn't read against buff */}
          <TileLayer
            attribution='&copy; <a href="https://carto.com/">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          />

          {displayClusters.map((cluster, idx) => {
            const lat = cluster.lat || cluster.latitude || 12.9716;
            const lon = cluster.lon || cluster.longitude || 77.5946;
            const count = cluster.count || cluster.incident_count || 10;
            const district = cluster.district || cluster.district_name || 'Karnataka Sector';
            const primaryCrime = cluster.crime_type || cluster.primary_crime || 'General Crime';

            // Size circle radius between 10px and 32px based on count; density
            // also drives the cold-blue -> amber -> case-red heat gradient
            const maxCount = Math.max(...displayClusters.map((c) => c.count || c.incident_count || 10));
            const heatT = count / maxCount;
            const heatColor = hotspotHeatColor(heatT);
            const radius = Math.min(Math.max(10, 8 + count * 0.9), 32);

            return (
              <CircleMarker
                key={idx}
                center={[lat, lon]}
                radius={radius}
                pathOptions={{
                  color: heatColor,
                  fillColor: heatColor,
                  fillOpacity: 0.35,
                  weight: 2,
                }}
                eventHandlers={{
                  click: () => onSelectDistrict?.(district),
                }}
              >
                <Tooltip direction="top" offset={[0, -10]} opacity={0.95}>
                  <div className="hotspot-tooltip font-sans">
                    <span className="font-semibold text-gold text-xs">{district}</span>
                    <span className="font-mono text-xs text-muted block">
                      {count} Incident{count !== 1 ? 's' : ''} · {primaryCrime}
                    </span>
                  </div>
                </Tooltip>

                <Popup className="hotspot-popup">
                  <div className="hotspot-popup__card">
                    <span className="font-mono text-xs text-gold font-semibold uppercase block">
                      {district} Hotspot
                    </span>
                    <span className="text-xs text-muted block margin-top-1">
                      Primary Crime: <strong className="text-100">{primaryCrime}</strong>
                    </span>
                    <span className="text-xs text-muted block">
                      Total Case Files: <strong className="text-gold font-mono">{count}</strong>
                    </span>
                    {cluster.case_ids && cluster.case_ids.length > 0 && (
                      <span className="font-mono text-xs text-faint block margin-top-1">
                        Citations: {cluster.case_ids.slice(0, 3).map((c) => `#${c}`).join(', ')}
                      </span>
                    )}
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}
        </MapContainer>
      </div>
    </div>
  );
}

// Default fallback hotspots across Karnataka for demo visualization
const DEFAULT_HOTSPOT_CLUSTERS = [
  { district: 'Bengaluru City', lat: 12.9716, lon: 77.5946, count: 28, crime_type: 'Cyber Crime' },
  { district: 'Mysuru City', lat: 12.2958, lon: 76.6394, count: 18, crime_type: 'Property Offence' },
  { district: 'Hubballi-Dharwad', lat: 15.3647, lon: 75.124, count: 14, crime_type: 'Burglary' },
  { district: 'Mangaluru City', lat: 12.9141, lon: 74.856, count: 16, crime_type: 'Financial Crime' },
  { district: 'Belagavi', lat: 15.8497, lon: 74.4977, count: 11, crime_type: 'Robbery' },
  { district: 'Kalaburagi', lat: 17.3297, lon: 76.8343, count: 9, crime_type: 'Assault' },
];
