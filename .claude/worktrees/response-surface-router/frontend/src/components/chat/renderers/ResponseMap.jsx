/**
 * ResponseMap — renders map response_type (from /api/hotspots).
 * Leaflet + dark CARTO tiles. Clusters rendered as gold-ringed circles.
 *
 * design.md: "gold-ringed circles sized by case count, not raw heat blobs"
 */

import { useEffect, useRef } from 'react';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import './ResponseRenderers.css';

// Dark tile layer — CARTO dark matter (free, no API key needed)
const TILE_URL = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
const TILE_ATTR =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>';

// Karnataka approximate center
const KARNATAKA_CENTER = [15.3173, 75.7139];
const DEFAULT_ZOOM = 7;

export default function ResponseMap({ envelope }) {
  const { data } = envelope;
  const mapRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Initialize map
    const map = L.map(containerRef.current, {
      center: KARNATAKA_CENTER,
      zoom: DEFAULT_ZOOM,
      zoomControl: true,
      attributionControl: true,
    });

    L.tileLayer(TILE_URL, {
      attribution: TILE_ATTR,
      maxZoom: 18,
    }).addTo(map);

    mapRef.current = map;

    // Render clusters if available
    const clusters = data?.clusters || data?.hotspots || [];
    if (Array.isArray(clusters) && clusters.length > 0) {
      const bounds = [];

      clusters.forEach((cluster) => {
        const lat = cluster.latitude ?? cluster.lat ?? cluster.center_lat;
        const lng = cluster.longitude ?? cluster.lng ?? cluster.lon ?? cluster.center_lng;

        if (lat == null || lng == null) return;

        const caseCount =
          cluster.case_count ??
          cluster.count ??
          (Array.isArray(cluster.case_ids) ? cluster.case_ids.length : 1);

        // Size the circle by case count — min 6px, max 30px
        const radius = Math.min(30, Math.max(6, Math.sqrt(caseCount) * 4));

        const circle = L.circleMarker([lat, lng], {
          radius,
          color: '#C6A24D',         // ksp-gold ring
          weight: 2,
          fillColor: 'rgba(198, 162, 77, 0.15)',
          fillOpacity: 0.6,
        }).addTo(map);

        // Tooltip with case count
        const tooltipContent = [
          `<strong>${caseCount} case${caseCount !== 1 ? 's' : ''}</strong>`,
          cluster.district ? `District: ${cluster.district}` : '',
          cluster.crime_type ? `Type: ${cluster.crime_type}` : '',
        ]
          .filter(Boolean)
          .join('<br/>');

        circle.bindTooltip(tooltipContent, {
          className: 'ksp-map-tooltip',
          direction: 'top',
        });

        bounds.push([lat, lng]);
      });

      // Fit bounds if we have markers
      if (bounds.length > 0) {
        map.fitBounds(bounds, { padding: [30, 30], maxZoom: 12 });
      }
    }

    // Handle map in collapsed panels — invalidate size when visible
    const observer = new ResizeObserver(() => {
      map.invalidateSize();
    });
    observer.observe(containerRef.current);

    return () => {
      observer.disconnect();
      map.remove();
    };
  }, [data]);

  return (
    <div className="response-map">
      <div className="response-map__label label-section">
        Hotspot Map — Karnataka
      </div>
      <div
        ref={containerRef}
        className="response-map__container"
        role="img"
        aria-label="Karnataka crime hotspot map"
      />
    </div>
  );
}
