'use client';

import { Clock, MapPin, Zap, CheckCircle2, Circle } from 'lucide-react';

interface Workout {
  id: number;
  workout_type: string;
  target_distance_m: number | null;
  target_duration_s: number | null;
  target_pace_min_per_km: number | null;
  target_hr_zone: number | null;
  description: string;
  status: string;
  matched_strava_id: number | null;
}

interface TodayCardProps {
  workouts: Workout[];
  onWorkoutClick?: (workout: Workout) => void;
}

const TYPE_STYLES: Record<string, { label: string; color: string; bg: string }> = {
  easy: { label: 'Easy Run', color: 'text-[var(--accent-run)]', bg: 'bg-orange-500/10' },
  long: { label: 'Long Run', color: 'text-[var(--accent-run)]', bg: 'bg-orange-500/15' },
  tempo: { label: 'Tempo', color: 'text-yellow-400', bg: 'bg-yellow-400/10' },
  intervals: { label: 'Intervals', color: 'text-red-400', bg: 'bg-red-400/10' },
  recovery: { label: 'Recovery', color: 'text-[var(--accent-recovery)]', bg: 'bg-violet-500/10' },
  race: { label: 'Race', color: 'text-yellow-300', bg: 'bg-yellow-300/10' },
  cross: { label: 'Cross-train', color: 'text-[var(--accent-bike)]', bg: 'bg-blue-500/10' },
  rest: { label: 'Rest', color: 'text-slate-400', bg: 'bg-slate-700/30' },
};

function formatPace(minPerKm: number): string {
  const mins = Math.floor(minPerKm);
  const secs = Math.round((minPerKm - mins) * 60);
  return `${mins}:${secs.toString().padStart(2, '0')}/km`;
}

function formatDistance(metres: number): string {
  return `${(metres / 1000).toFixed(1)} km`;
}

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  if (m < 60) return `${m} min`;
  const h = Math.floor(m / 60);
  const rem = m % 60;
  return rem ? `${h}h ${rem}m` : `${h}h`;
}

export default function TodayCard({ workouts, onWorkoutClick }: TodayCardProps) {
  if (!workouts.length) {
    return (
      <div className="rounded-2xl bg-slate-800/60 border border-slate-700 p-6 text-center text-slate-400">
        <p className="text-sm">No workouts scheduled for today.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {workouts.map((w) => {
        const style = TYPE_STYLES[w.workout_type] ?? TYPE_STYLES.easy;
        const done = w.status === 'completed';

        return (
          <button
            key={w.id}
            onClick={() => onWorkoutClick?.(w)}
            className={`w-full text-left rounded-2xl border p-5 transition-all hover:scale-[1.01] active:scale-[0.99] ${
              done
                ? 'border-slate-600 bg-slate-800/40'
                : 'border-slate-600 bg-slate-800/80 hover:border-orange-500/40'
            }`}
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-xs font-semibold uppercase tracking-wide px-2 py-0.5 rounded-full ${style.color} ${style.bg}`}>
                    {style.label}
                  </span>
                  {done && (
                    <span className="text-xs text-emerald-400 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" />
                      Done
                    </span>
                  )}
                  {!done && w.matched_strava_id && (
                    <span className="text-xs text-slate-400">Auto-matched</span>
                  )}
                </div>
                <p className="text-sm text-slate-200 leading-snug line-clamp-2">{w.description}</p>
              </div>
              {done ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
              ) : (
                <Circle className="w-5 h-5 text-slate-500 shrink-0 mt-0.5" />
              )}
            </div>

            <div className="mt-3 flex flex-wrap gap-3 text-xs text-slate-400">
              {w.target_distance_m && (
                <span className="flex items-center gap-1">
                  <MapPin className="w-3 h-3" />
                  {formatDistance(w.target_distance_m)}
                </span>
              )}
              {w.target_duration_s && (
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {formatDuration(w.target_duration_s)}
                </span>
              )}
              {w.target_pace_min_per_km && (
                <span className="flex items-center gap-1">
                  <Zap className="w-3 h-3" />
                  {formatPace(w.target_pace_min_per_km)}
                </span>
              )}
              {w.target_hr_zone && (
                <span className="flex items-center gap-1">
                  Zone {w.target_hr_zone}
                </span>
              )}
            </div>
          </button>
        );
      })}
    </div>
  );
}
