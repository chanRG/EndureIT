'use client';

import React, { Suspense, lazy } from 'react';

// Lazy load the map component to avoid SSR issues with Leaflet
const ActivityMap = lazy(() => import('./ActivityMap'));

interface ActivityDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  activity: any;
  loading: boolean;
}

export default function ActivityDetailModal({
  isOpen,
  onClose,
  activity,
  loading
}: ActivityDetailModalProps) {
  if (!isOpen) return null;

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDistance = (meters: number) => {
    return (meters / 1000).toFixed(2);
  };

  const formatPace = (metersPerSecond: number) => {
    if (!metersPerSecond) return 'N/A';
    const minutesPerKm = 1000 / (metersPerSecond * 60);
    const minutes = Math.floor(minutesPerKm);
    const seconds = Math.round((minutesPerKm - minutes) * 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  return (
    <div 
      className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div 
        className="bg-slate-950/95 rounded-3xl border border-slate-800 shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {loading ? (
          <div className="p-10 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400 mx-auto"></div>
            <p className="mt-4 text-slate-400">Loading activity details...</p>
          </div>
        ) : activity ? (
          <>
            {/* Header */}
            <div className="border-b border-slate-800/70 p-6 bg-gradient-to-r from-blue-900/30 via-indigo-900/20 to-slate-950/70">
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-3xl font-bold text-slate-100">{activity.name}</h2>
                  <p className="text-sm text-slate-400 mt-1">
                    {new Date(activity.start_date_local).toLocaleString()}
                  </p>
                </div>
                <button
                  onClick={onClose}
                  className="text-slate-400 hover:text-slate-100 text-3xl font-bold leading-none transition-colors"
                >
                  ×
                </button>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/15 text-blue-300 border border-blue-500/30 uppercase tracking-wide">
                  {activity.type}
                </span>
                {activity.workout_type && (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 uppercase tracking-wide">
                    Workout
                  </span>
                )}
              </div>
            </div>

            {/* Map */}
            {(activity.map?.summary_polyline || activity.start_latlng) && (
              <div className="px-6 pt-6">
                <h3 className="text-lg font-semibold text-slate-100 mb-3 flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-blue-400 animate-pulse" />
                  Route Map
                </h3>
                <Suspense fallback={
                  <div className="w-full h-64 bg-slate-900/60 border border-slate-800 rounded-xl flex items-center justify-center">
                    <p className="text-slate-500">Loading map...</p>
                  </div>
                }>
                  <ActivityMap
                    polyline={activity.map?.summary_polyline}
                    startLatlng={activity.start_latlng}
                    endLatlng={activity.end_latlng}
                  />
                </Suspense>
              </div>
            )}

            {/* Main Stats */}
            <div className="p-6 grid grid-cols-2 md:grid-cols-4 gap-4 text-slate-100">
              {[
                { label: 'Distance', value: `${formatDistance(activity.distance)} km`, accent: 'from-blue-500/20 via-blue-500/5 to-transparent', border: 'border-blue-500/30' },
                { label: 'Duration', value: formatTime(activity.moving_time), accent: 'from-purple-500/20 via-purple-500/5 to-transparent', border: 'border-purple-500/30' },
                { label: 'Pace', value: `${formatPace(activity.average_speed)}/km`, accent: 'from-emerald-500/20 via-emerald-500/5 to-transparent', border: 'border-emerald-500/30' },
                { label: 'Elevation', value: `${Math.round(activity.total_elevation_gain)} m`, accent: 'from-orange-500/20 via-orange-500/5 to-transparent', border: 'border-orange-500/30' },
              ].map((stat) => (
                <div
                  key={stat.label}
                  className={`rounded-2xl p-4 border ${stat.border} bg-gradient-to-br ${stat.accent} backdrop-blur-md shadow-lg`}
                >
                  <p className="text-xs text-slate-400 uppercase tracking-wide">{stat.label}</p>
                  <p className="text-3xl font-semibold text-slate-100 mt-2">{stat.value}</p>
                </div>
              ))}
            </div>

            {/* Heart Rate Stats */}
            {activity.has_heartrate && (
              <div className="px-6 pb-6">
                <h3 className="text-lg font-semibold text-slate-100 mb-3 flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-rose-400 animate-pulse" />
                  Heart Rate
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  {[
                    { label: 'Average HR', value: `${Math.round(activity.average_heartrate)} bpm` },
                    { label: 'Max HR', value: `${Math.round(activity.max_heartrate)} bpm` },
                  ].map((hr) => (
                    <div key={hr.label} className="rounded-2xl p-4 border border-rose-500/30 bg-rose-500/10 backdrop-blur-md text-slate-100 shadow-lg">
                      <p className="text-xs text-slate-200/70 uppercase tracking-wide">{hr.label}</p>
                      <p className="text-2xl font-semibold text-rose-200 mt-2">{hr.value}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Additional Stats */}
            <div className="px-6 pb-6">
              <h3 className="text-lg font-semibold text-slate-100 mb-3 flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-purple-400" />
                Additional Insights
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm text-slate-200">
                <div className="bg-slate-900/60 border border-slate-800/70 rounded-xl px-4 py-3">
                  <span className="text-xs text-slate-400 uppercase tracking-wide">Max Speed</span>
                  <span className="ml-2 block text-lg font-semibold text-slate-100 mt-1">{formatPace(activity.max_speed)}/km</span>
                </div>
                <div className="bg-slate-900/60 border border-slate-800/70 rounded-xl px-4 py-3">
                  <span className="text-xs text-slate-400 uppercase tracking-wide">Elapsed Time</span>
                  <span className="ml-2 block text-lg font-semibold text-slate-100 mt-1">{formatTime(activity.elapsed_time)}</span>
                </div>
                {activity.calories && (
                  <div className="bg-slate-900/60 border border-slate-800/70 rounded-xl px-4 py-3">
                    <span className="text-xs text-slate-400 uppercase tracking-wide">Calories</span>
                    <span className="ml-2 block text-lg font-semibold text-amber-200 mt-1">{Math.round(activity.calories)}</span>
                  </div>
                )}
                <div className="bg-slate-900/60 border border-slate-800/70 rounded-xl px-4 py-3">
                  <span className="text-xs text-slate-400 uppercase tracking-wide">Achievements</span>
                  <span className="ml-2 block text-lg font-semibold text-slate-100 mt-1">{activity.achievement_count || 0}</span>
                </div>
                <div className="bg-slate-900/60 border border-slate-800/70 rounded-xl px-4 py-3">
                  <span className="text-xs text-slate-400 uppercase tracking-wide">Kudos</span>
                  <span className="ml-2 block text-lg font-semibold text-slate-100 mt-1">{activity.kudos_count || 0}</span>
                </div>
                {activity.suffer_score && (
                  <div className="bg-slate-900/60 border border-slate-800/70 rounded-xl px-4 py-3">
                    <span className="text-xs text-slate-400 uppercase tracking-wide">Suffer Score</span>
                    <span className="ml-2 block text-lg font-semibold text-rose-200 mt-1">{activity.suffer_score}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Best Efforts */}
            {activity.best_efforts && activity.best_efforts.length > 0 && (
              <div className="px-6 pb-6">
                <h3 className="text-lg font-semibold text-slate-100 mb-3 flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-yellow-400" />
                  Best Efforts
                </h3>
                <div className="grid md:grid-cols-2 gap-3">
                  {activity.best_efforts.map((effort: any, idx: number) => {
                    const isPR = effort.pr_rank === 1;
                    return (
                      <div
                        key={idx}
                        className={`rounded-2xl border backdrop-blur-md p-4 shadow-lg transition-transform hover:-translate-y-1 ${
                          isPR
                            ? 'border-yellow-400/40 bg-gradient-to-br from-yellow-500/20 via-yellow-500/5 to-slate-900'
                            : 'border-slate-700/70 bg-slate-900/60'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <p className="font-semibold text-slate-100">{effort.name}</p>
                            <p className="text-xs text-slate-400 mt-1">{formatDistance(effort.distance)} km</p>
                          </div>
                          {isPR && (
                            <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold text-yellow-300 bg-yellow-500/20 border border-yellow-500/40">
                              PR
                            </span>
                          )}
                        </div>
                        <div className="mt-4 flex items-center justify-between text-sm">
                          <div>
                            <p className="text-xs text-slate-400 uppercase tracking-wide">Time</p>
                            <p className="text-lg font-semibold text-blue-300">{formatTime(effort.elapsed_time)}</p>
                          </div>
                          {effort.pr_rank && (
                            <div className="text-right">
                              <p className="text-xs text-slate-400 uppercase tracking-wide">Rank</p>
                              <p className="text-base font-semibold text-emerald-300">#{effort.pr_rank}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Description */}
            {activity.description && (
              <div className="px-6 pb-6">
                <h3 className="text-lg font-semibold text-slate-100 mb-3">Description</h3>
                <p className="text-slate-300 whitespace-pre-wrap bg-slate-900/60 border border-slate-800/70 rounded-2xl p-4">
                  {activity.description}
                </p>
              </div>
            )}

            {/* View on Strava */}
            <div className="px-6 pb-6">
              <a
                href={`https://www.strava.com/activities/${activity.id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-5 py-3 text-sm font-semibold rounded-full text-slate-900 bg-gradient-to-r from-amber-300 to-orange-400 hover:from-amber-200 hover:to-orange-300 transition shadow-lg"
              >
                View on Strava →
              </a>
            </div>
          </>
        ) : (
          <div className="p-8 text-center text-slate-500">
            No activity data available
          </div>
        )}
      </div>
    </div>
  );
}

