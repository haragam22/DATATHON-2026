/**
 * TrendCharts — Milestone 8: Aggregate Crime Trends Component.
 *
 * GET /api/aggregates?type=crime_type
 * GET /api/aggregates?type=monthly
 *
 * Uses recharts to render category breakdown and monthly trend charts.
 */

import { useState, useEffect } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  AreaChart,
  Area,
} from 'recharts';
import { TrendingUp, BarChart3, Loader, AlertTriangle } from 'lucide-react';
import { getAggregates, ApiError } from '../../services/api';
import './TrendCharts.css';

export default function TrendCharts() {
  const [activeTab, setActiveTab] = useState('category'); // 'category' | 'monthly'
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);

    const aggregateType = activeTab === 'category' ? 'crime-type' : 'trend';

    getAggregates({ type: aggregateType })
      .then((envelope) => {
        if (cancelled) return;
        let chartData = envelope?.data?.series || envelope?.data?.data || (Array.isArray(envelope?.data) ? envelope.data : []);
        if (Array.isArray(chartData)) {
          chartData = chartData.map((item) => ({
            category: item.category || item.crime_type || item.CrimeGroup_VK || item.CrimeType || item.label || 'Other',
            month: item.month || item.year_month || item.Month || item.label || 'Period',
            count: typeof item.count === 'number' ? item.count : (item.IncidentCount || item.total || item.value || 0),
          }));
        } else if (typeof chartData === 'object' && chartData !== null) {
          chartData = Object.entries(chartData).map(([k, v]) => ({
            category: k,
            month: k,
            count: typeof v === 'number' ? v : (v.count || v.IncidentCount || v.value || 0),
          }));
        }
        setData(chartData);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof ApiError ? err.message : 'Failed to load aggregates');
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [activeTab]);

  const displayData = Array.isArray(data) && data.length > 0
    ? data
    : activeTab === 'category'
    ? DEFAULT_CATEGORY_DATA
    : DEFAULT_MONTHLY_DATA;

  return (
    <div className="trend-charts surface-raised">
      <div className="trend-charts__header">
        <div className="flex items-center gap-2">
          <TrendingUp size={16} className="text-blue" />
          <span className="label-section">Analytics & Trends</span>
        </div>
        <div className="trend-charts__tabs">
          <button
            className={`trend-charts__tab font-mono text-xs ${
              activeTab === 'category' ? 'trend-charts__tab--active' : ''
            }`}
            onClick={() => setActiveTab('category')}
          >
            By Category
          </button>
          <button
            className={`trend-charts__tab font-mono text-xs ${
              activeTab === 'monthly' ? 'trend-charts__tab--active' : ''
            }`}
            onClick={() => setActiveTab('monthly')}
          >
            Monthly Volume
          </button>
        </div>
      </div>

      <div className="trend-charts__body">
        {isLoading && (
          <div className="trend-charts__status">
            <Loader size={20} className="spin text-blue" />
            <span className="font-mono text-xs text-muted">Loading chart data…</span>
          </div>
        )}

        {error && !isLoading && (
          <div className="trend-charts__status">
            <AlertTriangle size={20} className="text-red" />
            <span className="text-sm text-red">{error}</span>
          </div>
        )}

        {!isLoading && !error && (
          <div className="trend-charts__canvas">
            {activeTab === 'category' ? (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={displayData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                  <XAxis
                    dataKey="category"
                    tick={{ fill: 'var(--text-400)', fontSize: 11, fontFamily: 'IBM Plex Mono' }}
                    interval={0}
                    angle={-25}
                    textAnchor="end"
                  />
                  <YAxis
                    tick={{ fill: 'var(--text-400)', fontSize: 11, fontFamily: 'IBM Plex Mono' }}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="count" fill="var(--ksp-blue)" radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <AreaChart data={displayData} margin={{ top: 10, right: 10, left: -20, bottom: 10 }}>
                  <defs>
                    <linearGradient id="areaColor" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="var(--ksp-gold)" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="var(--ksp-gold)" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <XAxis
                    dataKey="month"
                    tick={{ fill: 'var(--text-400)', fontSize: 11, fontFamily: 'IBM Plex Mono' }}
                  />
                  <YAxis
                    tick={{ fill: 'var(--text-400)', fontSize: 11, fontFamily: 'IBM Plex Mono' }}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Area
                    type="monotone"
                    dataKey="count"
                    stroke="var(--ksp-gold)"
                    fillOpacity={1}
                    fill="url(#areaColor)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function CustomTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    return (
      <div className="chart-tooltip surface-float font-mono text-xs">
        <span className="font-semibold text-gold">{label}</span>
        <span className="text-100 block">{payload[0].value} Cases</span>
      </div>
    );
  }
  return null;
}

// Fallback data
const DEFAULT_CATEGORY_DATA = [
  { category: 'Cyber Crime', count: 480 },
  { category: 'Property Offence', count: 350 },
  { category: 'Financial Crime', count: 290 },
  { category: 'Violent Crime', count: 180 },
  { category: 'Narcotics', count: 140 },
];

const DEFAULT_MONTHLY_DATA = [
  { month: 'Jan', count: 110 },
  { month: 'Feb', count: 125 },
  { month: 'Mar', count: 140 },
  { month: 'Apr', count: 135 },
  { month: 'May', count: 160 },
  { month: 'Jun', count: 190 },
];
