/**
 * ResponseNetwork — renders network response_type (from /api/network/<case_id>).
 * Force-directed graph using react-force-graph-2d.
 *
 * design.md:
 *   - Nodes: circle, initials avatar, ring colored by role
 *     accused = signal-red, victim = ksp-blue, associate/witness = text-400
 *   - Edges: thin line-700, labeled on hover only
 *   - Selected node: ksp-gold glow ring
 *   - NEVER photos — initials in a ring only
 */

import { useRef, useState, useMemo, useCallback, useEffect } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import './ResponseRenderers.css';

// Role → ring color mapping (from design.md)
const ROLE_COLORS = {
  accused: '#B8493A',    // signal-red
  suspect: '#B8493A',
  victim: '#2C5AA0',     // ksp-blue
  complainant: '#2C5AA0',
  associate: '#96A2C0',  // text-400
  witness: '#96A2C0',
  default: '#96A2C0',
};

function getRoleColor(role) {
  if (!role) return ROLE_COLORS.default;
  const r = role.toLowerCase();
  return ROLE_COLORS[r] || ROLE_COLORS.default;
}

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

export default function ResponseNetwork({ envelope }) {
  const { data } = envelope;
  const graphRef = useRef(null);
  const containerRef = useRef(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [hoveredLink, setHoveredLink] = useState(null);
  const [dimensions, setDimensions] = useState({ width: 600, height: 400 });

  // Parse graph data
  const graphData = useMemo(() => parseGraphData(data), [data]);

  // Observe container resize
  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 0 && height > 0) {
          setDimensions({ width, height: Math.max(height, 350) });
        }
      }
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  // Custom node renderer — initials in a ring
  const paintNode = useCallback(
    (node, ctx) => {
      const { x, y } = node;
      const r = 16;
      const isSelected = selectedNode?.id === node.id;
      const ringColor = getRoleColor(node.role);
      const initials = getInitials(node.name || node.label || node.id);

      // Glow for selected node
      if (isSelected) {
        ctx.beginPath();
        ctx.arc(x, y, r + 4, 0, 2 * Math.PI);
        ctx.fillStyle = 'rgba(198, 162, 77, 0.25)';
        ctx.fill();
        ctx.strokeStyle = '#C6A24D'; // ksp-gold
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      // Node background
      ctx.beginPath();
      ctx.arc(x, y, r, 0, 2 * Math.PI);
      ctx.fillStyle = '#161F35'; // ink-800
      ctx.fill();

      // Ring
      ctx.strokeStyle = ringColor;
      ctx.lineWidth = 2;
      ctx.stroke();

      // Initials
      ctx.fillStyle = '#EAEEF7'; // text-100
      ctx.font = `500 10px 'IBM Plex Mono', monospace`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(initials, x, y);
    },
    [selectedNode]
  );

  // Custom link renderer
  const paintLink = useCallback(
    (link, ctx) => {
      const isHovered = hoveredLink === link;
      ctx.strokeStyle = isHovered ? '#96A2C0' : '#2B3757'; // text-400 : line-700
      ctx.lineWidth = isHovered ? 1.5 : 0.8;
      ctx.beginPath();
      ctx.moveTo(link.source.x, link.source.y);
      ctx.lineTo(link.target.x, link.target.y);
      ctx.stroke();

      // Edge label on hover only (design.md: "don't clutter at rest")
      if (isHovered && link.label) {
        const midX = (link.source.x + link.target.x) / 2;
        const midY = (link.source.y + link.target.y) / 2;
        ctx.fillStyle = '#96A2C0';
        ctx.font = `400 10px 'IBM Plex Mono', monospace`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(link.label, midX, midY - 6);
      }
    },
    [hoveredLink]
  );

  if (!graphData.nodes.length) {
    return (
      <div className="response-network">
        <p className="text-muted text-sm">No network data available.</p>
      </div>
    );
  }

  return (
    <div className="response-network">
      <div className="response-network__header">
        <span className="label-section">Investigation Network</span>
        <div className="response-network__legend">
          <LegendItem color={ROLE_COLORS.accused} label="Accused" />
          <LegendItem color={ROLE_COLORS.victim} label="Victim" />
          <LegendItem color={ROLE_COLORS.associate} label="Associate/Witness" />
        </div>
      </div>
      <div ref={containerRef} className="response-network__canvas">
        <ForceGraph2D
          ref={graphRef}
          graphData={graphData}
          width={dimensions.width}
          height={dimensions.height}
          backgroundColor="#0A0F1C"
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
          onNodeClick={(node) => setSelectedNode(node)}
          onLinkHover={(link) => setHoveredLink(link)}
          onBackgroundClick={() => setSelectedNode(null)}
          cooldownTicks={80}
          d3AlphaDecay={0.04}
          d3VelocityDecay={0.3}
        />
      </div>
      {selectedNode && (
        <div className="response-network__detail surface-raised">
          <span className="font-mono text-xs text-gold font-semibold">
            {selectedNode.name || selectedNode.label || `Entity #${selectedNode.id}`}
          </span>
          {selectedNode.role && (
            <span className="chip chip-muted uppercase text-xs">{selectedNode.role}</span>
          )}
        </div>
      )}
    </div>
  );
}

// ── Legend sub-component ──

function LegendItem({ color, label }) {
  return (
    <span className="response-network__legend-item text-xs text-muted">
      <span
        className="response-network__legend-dot"
        style={{ borderColor: color }}
        aria-hidden="true"
      />
      {label}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Parse network data from various backend shapes
// ---------------------------------------------------------------------------

function parseGraphData(data) {
  if (!data) return { nodes: [], links: [] };

  // If data already has nodes/links (or edges)
  let nodes = data.nodes || data.vertices || [];
  let links = data.links || data.edges || [];

  // Normalize nodes
  nodes = nodes.map((n) => ({
    id: n.id ?? n.node_id ?? n.AccusedMasterID ?? n.VictimMasterID,
    name: n.name ?? n.label ?? n.AccusedName ?? n.VictimName ?? '',
    role: n.role ?? n.type ?? n.node_type ?? 'default',
    ...n,
  }));

  // Normalize links
  links = links.map((l) => ({
    source: l.source ?? l.from ?? l.source_id,
    target: l.target ?? l.to ?? l.target_id,
    label: l.label ?? l.relationship ?? l.type ?? '',
    ...l,
  }));

  return { nodes, links };
}
