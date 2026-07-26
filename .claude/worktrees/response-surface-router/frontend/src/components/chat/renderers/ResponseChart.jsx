/**
 * ResponseChart — renders chart response_type (from /api/aggregates).
 * Uses recharts. Auto-detects appropriate chart type from data shape.
 */

import { useMemo } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';
import './ResponseRenderers.css';

// Chart color palette — ksp-blue first, then complementary muted tones
const COLORS = [
  '#2C5AA0', // ksp-blue
  '#C6A24D', // ksp-gold
  '#4C8067', // signal-green
  '#C68A3D', // signal-amber
  '#B8493A', // signal-red
  '#6B7DB3', // muted blue
  '#8B6F9E', // muted purple
  '#5E8A8A', // muted teal
];

// Recharts custom tooltip styled to match design tokens
function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip surface-float">
      <p className="chart-tooltip__label font-mono text-xs">{label}</p>
      {payload.map((entry, i) => (
        <p key={i} className="chart-tooltip__value text-sm" style={{ color: entry.color }}>
          {entry.name}: <strong>{entry.value?.toLocaleString()}</strong>
        </p>
      ))}
    </div>
  );
}

export default function ResponseChart({ envelope }) {
  const { data } = envelope;

  const { chartType, chartData, dataKeys, xKey } = useMemo(
    () => parseChartData(data),
    [data]
  );

  if (!chartData || chartData.length === 0) {
    return (
      <div className="response-chart">
        <p className="text-muted text-sm">No chart data available.</p>
      </div>
    );
  }

  return (
    <div className="response-chart">
      {data?.title && (
        <div className="response-chart__title label-section">{data.title}</div>
      )}
      <div className="response-chart__container">
        <ResponsiveContainer width="100%" height={280}>
          {chartType === 'pie' ? (
            <PieChart>
              <Pie
                data={chartData}
                dataKey={dataKeys[0]}
                nameKey={xKey}
                cx="50%"
                cy="50%"
                outerRadius={100}
                strokeWidth={1}
                stroke="var(--line-700)"
              >
                {chartData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip content={<ChartTooltip />} />
              <Legend
                wrapperStyle={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 'var(--text-xs)',
                  color: 'var(--text-400)',
                }}
              />
            </PieChart>
          ) : chartType === 'line' ? (
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--line-700)" />
              <XAxis
                dataKey={xKey}
                tick={{ fill: 'var(--text-400)', fontSize: 11, fontFamily: 'var(--font-mono)' }}
                axisLine={{ stroke: 'var(--line-700)' }}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: 'var(--text-400)', fontSize: 11, fontFamily: 'var(--font-mono)' }}
                axisLine={{ stroke: 'var(--line-700)' }}
                tickLine={false}
              />
              <Tooltip content={<ChartTooltip />} />
              {dataKeys.map((key, i) => (
                <Line
                  key={key}
                  type="monotone"
                  dataKey={key}
                  stroke={COLORS[i % COLORS.length]}
                  strokeWidth={2}
                  dot={{ r: 3, fill: COLORS[i % COLORS.length] }}
                  activeDot={{ r: 5 }}
                />
              ))}
            </LineChart>
          ) : (
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--line-700)" />
              <XAxis
                dataKey={xKey}
                tick={{ fill: 'var(--text-400)', fontSize: 11, fontFamily: 'var(--font-mono)' }}
                axisLine={{ stroke: 'var(--line-700)' }}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: 'var(--text-400)', fontSize: 11, fontFamily: 'var(--font-mono)' }}
                axisLine={{ stroke: 'var(--line-700)' }}
                tickLine={false}
              />
              <Tooltip content={<ChartTooltip />} />
              {dataKeys.map((key, i) => (
                <Bar
                  key={key}
                  dataKey={key}
                  fill={COLORS[i % COLORS.length]}
                  radius={[2, 2, 0, 0]}
                />
              ))}
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Parse chart data from various backend shapes
// ---------------------------------------------------------------------------

function parseChartData(data) {
  if (!data) return { chartType: 'bar', chartData: [], dataKeys: [], xKey: 'name' };

  // If data already has chart_data / chart_type (structured by backend)
  if (data.chart_data && Array.isArray(data.chart_data)) {
    const xKey = data.x_key || detectXKey(data.chart_data[0]);
    const dataKeys = data.data_keys || detectDataKeys(data.chart_data[0], xKey);
    const chartType = data.chart_type || inferChartType(data.chart_data, xKey);
    return { chartType, chartData: data.chart_data, dataKeys, xKey };
  }

  // If data is an array directly
  if (Array.isArray(data)) {
    const xKey = detectXKey(data[0]);
    const dataKeys = detectDataKeys(data[0], xKey);
    const chartType = inferChartType(data, xKey);
    return { chartType, chartData: data, dataKeys, xKey };
  }

  // If data has named arrays (e.g., { labels: [...], values: [...] })
  if (data.labels && data.values) {
    const chartData = data.labels.map((label, i) => ({
      name: label,
      value: Array.isArray(data.values[i]) ? data.values[i][0] : data.values[i],
    }));
    return { chartType: 'bar', chartData, dataKeys: ['value'], xKey: 'name' };
  }

  // Try any array-valued property
  const arrayProp = Object.entries(data).find(
    ([k, v]) => Array.isArray(v) && v.length > 0 && k !== 'session_id'
  );
  if (arrayProp) {
    const [, arr] = arrayProp;
    if (typeof arr[0] === 'object') {
      const xKey = detectXKey(arr[0]);
      const dataKeys = detectDataKeys(arr[0], xKey);
      return { chartType: inferChartType(arr, xKey), chartData: arr, dataKeys, xKey };
    }
  }

  return { chartType: 'bar', chartData: [], dataKeys: [], xKey: 'name' };
}

function detectXKey(sample) {
  if (!sample || typeof sample !== 'object') return 'name';
  const candidates = ['name', 'label', 'category', 'date', 'month', 'year', 'type', 'period', 'district'];
  for (const c of candidates) {
    if (c in sample) return c;
  }
  // Use first string-valued key
  const stringKey = Object.entries(sample).find(([, v]) => typeof v === 'string');
  return stringKey ? stringKey[0] : Object.keys(sample)[0];
}

function detectDataKeys(sample, xKey) {
  if (!sample || typeof sample !== 'object') return ['value'];
  return Object.entries(sample)
    .filter(([k, v]) => k !== xKey && k !== 'session_id' && typeof v === 'number')
    .map(([k]) => k);
}

function inferChartType(data, xKey) {
  if (!data || data.length === 0) return 'bar';
  // If x values look like dates/time-series, use line
  const first = data[0]?.[xKey];
  if (typeof first === 'string' && /\d{4}[-/]/.test(first)) return 'line';
  // If few categories, pie might work
  if (data.length <= 6 && data.length >= 2) return 'bar'; // bar is still cleaner for most cases
  return 'bar';
}
