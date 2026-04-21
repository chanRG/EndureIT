'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { trainingAPI } from '@/lib/api';
import TodayCard from '@/components/training/TodayCard';
import WeekStrip from '@/components/training/WeekStrip';
import PlanWizard from '@/components/training/PlanWizard';
import { Plus, ChevronLeft, ChevronRight, Trophy, Calendar } from 'lucide-react';

function getMondayOfWeek(date: Date): string {
  const d = new Date(date);
  const day = d.getDay();
  const diff = (day === 0 ? -6 : 1 - day);
  d.setDate(d.getDate() + diff);
  return d.toISOString().split('T')[0];
}

function addWeeks(dateStr: string, n: number): string {
  const d = new Date(dateStr);
  d.setDate(d.getDate() + n * 7);
  return d.toISOString().split('T')[0];
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-GB', { month: 'short', day: 'numeric' });
}

interface ActivePlan {
  id: number;
  goal_distance_km: number;
  race_name: string | null;
  race_date: string;
  status: string;
  total_weeks: number;
  current_week: number;
  current_phase: string | null;
  today_workouts: any[];
}

export default function TrainingPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [plan, setPlan] = useState<ActivePlan | null>(null);
  const [loadingPlan, setLoadingPlan] = useState(true);
  const [showWizard, setShowWizard] = useState(false);

  const [weekStart, setWeekStart] = useState(getMondayOfWeek(new Date()));
  const [weekWorkouts, setWeekWorkouts] = useState<any[]>([]);
  const [loadingWeek, setLoadingWeek] = useState(false);

  useEffect(() => {
    if (!authLoading && !user) router.push('/login');
  }, [user, authLoading, router]);

  useEffect(() => {
    if (!user) return;
    fetchActivePlan();
  }, [user]);

  useEffect(() => {
    if (!user) return;
    fetchWeekWorkouts();
  }, [user, weekStart]);

  async function fetchActivePlan() {
    setLoadingPlan(true);
    try {
      const data = await trainingAPI.getActivePlan();
      setPlan(data);
    } catch {
      setPlan(null);
    } finally {
      setLoadingPlan(false);
    }
  }

  async function fetchWeekWorkouts() {
    setLoadingWeek(true);
    try {
      const data = await trainingAPI.getWeekWorkouts(weekStart);
      setWeekWorkouts(data);
    } catch {
      setWeekWorkouts([]);
    } finally {
      setLoadingWeek(false);
    }
  }

  if (authLoading || !user) return null;

  const PHASE_COLORS: Record<string, string> = {
    base: 'text-blue-400',
    build: 'text-orange-400',
    peak: 'text-red-400',
    taper: 'text-violet-400',
  };

  return (
    <div className="min-h-screen bg-[#0f172a] text-white">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-[#0f172a]/90 backdrop-blur border-b border-slate-800 px-4 py-3 flex items-center justify-between">
        <h1 className="text-lg font-semibold">Training</h1>
        {!showWizard && (
          <button
            onClick={() => setShowWizard(true)}
            className="flex items-center gap-1.5 bg-orange-500 hover:bg-orange-600 text-white text-sm font-medium px-3 py-1.5 rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Plan
          </button>
        )}
      </div>

      <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
        {/* Plan Wizard */}
        {showWizard && (
          <PlanWizard
            onCreated={() => { setShowWizard(false); fetchActivePlan(); fetchWeekWorkouts(); }}
            onCancel={() => setShowWizard(false)}
          />
        )}

        {/* Active Plan Summary */}
        {!showWizard && !loadingPlan && plan && (
          <div className="rounded-2xl bg-gradient-to-br from-orange-500/10 to-slate-800/60 border border-orange-500/20 p-5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <Trophy className="w-4 h-4 text-orange-400" />
                  <span className="text-sm font-medium text-orange-400">
                    {plan.race_name ?? `${plan.goal_distance_km} km Race`}
                  </span>
                </div>
                <p className="text-xs text-slate-400 flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  Race day: {formatDate(plan.race_date)}
                </p>
              </div>
              <div className="text-right shrink-0">
                <div className="text-2xl font-bold text-white">
                  Week {plan.current_week}
                  <span className="text-slate-500 text-base font-normal">/{plan.total_weeks}</span>
                </div>
                {plan.current_phase && (
                  <div className={`text-xs capitalize font-medium ${PHASE_COLORS[plan.current_phase] ?? 'text-slate-400'}`}>
                    {plan.current_phase} phase
                  </div>
                )}
              </div>
            </div>

            {/* Progress bar */}
            <div className="mt-4">
              <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-orange-500 to-orange-400 rounded-full transition-all"
                  style={{ width: `${(plan.current_week / plan.total_weeks) * 100}%` }}
                />
              </div>
            </div>
          </div>
        )}

        {/* No plan state */}
        {!showWizard && !loadingPlan && !plan && (
          <div className="rounded-2xl bg-slate-800/60 border border-slate-700 p-8 text-center space-y-4">
            <Trophy className="w-10 h-10 text-slate-600 mx-auto" />
            <div>
              <p className="text-white font-medium mb-1">No active training plan</p>
              <p className="text-sm text-slate-400">Create a plan to start training towards your next race.</p>
            </div>
            <button
              onClick={() => setShowWizard(true)}
              className="inline-flex items-center gap-2 bg-orange-500 hover:bg-orange-600 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
            >
              <Plus className="w-4 h-4" />
              Create Plan
            </button>
          </div>
        )}

        {/* Today's Workouts */}
        {!showWizard && plan && plan.today_workouts.length > 0 && (
          <section>
            <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wide mb-3">Today</h2>
            <TodayCard workouts={plan.today_workouts} />
          </section>
        )}

        {/* Week Strip */}
        {!showWizard && (
          <section>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wide">This Week</h2>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setWeekStart(addWeeks(weekStart, -1))}
                  className="p-1 rounded-lg hover:bg-slate-700 text-slate-400 hover:text-white"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="text-xs text-slate-400">
                  {formatDate(weekStart)} – {formatDate(addWeeks(weekStart, 1).replace(/(\d{4}-\d{2}-\d{2})/, (m) => {
                    const d = new Date(m);
                    d.setDate(d.getDate() + 6);
                    return d.toISOString().split('T')[0];
                  }))}
                </span>
                <button
                  onClick={() => setWeekStart(addWeeks(weekStart, 1))}
                  className="p-1 rounded-lg hover:bg-slate-700 text-slate-400 hover:text-white"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
            {loadingWeek ? (
              <div className="h-16 rounded-xl bg-slate-800/40 animate-pulse" />
            ) : (
              <div className="rounded-2xl bg-slate-800/60 border border-slate-700 p-3">
                <WeekStrip workouts={weekWorkouts} weekStart={weekStart} />
              </div>
            )}
          </section>
        )}
      </div>
    </div>
  );
}
