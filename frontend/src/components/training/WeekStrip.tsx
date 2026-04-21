'use client';

import { CheckCircle2, Circle, X } from 'lucide-react';

interface DayWorkout {
  id: number;
  scheduled_date: string;
  workout_type: string;
  status: string;
  target_distance_m: number | null;
  phase: string;
}

interface WeekStripProps {
  workouts: DayWorkout[];
  weekStart: string;
  onDayClick?: (day: string, workouts: DayWorkout[]) => void;
}

const DAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

const TYPE_DOT: Record<string, string> = {
  easy: 'bg-orange-400',
  long: 'bg-orange-500',
  tempo: 'bg-yellow-400',
  intervals: 'bg-red-400',
  recovery: 'bg-violet-400',
  race: 'bg-yellow-300',
  cross: 'bg-blue-400',
  rest: 'bg-slate-600',
};

const PHASE_BAR: Record<string, string> = {
  base: 'bg-blue-500',
  build: 'bg-orange-500',
  peak: 'bg-red-500',
  taper: 'bg-violet-500',
};

export default function WeekStrip({ workouts, weekStart, onDayClick }: WeekStripProps) {
  const today = new Date().toISOString().split('T')[0];

  const days = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(weekStart);
    d.setDate(d.getDate() + i);
    return d.toISOString().split('T')[0];
  });

  const byDay: Record<string, DayWorkout[]> = {};
  for (const w of workouts) {
    if (!byDay[w.scheduled_date]) byDay[w.scheduled_date] = [];
    byDay[w.scheduled_date].push(w);
  }

  return (
    <div className="grid grid-cols-7 gap-1">
      {days.map((day, i) => {
        const dayWorkouts = byDay[day] ?? [];
        const isToday = day === today;
        const isPast = day < today;
        const firstWorkout = dayWorkouts[0];
        const allDone = dayWorkouts.length > 0 && dayWorkouts.every((w) => w.status === 'completed');
        const anyMissed = isPast && dayWorkouts.length > 0 && !allDone;
        const phase = firstWorkout?.phase;

        return (
          <button
            key={day}
            onClick={() => onDayClick?.(day, dayWorkouts)}
            className={`flex flex-col items-center rounded-xl p-2 transition-all hover:bg-slate-700/60 ${
              isToday ? 'ring-2 ring-orange-500/60 bg-slate-700/40' : ''
            }`}
          >
            <span className={`text-[10px] font-medium mb-1 ${isToday ? 'text-orange-400' : 'text-slate-500'}`}>
              {DAY_LABELS[i]}
            </span>

            <div className="relative w-8 h-8 flex items-center justify-center">
              {allDone ? (
                <CheckCircle2 className="w-6 h-6 text-emerald-400" />
              ) : anyMissed ? (
                <X className="w-5 h-5 text-red-400/70" />
              ) : dayWorkouts.length === 0 ? (
                <span className="w-2 h-2 rounded-full bg-slate-700" />
              ) : (
                <div className="flex flex-col gap-0.5 items-center">
                  {dayWorkouts.slice(0, 2).map((w) => (
                    <span
                      key={w.id}
                      className={`w-2 h-2 rounded-full ${TYPE_DOT[w.workout_type] ?? 'bg-slate-500'}`}
                    />
                  ))}
                </div>
              )}
            </div>

            {phase && (
              <span className={`mt-1 w-4 h-0.5 rounded-full ${PHASE_BAR[phase] ?? 'bg-slate-600'}`} />
            )}
          </button>
        );
      })}
    </div>
  );
}
