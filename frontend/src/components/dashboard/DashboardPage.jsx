/**
 * DashboardPage — Milestone 8: Opening Landing Screen.
 *
 * Requirements (frontend.md / idea.md):
 *   - The opening screen beat for the demo
 *   - District-level hotspot map
 *   - Recent trend charts
 *   - Patrol-recommendation feed
 *   - Quick-action shortcuts into Chat and Investigation Board
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Shield,
  Activity,
  AlertTriangle,
  MapPin,
  TrendingUp,
  MessageSquare,
  Network,
  ChevronRight,
  Zap,
} from 'lucide-react';
import HotspotMap from './HotspotMap';
import TrendCharts from './TrendCharts';
import './DashboardPage.css';

export default function DashboardPage() {
  const navigate = useNavigate();
  const [selectedDistrict, setSelectedDistrict] = useState(null);

  const handleRecommendationClick = (promptText) => {
    navigate('/chat', { state: { initialPrompt: promptText } });
  };

  const handleInvestigateClick = (caseId) => {
    navigate('/investigate', { state: { caseId } });
  };

  return (
    <div className="dashboard-page">
      {/* ── Top Bar: Hero KPI Cards ── */}
      <div className="dashboard-page__kpis">
        <KpiCard
          label="Total Incidents (YTD)"
          value="1,450"
          sub="Indexed across Karnataka"
          icon={Activity}
          accentColor="var(--ksp-blue)"
        />
        <KpiCard
          label="High-Gravity Ratio"
          value="24.8%"
          sub="Murder / Dacoity / Cyber"
          icon={AlertTriangle}
          accentColor="var(--signal-amber)"
        />
        <KpiCard
          label="Active Hotspots"
          value="6 Districts"
          sub="Bengaluru, Mysuru, Hubballi..."
          icon={MapPin}
          accentColor="var(--ksp-gold)"
        />
        <KpiCard
          label="Resolved Networks"
          value="89.2%"
          sub="Accused-Coaccused links mapped"
          icon={Shield}
          accentColor="var(--signal-green)"
        />
      </div>

      {/* ── Main Section: Hotspot Map + Analytics ── */}
      <div className="dashboard-page__grid">
        <div className="dashboard-page__map-panel">
          <HotspotMap onSelectDistrict={(d) => setSelectedDistrict(d)} />
        </div>
        <div className="dashboard-page__analytics-panel">
          <TrendCharts />
        </div>
      </div>

      {/* ── Bottom Section: Patrol Recommendation Feed ── */}
      <div className="dashboard-page__feed surface-raised">
        <div className="dashboard-page__feed-header">
          <div className="flex items-center gap-2">
            <Zap size={16} className="text-gold" />
            <span className="label-section">Tactical Patrol & Focus Recommendations</span>
          </div>
          <span className="font-mono text-xs text-faint">Auto-generated from crime density</span>
        </div>

        <div className="dashboard-page__feed-grid">
          <RecommendationCard
            title="Bengaluru City — Cyber Fraud Surge"
            desc="High cluster density detected in Electronic City. Recommend deploying cyber forensic unit."
            actionLabel="Ask AI in Chat"
            onAction={() =>
              handleRecommendationClick('Show cyber crime trends in Bengaluru City for last 6 months')
            }
          />
          <RecommendationCard
            title="Hubballi-Dharwad — Repeat Offender Network"
            desc="Accused Master #1 has 3 connected co-accused in active property cases."
            actionLabel="Open Network Board"
            onAction={() => handleInvestigateClick(1)}
          />
          <RecommendationCard
            title="Mysuru District — Property Crime Patrol"
            desc="Night-time burglary cluster identified along VV Mohalla sector."
            actionLabel="Analyze Query"
            onAction={() =>
              handleRecommendationClick('List top burglary hotspots in Mysuru district')
            }
          />
        </div>
      </div>
    </div>
  );
}

function KpiCard({ label, value, sub, icon: Icon, accentColor }) {
  return (
    <div className="kpi-card surface-raised">
      <div className="kpi-card__top">
        <span className="label-section text-xs">{label}</span>
        <Icon size={16} style={{ color: accentColor }} />
      </div>
      <div className="kpi-card__value font-mono text-xl font-semibold text-100">{value}</div>
      <div className="kpi-card__sub font-mono text-xs text-faint">{sub}</div>
    </div>
  );
}

function RecommendationCard({ title, desc, actionLabel, onAction }) {
  return (
    <div className="recommendation-card surface-float">
      <div className="recommendation-card__body">
        <span className="font-semibold text-sm text-100">{title}</span>
        <span className="text-xs text-muted block margin-top-1">{desc}</span>
      </div>
      <button
        className="btn btn-ghost font-mono text-xs recommendation-card__btn"
        onClick={onAction}
      >
        {actionLabel} <ChevronRight size={12} />
      </button>
    </div>
  );
}
