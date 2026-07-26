/**
 * InvestigationBoard — Milestone 5: Dedicated force-directed network graph view.
 *
 * GET /api/network/<case_id>
 * Backend returns: { nodes: [{id, label, is_seed}], edges: [{source, target, weight, shared_case_ids}], case_ids }
 *
 * Features per design.md:
 *   - Force-directed graph on ink-950 canvas (#0A0F1C)
 *   - Initials-in-a-ring avatars (NEVER photos or illustrations)
 *   - Seed accused: signal-red ring, Expanded co-accused: text-400 ring
 *   - Hover edge labels (shared case count in 10px Plex Mono)
 *   - Selected node gets ksp-gold glow ring
 *   - Case ID input for quick investigation
 *   - Zoom controls (in/out/fit)
 */

import { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { Search, Loader, RefreshCw, ZoomIn, ZoomOut, Maximize2, UserCheck, AlertTriangle, Network } from 'lucide-react';
import { getNetwork, ApiError } from '../../services/api';
import './InvestigationBoard.css';

// Role → ring color mapping (from design.md)
const ROLE_COLORS = {
  seed:      '#B23A34',   // case red — seed accused from the queried case
  expanded:  '#4A5A6A',   // slate steel — co-accused pulled in via recidivism expansion
  selected:  '#E8A33D',   // evidence amber — currently focused entity
};

function getInitials(name) {
  if (!name) return '?';
  return name
    .split(/\s+/)
    .filter(Boolean)
    .map((w) => w[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();
}

export default function InvestigationBoard({ initialCaseId = 1, onSelectEntity }) {
  const [caseIdInput, setCaseIdInput] = useState(String(initialCaseId));
  const [activeCaseId, setActiveCaseId] = useState(initialCaseId);
  const [networkData, setNetworkData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [hoveredLink, setHoveredLink] = useState(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 500 });

  const graphRef = useRef(null);
  const containerRef = useRef(null);

  // Fetch network data when activeCaseId changes
  useEffect(() => {
    if (!activeCaseId) return;
    let cancelled = false;

    setIsLoading(true);
    setError(null);
    setSelectedNode(null);

    getNetwork(activeCaseId)
      .then((envelope) => {
        if (cancelled) return;
        // Backend returns envelope { response_type, data, ... }
        // data is { nodes, edges, case_ids }
        setNetworkData(envelope?.data ?? envelope);
      })
      .catch((err) => {
        if (cancelled) return;
        const msg = err instanceof ApiError ? err.message : 'Failed to load network graph';
        setError(msg);
        setNetworkData(null);
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => { cancelled = true; };
  }, [activeCaseId]);

  // Observe container resize
  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 0 && height > 0) {
          setDimensions({ width, height: Math.max(height, 400) });
        }
      }
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  // Parse graph data — match actual backend shape:
  //   nodes: [{id: int, label: str, is_seed: bool}]
  //   edges: [{source: int, target: int, weight: int, shared_case_ids: int[]}]
  const graphData = useMemo(() => {
    if (!networkData) return { nodes: [], links: [] };

    const rawNodes = networkData.nodes || [];
    const rawEdges = networkData.edges || networkData.links || [];

    const nodes = rawNodes.map((n) => ({
      id: String(n.id),
      name: n.label || n.name || `Entity #${n.id}`,
      isSeed: Boolean(n.is_seed),
    }));

    const links = rawEdges.map((e) => ({
      source: String(e.source),
      target: String(e.target),
      weight: e.weight || 1,
      sharedCaseIds: e.shared_case_ids || [],
      label: e.weight > 1
        ? `${e.weight} shared cases`
        : e.shared_case_ids?.length
          ? `Case #${e.shared_case_ids[0]}`
          : '',
    }));

    return { nodes, links };
  }, [networkData]);

  // Handle case search
  const handleSearch = (e) => {
    e.preventDefault();
    const id = parseInt(caseIdInput.trim(), 10);
    if (!isNaN(id) && id > 0) {
      setActiveCaseId(id);
    }
  };

  // Node painter — initials in a ring (NEVER photos)
  const paintNode = useCallback(
    (node, ctx) => {
      const { x, y } = node;
      const r = 16;
      const isSelected = selectedNode?.id === node.id;
      const ringColor = isSelected
        ? ROLE_COLORS.selected
        : node.isSeed
          ? ROLE_COLORS.seed
          : ROLE_COLORS.expanded;
      const initials = getInitials(node.name);

      // Selected node: crisp outer ring, flat — no glow/blur (investigation
      // board stays flat per design.md, this is a focus indicator not a light)
      if (isSelected) {
        ctx.beginPath();
        ctx.arc(x, y, r + 5, 0, 2 * Math.PI);
        ctx.strokeStyle = '#E8A33D';
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }

      // Background — the board stays a dark control-room canvas by design
      // (see "Dark-Canvas Exception" in design.md), independent of theme
      ctx.beginPath();
      ctx.arc(x, y, r, 0, 2 * Math.PI);
      ctx.fillStyle = '#1C2C4A'; // dark-theme raised surface
      ctx.fill();

      // Outer ring
      ctx.strokeStyle = ringColor;
      ctx.lineWidth = 2.5;
      ctx.stroke();

      // Initials text
      ctx.fillStyle = '#EAECEF'; // case paper
      ctx.font = `600 11px 'IBM Plex Mono', monospace`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(initials, x, y);
    },
    [selectedNode]
  );

  // Link painter — edge label on hover only (design.md: don't clutter at rest)
  const paintLink = useCallback(
    (link, ctx) => {
      const isHovered = hoveredLink === link;
      ctx.strokeStyle = isHovered ? '#9FB0C0' : '#4A5A6A'; // text-400 (dark) : slate steel
      ctx.lineWidth = isHovered ? 2 : Math.min(link.weight || 1, 3) * 0.6;
      ctx.beginPath();
      ctx.moveTo(link.source.x, link.source.y);
      ctx.lineTo(link.target.x, link.target.y);
      ctx.stroke();

      if (isHovered && link.label) {
        const midX = (link.source.x + link.target.x) / 2;
        const midY = (link.source.y + link.target.y) / 2;
        ctx.fillStyle = '#EAECEF';
        ctx.font = `500 10px 'IBM Plex Mono', monospace`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(link.label, midX, midY - 8);
      }
    },
    [hoveredLink]
  );

  // Zoom controls
  const handleZoomIn = () => {
    const fg = graphRef.current;
    if (fg) fg.zoom(fg.zoom() * 1.3, 300);
  };
  const handleZoomOut = () => {
    const fg = graphRef.current;
    if (fg) fg.zoom(fg.zoom() / 1.3, 300);
  };
  const handleFit = () => {
    const fg = graphRef.current;
    if (fg) fg.zoomToFit(400, 40);
  };

  const handleNodeClick = useCallback((node) => {
    setSelectedNode(node);
    onSelectEntity?.(node);
  }, [onSelectEntity]);

  return (
    <div className="investigation-board surface-base">
      {/* ── Header Toolbar ── */}
      <div className="investigation-board__toolbar">
        <div className="investigation-board__title">
          <Network size={16} className="text-blue" />
          <span className="label-section">Investigation Board</span>
          <span className="font-mono text-xs text-faint">Case #{activeCaseId}</span>
        </div>

        <form onSubmit={handleSearch} className="investigation-board__search-form">
          <div className="investigation-board__input-wrapper">
            <Search size={14} className="investigation-board__search-icon" />
            <input
              type="number"
              min="1"
              className="investigation-board__input font-mono"
              value={caseIdInput}
              onChange={(e) => setCaseIdInput(e.target.value)}
              placeholder="Case ID..."
              aria-label="Case ID"
            />
          </div>
          <button
            type="submit"
            className="btn btn-primary font-mono text-xs"
            disabled={isLoading || !caseIdInput}
          >
            {isLoading ? <Loader size={14} className="spin" /> : 'Load'}
          </button>
        </form>

        <div className="investigation-board__legend">
          <LegendDot color={ROLE_COLORS.seed} label="Seed Accused" />
          <LegendDot color={ROLE_COLORS.expanded} label="Co-Accused" />
          <LegendDot color={ROLE_COLORS.selected} label="Active Focus" glow />
        </div>
      </div>

      {/* ── Graph Canvas Area ── */}
      <div ref={containerRef} className="investigation-board__canvas-container">
        {isLoading && (
          <div className="investigation-board__overlay">
            <Loader size={28} className="spin text-blue" />
            <span className="font-mono text-xs text-muted">
              Loading Case #{activeCaseId} network graph…
            </span>
          </div>
        )}

        {error && !isLoading && (
          <div className="investigation-board__overlay">
            <AlertTriangle size={24} className="text-red" />
            <span className="text-sm text-red">{error}</span>
            <button
              className="btn btn-ghost text-xs font-mono"
              onClick={() => { setActiveCaseId(0); setTimeout(() => setActiveCaseId(activeCaseId), 0); }}
            >
              <RefreshCw size={12} /> Retry
            </button>
          </div>
        )}

        {!isLoading && !error && graphData.nodes.length === 0 && (
          <div className="investigation-board__overlay">
            <Network size={28} className="text-faint" />
            <p className="text-muted text-sm">No network entities found for Case #{activeCaseId}.</p>
            <span className="text-faint text-xs font-mono">Try a case with accused records.</span>
          </div>
        )}

        {!isLoading && !error && graphData.nodes.length > 0 && (
          <>
            <ForceGraph2D
              ref={graphRef}
              graphData={graphData}
              width={dimensions.width}
              height={dimensions.height}
              backgroundColor="#16233D"
              nodeCanvasObject={paintNode}
              nodePointerAreaPaint={(node, color, ctx) => {
                ctx.beginPath();
                ctx.arc(node.x, node.y, 18, 0, 2 * Math.PI);
                ctx.fillStyle = color;
                ctx.fill();
              }}
              linkCanvasObject={paintLink}
              linkPointerAreaPaint={(link, color, ctx) => {
                ctx.strokeStyle = color;
                ctx.lineWidth = 6;
                ctx.beginPath();
                ctx.moveTo(link.source.x, link.source.y);
                ctx.lineTo(link.target.x, link.target.y);
                ctx.stroke();
              }}
              onNodeClick={handleNodeClick}
              onLinkHover={(link) => setHoveredLink(link)}
              onBackgroundClick={() => setSelectedNode(null)}
              cooldownTicks={100}
              d3AlphaDecay={0.03}
              d3VelocityDecay={0.3}
            />

            {/* Floating Zoom Controls */}
            <div className="investigation-board__controls surface-float">
              <button className="btn-icon" onClick={handleZoomIn} title="Zoom In" aria-label="Zoom In">
                <ZoomIn size={14} />
              </button>
              <button className="btn-icon" onClick={handleZoomOut} title="Zoom Out" aria-label="Zoom Out">
                <ZoomOut size={14} />
              </button>
              <button className="btn-icon" onClick={handleFit} title="Fit to Screen" aria-label="Fit to Screen">
                <Maximize2 size={14} />
              </button>
            </div>
          </>
        )}
      </div>

      {/* ── Selected Node Detail (bottom-left) ── */}
      {selectedNode && (
        <div className="investigation-board__detail surface-raised animate-fade-in">
          <div className="investigation-board__detail-header">
            <UserCheck size={16} className="text-gold" />
            <span className="font-mono text-sm font-semibold text-gold">
              {selectedNode.name || `Entity #${selectedNode.id}`}
            </span>
            <span className="chip chip-muted uppercase text-xs">
              {selectedNode.isSeed ? 'Seed Accused' : 'Co-Accused'}
            </span>
          </div>
          <p className="text-xs text-muted" style={{ marginTop: 'var(--space-1)' }}>
            AccusedMasterID: <span className="font-mono">{selectedNode.id}</span>
          </p>
        </div>
      )}
    </div>
  );
}

function LegendDot({ color, label, glow = false }) {
  return (
    <span className="investigation-board__legend-item text-xs text-muted">
      <span
        className={`investigation-board__legend-dot ${glow ? 'investigation-board__legend-dot--glow' : ''}`}
        style={{ borderColor: color }}
        aria-hidden="true"
      />
      {label}
    </span>
  );
}
