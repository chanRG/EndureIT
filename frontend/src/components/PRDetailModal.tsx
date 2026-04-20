'use client';

import { X, Trophy, Activity, Heart, Calendar, TrendingDown } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';

interface PRHistoryItem {
  name: string;
  distance: number;
  elapsed_time: number;
  moving_time: number;
  start_date: string;
  start_date_local: string;
  activity_id: number;
  activity_name: string;
  pr_rank?: number;
  average_heartrate?: number;
  max_heartrate?: number;
  has_heartrate: boolean;
}

interface PRDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  distanceName: string;
  prHistory: PRHistoryItem[];
  loading: boolean;
}

export default function PRDetailModal({
  isOpen,
  onClose,
  distanceName,
  prHistory,
  loading,
}: PRDetailModalProps) {
  if (!isOpen) return null;

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: 'numeric'
    });
  };

  const formatShortDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric',
      month: 'short', 
      day: 'numeric'
    });
  };

  // Prepare data for time progression chart
  const timeData = prHistory
    .sort((a, b) => new Date(a.start_date).getTime() - new Date(b.start_date).getTime())
    .map((pr, index) => ({
      timestamp: new Date(pr.start_date_local).getTime(),
      date: formatShortDate(pr.start_date_local),
      fullDate: formatDate(pr.start_date_local),
      time: pr.elapsed_time,
      timeFormatted: formatDuration(pr.elapsed_time),
      isPR: pr.pr_rank === 1,
      attempt: index + 1,
    }));

  // Prepare data for heart rate chart (only items with HR data)
  const hrData = prHistory
    .filter(pr => pr.has_heartrate && pr.average_heartrate)
    .sort((a, b) => new Date(a.start_date).getTime() - new Date(b.start_date).getTime())
    .map((pr) => ({
      timestamp: new Date(pr.start_date_local).getTime(),
      date: formatShortDate(pr.start_date_local),
      avgHR: pr.average_heartrate,
      maxHR: pr.max_heartrate,
      time: pr.elapsed_time,
    }));

  const currentPR = prHistory.find(pr => pr.pr_rank === 1);
  const hasHeartRateData = hrData.length > 0;

  // Calculate improvements
  const improvements = prHistory
    .sort((a, b) => new Date(a.start_date).getTime() - new Date(b.start_date).getTime())
    .map((pr, index, arr) => {
      if (index === 0) return null;
      const previous = arr[index - 1];
      const improvement = previous.elapsed_time - pr.elapsed_time;
      return {
        date: formatShortDate(pr.start_date_local),
        improvement: improvement,
        improvementFormatted: improvement > 0 ? `-${formatDuration(improvement)}` : `+${formatDuration(Math.abs(improvement))}`,
        improved: improvement > 0,
      };
    })
    .filter(Boolean);

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-slate-950/95 rounded-3xl max-w-6xl w-full max-h-[90vh] overflow-y-auto border border-slate-800 shadow-2xl">
        {/* Header */}
        <div className="sticky top-0 bg-gradient-to-r from-yellow-900/40 via-orange-900/30 to-slate-950/80 border-b border-slate-800 px-6 py-5 flex items-center justify-between backdrop-blur-lg">
          <div className="flex items-center gap-3">
            <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-yellow-400/20 border border-yellow-400/40 text-yellow-300">
              <Trophy className="w-5 h-5" />
            </span>
            <div>
              <h2 className="text-2xl font-bold text-slate-100">{distanceName} PR History</h2>
              <p className="text-sm text-slate-400">
                {prHistory.length} attempt{prHistory.length !== 1 ? 's' : ''} captured
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-800/70 rounded-lg transition-colors text-slate-400 hover:text-slate-100"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {loading ? (
          <div className="p-12 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400 mx-auto"></div>
            <p className="mt-4 text-slate-400">Loading PR history...</p>
          </div>
        ) : prHistory.length === 0 ? (
          <div className="p-12 text-center text-slate-400">
            <Activity className="w-16 h-16 mx-auto text-slate-700 mb-4" />
            <p>No history found for this distance</p>
          </div>
        ) : (
          <div className="p-6 space-y-8 text-slate-200">
            {/* Current PR Highlight */}
            {currentPR && (
              <div className="rounded-2xl p-6 border border-yellow-500/40 bg-gradient-to-br from-yellow-900/20 via-orange-900/10 to-slate-900 shadow-xl">
                <div className="flex items-center gap-2 mb-4">
                  <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-yellow-400/10 border border-yellow-400/30 text-yellow-300">
                    <Trophy className="w-5 h-5" />
                  </span>
                  <h3 className="text-xl font-bold text-slate-100">Current Personal Record</h3>
                </div>
                <div className="grid md:grid-cols-3 gap-4">
                  <div>
                    <p className="text-sm text-slate-400 uppercase tracking-wide">Time</p>
                    <p className="text-4xl font-bold text-blue-300">
                      {formatDuration(currentPR.elapsed_time)}
                    </p>
                  </div>
                  {currentPR.has_heartrate && currentPR.average_heartrate && (
                    <div>
                      <p className="text-sm text-slate-400 uppercase tracking-wide">Avg Heart Rate</p>
                      <p className="text-3xl font-bold text-rose-300">
                        {currentPR.average_heartrate.toFixed(0)} <span className="text-lg">bpm</span>
                      </p>
                    </div>
                  )}
                  <div>
                    <p className="text-sm text-slate-400 uppercase tracking-wide">Date</p>
                    <p className="text-lg font-semibold text-slate-100">
                      {formatDate(currentPR.start_date_local)}
                    </p>
                    <p className="text-sm text-slate-400 truncate">
                      {currentPR.activity_name}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Time Progression Chart */}
            <div className="glass rounded-2xl p-6 border border-blue-500/20 bg-blue-900/10 shadow-lg">
              <h3 className="text-lg font-bold text-slate-100 mb-4 flex items-center gap-2">
                <TrendingDown className="w-5 h-5 text-blue-400" />
                Time Progression
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={timeData}>
                  <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="timestamp"
                    type="number"
                    domain={['dataMin', 'dataMax']}
                    scale="time"
                    tickFormatter={(timestamp) => {
                      const date = new Date(timestamp);
                      return date.toLocaleDateString('en-US', { 
                        month: 'short',
                        year: '2-digit'
                      });
                    }}
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis
                    stroke="#475569"
                    tickFormatter={(value) => formatDuration(value)}
                    tick={{ fontSize: 12 }}
                  />
                  <Tooltip 
                    labelFormatter={(timestamp) => {
                      const item = timeData.find(d => d.timestamp === timestamp);
                      return item ? item.fullDate : new Date(timestamp).toLocaleDateString();
                    }}
                    formatter={(value: any) => [formatDuration(value), 'Time']}
                  />
                  <Legend wrapperStyle={{ color: '#cbd5e1' }} />
                  <Line 
                    type="monotone" 
                    dataKey="time" 
                    stroke="#60a5fa" 
                    strokeWidth={2}
                    name="Time"
                    dot={(props: any) => {
                      const { cx, cy, payload } = props;
                      return (
                        <circle
                          cx={cx}
                          cy={cy}
                          r={payload.isPR ? 6 : 4}
                          fill={payload.isPR ? '#facc15' : '#60a5fa'}
                          stroke={payload.isPR ? '#f59e0b' : '#3b82fa'}
                          strokeWidth={2}
                        />
                      );
                    }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Heart Rate Chart */}
            {hasHeartRateData && (
              <div className="glass rounded-2xl p-6 border border-rose-500/20 bg-rose-900/10 shadow-lg">
                <h3 className="text-lg font-bold text-slate-100 mb-4 flex items-center gap-2">
                  <Heart className="w-5 h-5 text-rose-400" />
                  Heart Rate Analysis
                </h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={hrData}>
                    <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="timestamp"
                      type="number"
                      domain={['dataMin', 'dataMax']}
                      scale="time"
                      tickFormatter={(timestamp) => {
                        const date = new Date(timestamp);
                        return date.toLocaleDateString('en-US', { 
                          month: 'short',
                          year: '2-digit'
                        });
                      }}
                      tick={{ fontSize: 12 }}
                    />
                    <YAxis tick={{ fontSize: 12 }} stroke="#475569" />
                    <Tooltip 
                      labelFormatter={(timestamp) => {
                        const item = hrData.find(d => d.timestamp === timestamp);
                        return item ? item.date : new Date(timestamp).toLocaleDateString();
                      }}
                      contentStyle={{ backgroundColor: '#0f172a', borderRadius: '0.75rem', border: '1px solid #334155', color: '#e2e8f0' }}
                    />
                    <Legend wrapperStyle={{ color: '#cbd5e1' }} />
                    <Bar dataKey="avgHR" fill="#fb7185" name="Avg HR (bpm)" />
                    {hrData.some(d => d.maxHR) && (
                      <Bar dataKey="maxHR" fill="#fda4af" name="Max HR (bpm)" />
                    )}
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* All Attempts Table */}
            <div className="glass rounded-2xl p-6 border border-slate-700/60 bg-slate-900/70 shadow-lg">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-purple-400" />
                  <h3 className="text-lg font-bold text-slate-100">All Attempts</h3>
                </div>
                <span className="text-sm text-slate-400">{prHistory.length} entries</span>
              </div>
              <div className="overflow-hidden rounded-xl border border-slate-800/60">
                <table className="w-full">
                  <thead className="bg-slate-900/80">
                    <tr className="text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                      <th className="px-4 py-3">Rank</th>
                      <th className="px-4 py-3">Date</th>
                      <th className="px-4 py-3">Time</th>
                      <th className="px-4 py-3">Avg HR</th>
                      <th className="px-4 py-3">Activity</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/80">
                    {prHistory.map((pr, index) => {
                      const isCurrent = pr.pr_rank === 1;
                      return (
                        <tr
                          key={pr.activity_id}
                          className={`transition-colors ${
                            isCurrent
                              ? 'bg-yellow-500/10 border-l-2 border-l-yellow-400'
                              : 'hover:bg-slate-900/70'
                          }`}
                        >
                          <td className="px-4 py-3 whitespace-nowrap text-sm">
                            {isCurrent ? (
                              <span className="inline-flex items-center gap-1 text-yellow-300 font-semibold">
                                <Trophy className="w-4 h-4" />
                                PR
                              </span>
                            ) : (
                              <span className="text-slate-400">#{index + 1}</span>
                            )}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-slate-200">
                            {formatDate(pr.start_date_local)}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm font-semibold text-blue-200">
                            {formatDuration(pr.elapsed_time)}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-slate-400">
                            {pr.has_heartrate && pr.average_heartrate
                              ? `${pr.average_heartrate.toFixed(0)} bpm`
                              : '—'}
                          </td>
                          <td className="px-4 py-3 text-sm text-slate-400 truncate max-w-xs">
                            {pr.activity_name}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

