'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { HeartPulse, RefreshCcw, Clock, Activity } from 'lucide-react';

interface HeartRateZone {
  zone: number;
  label: string;
  hr_range: [number, number];
  time_seconds: number;
  time_formatted?: string;
  percent_time?: number;
  distance_km?: number;
  average_pace?: string | null;
}

interface HeartRateZoneAnalysis {
  analysis_window: {
    start: string;
    end: string;
    days: number;
  };
  activity_count: number;
  total_time_seconds?: number;
  total_time_formatted?: string;
  total_distance_km?: number;
  hr_max?: number;
  hr_max_computed?: number | null;
  hr_max_override?: number | null;
  zones: HeartRateZone[];
  notes?: string[];
}

interface HeartRateZonesCardProps {
  analysis: HeartRateZoneAnalysis | null;
  loading: boolean;
  error: string;
  onRefresh: () => void;
  onMaxHrChange: (value: number | null) => void;
  maxHrOverride: number | null;
}

const formatDateRange = (startIso: string, endIso: string) => {
  const start = new Date(startIso);
  const end = new Date(endIso);
  return `${start.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} → ${end.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;
};

const HeartRateZonesCard: React.FC<HeartRateZonesCardProps> = ({
  analysis,
  loading,
  error,
  onRefresh,
  onMaxHrChange,
  maxHrOverride,
}) => {
  const chartData = useMemo(
    () =>
      (analysis?.zones || []).map((zone) => ({
        name: zone.label,
        minutes: +(zone.time_seconds / 60).toFixed(1),
        percent: zone.percent_time ?? 0,
        pace: zone.average_pace || '—',
      })),
    [analysis?.zones]
  );

  const [maxHrInput, setMaxHrInput] = useState<string>(() => (maxHrOverride != null ? String(maxHrOverride) : ''));

  useEffect(() => {
    setMaxHrInput(maxHrOverride != null ? String(maxHrOverride) : '');
  }, [maxHrOverride]);

  const handleApplyOverride = () => {
    if (!maxHrInput.trim()) {
      onMaxHrChange(null);
      return;
    }
    const parsed = parseInt(maxHrInput, 10);
    if (Number.isNaN(parsed) || parsed < 80 || parsed > 240) {
      return;
    }
    onMaxHrChange(parsed);
  };

  const handleResetOverride = () => {
    setMaxHrInput('');
    onMaxHrChange(null);
  };

  return (
    <div className="glass rounded-2xl shadow-2xl p-8 border border-blue-500/20 bg-slate-900/70">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <span className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-500/20 border border-blue-500/40 text-blue-300">
            <HeartPulse className="w-6 h-6" />
          </span>
          <div>
            <h3 className="text-2xl font-bold text-slate-100">Heart Rate Zone Analysis</h3>
            <p className="text-sm text-slate-400">
              Last 30 days &bull; {analysis?.analysis_window ? formatDateRange(analysis.analysis_window.start, analysis.analysis_window.end) : '—'}
            </p>
          </div>
        </div>
        <div className="flex flex-col md:flex-row gap-3 md:items-center">
          <div className="flex items-end gap-2">
            <div className="flex flex-col gap-2">
              <label className="text-xs uppercase tracking-wide text-slate-400">Manual Max HR</label>
              <input
                type="number"
                min={80}
                max={240}
                value={maxHrInput}
                onChange={(e) => setMaxHrInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleApplyOverride();
                  }
                }}
                placeholder={analysis?.hr_max_computed ? String(analysis.hr_max_computed) : 'auto'}
                className="w-32 rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40"
              />
            </div>
            <button
              onClick={handleApplyOverride}
              disabled={loading}
              className="px-3 py-2 text-sm rounded-lg border border-blue-500/40 text-blue-200 hover:bg-blue-500/10 transition disabled:opacity-60"
            >
              Apply
            </button>
            <button
              onClick={handleResetOverride}
              disabled={loading}
              className="px-3 py-2 text-sm rounded-lg border border-slate-700 text-slate-300 hover:bg-slate-800/60 transition disabled:opacity-60"
            >
              Auto
            </button>
          </div>
          <button
            onClick={onRefresh}
            disabled={loading}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-700 text-slate-200 hover:bg-slate-800/80 transition disabled:opacity-60"
          >
            <RefreshCcw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {error ? (
        <div className="border border-rose-500/40 bg-rose-900/20 rounded-xl p-5 text-rose-200">
          {error}
        </div>
      ) : loading ? (
        <div className="py-12 text-center text-slate-400">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-400 mx-auto"></div>
          <p className="mt-4">Calculating zone distribution...</p>
        </div>
      ) : !analysis || analysis.zones.length === 0 ? (
        <div className="border border-slate-800 rounded-xl p-6 text-slate-400 text-center">
          No heart rate data available for the selected period.
        </div>
      ) : (
        <div className="space-y-6">
          <div className="grid md:grid-cols-4 gap-4 text-slate-100">
            <div className="rounded-xl border border-slate-800/60 bg-slate-900/60 px-4 py-3">
              <p className="text-xs uppercase tracking-wide text-slate-400 flex items-center gap-2"><HeartPulse className="w-4 h-4" /> Max HR</p>
              <p className="text-2xl font-semibold mt-1">{analysis.hr_max || '—'} bpm</p>
              <p className="text-[0.65rem] text-slate-500 mt-1">
                {analysis.hr_max_override ? 'Manual override applied' : 'Observed maximum in period'}
              </p>
            </div>
            <div className="rounded-xl border border-slate-800/60 bg-slate-900/60 px-4 py-3">
              <p className="text-xs uppercase tracking-wide text-slate-400 flex items-center gap-2"><Clock className="w-4 h-4" /> Time in Zones</p>
              <p className="text-2xl font-semibold mt-1">{analysis.total_time_formatted || '—'}</p>
            </div>
            <div className="rounded-xl border border-slate-800/60 bg-slate-900/60 px-4 py-3">
              <p className="text-xs uppercase tracking-wide text-slate-400 flex items-center gap-2"><Activity className="w-4 h-4" /> Activities</p>
              <p className="text-2xl font-semibold mt-1">{analysis.activity_count}</p>
            </div>
            <div className="rounded-xl border border-slate-800/60 bg-slate-900/60 px-4 py-3">
              <p className="text-xs uppercase tracking-wide text-slate-400">Distance Covered</p>
              <p className="text-2xl font-semibold mt-1">
                {analysis.total_distance_km !== undefined && analysis.total_distance_km !== null
                  ? `${analysis.total_distance_km.toFixed(2)} km`
                  : '—'}
              </p>
            </div>
          </div>

          <div className="grid lg:grid-cols-2 gap-6">
            <div className="rounded-2xl border border-slate-800/60 bg-slate-900/60 p-4">
              <h4 className="text-sm font-semibold text-slate-300 mb-3">Time Spent per Zone (minutes)</h4>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                  <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderRadius: 12, border: '1px solid #1e293b', color: '#e2e8f0' }}
                    cursor={{ fill: 'rgba(59,130,246,0.1)' }}
                    formatter={(value: number, _name, payload) => [`${value} min`, payload?.payload?.pace ? `Avg Pace: ${payload.payload.pace}` : undefined]}
                  />
                  <Bar dataKey="minutes" fill="#38bdf8" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="rounded-2xl border border-slate-800/60 bg-slate-900/60 p-4 overflow-x-auto">
              <h4 className="text-sm font-semibold text-slate-300 mb-3">Zone Details</h4>
              <table className="w-full text-sm">
                <thead className="text-slate-400 uppercase text-xs border-b border-slate-800">
                  <tr>
                    <th className="py-2 text-left">Zone</th>
                    <th className="py-2 text-left">HR Range</th>
                    <th className="py-2 text-left">Time</th>
                    <th className="py-2 text-left">% Time</th>
                    <th className="py-2 text-left">Avg Pace</th>
                    <th className="py-2 text-left">Distance</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-200">
                  {analysis.zones.map((zone) => (
                    <tr key={zone.zone} className="hover:bg-slate-800/40">
                      <td className="py-3 font-semibold">{zone.label}</td>
                      <td className="py-3 text-slate-400">{zone.hr_range?.[0] ?? '—'}-{zone.hr_range?.[1] ?? '—'} bpm</td>
                      <td className="py-3">{zone.time_formatted || '—'}</td>
                      <td className="py-3">{zone.percent_time !== undefined ? `${zone.percent_time}%` : '—'}</td>
                      <td className="py-3">{zone.average_pace || '—'}</td>
                      <td className="py-3">{zone.distance_km !== undefined ? `${zone.distance_km.toFixed(2)} km` : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {analysis.notes && analysis.notes.length > 0 && (
            <div className="border border-slate-800/60 rounded-xl p-4 text-xs text-slate-400 space-y-1">
              {analysis.notes.map((note, idx) => (
                <p key={idx}>• {note}</p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default HeartRateZonesCard;
