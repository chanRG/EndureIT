'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  ArrowLeft,
  BellRing,
  CalendarClock,
  CheckCircle2,
  Mail,
  ShieldCheck,
  Smartphone,
} from 'lucide-react';

import EnablePushButton from '@/components/notifications/EnablePushButton';
import { useAuth } from '@/contexts/AuthContext';
import { nutritionAPI, pushAPI } from '@/lib/api';

interface PushStatusResponse {
  configured: boolean;
  has_active_subscription: boolean;
  subscriptions: Array<{
    id: number;
    platform: string | null;
    user_agent: string | null;
    is_active: boolean;
    last_success_at: string | null;
    error_count: number;
    created_at: string;
  }>;
}

interface ReminderItem {
  id: number;
  kind: string;
  scheduled_at: string;
  status: string;
  payload: {
    title?: string;
    body?: string;
  } | null;
}

function getReminderLabel(kind: string): string {
  const labels: Record<string, string> = {
    meal: 'Meal',
    pre_workout_fuel: 'Pre-workout',
    in_workout_gel: 'Mid-session fuel',
    post_workout_recovery: 'Recovery',
  };
  return labels[kind] ?? kind;
}

export default function NotificationsSettingsPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [status, setStatus] = useState<PushStatusResponse | null>(null);
  const [reminders, setReminders] = useState<ReminderItem[]>([]);
  const [loadingPage, setLoadingPage] = useState(true);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
    }
  }, [authLoading, router, user]);

  useEffect(() => {
    if (!user) {
      return;
    }

    refresh();
  }, [user]);

  async function refresh() {
    setLoadingPage(true);
    try {
      const [pushStatus, upcomingReminders] = await Promise.all([
        pushAPI.getSubscriptions(),
        nutritionAPI.getUpcomingReminders(),
      ]);
      setStatus(pushStatus);
      setReminders(upcomingReminders);
    } finally {
      setLoadingPage(false);
    }
  }

  if (authLoading || !user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,rgba(34,197,94,0.16),transparent_24%),radial-gradient(circle_at_top_right,rgba(59,130,246,0.14),transparent_26%),#0f172a] px-4 py-6 text-white">
      <div className="mx-auto max-w-5xl space-y-6">
        <div className="flex items-center justify-between">
          <Link
            href="/nutrition"
            className="inline-flex items-center gap-2 rounded-2xl border border-slate-700/80 bg-slate-950/55 px-4 py-2 text-sm text-slate-200 transition hover:border-slate-500"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to nutrition
          </Link>
        </div>

        <section className="overflow-hidden rounded-[32px] border border-slate-700/80 bg-[linear-gradient(180deg,rgba(15,23,42,0.95),rgba(15,23,42,0.82))] shadow-[0_30px_90px_rgba(15,23,42,0.46)]">
          <div className="border-b border-slate-800/80 px-6 py-6">
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-green-300/85">
              Notification Center
            </p>
            <div className="mt-3 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <h1 className="flex items-center gap-3 text-3xl font-semibold text-white">
                  <BellRing className="h-8 w-8 text-green-300" />
                  Reminders that move with your plan
                </h1>
                <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-300">
                  EndureIT can deliver meal nudges, pre-run fueling cues, mid-session carb reminders, and post-workout recovery prompts. Push is instant; critical reminders can fall back to email.
                </p>
              </div>
            </div>
          </div>

          <div className="grid gap-4 px-6 py-6 md:grid-cols-3">
            <div className="rounded-3xl border border-slate-700/70 bg-slate-950/55 p-5">
              <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">
                <Smartphone className="h-4 w-4 text-sky-300" />
                Devices
              </p>
              <p className="mt-3 text-3xl font-semibold text-white">
                {status?.subscriptions.filter((item) => item.is_active).length ?? '—'}
              </p>
              <p className="mt-2 text-sm text-slate-400">
                Active browser subscriptions tied to this account.
              </p>
            </div>

            <div className="rounded-3xl border border-slate-700/70 bg-slate-950/55 p-5">
              <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">
                <CalendarClock className="h-4 w-4 text-orange-300" />
                Upcoming
              </p>
              <p className="mt-3 text-3xl font-semibold text-white">{reminders.length}</p>
              <p className="mt-2 text-sm text-slate-400">
                Scheduled reminders waiting in the queue.
              </p>
            </div>

            <div className="rounded-3xl border border-slate-700/70 bg-slate-950/55 p-5">
              <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">
                <Mail className="h-4 w-4 text-violet-300" />
                Email Fallback
              </p>
              <p className="mt-3 text-lg font-semibold text-white">{user.email}</p>
              <p className="mt-2 text-sm text-slate-400">
                Used for critical fueling reminders when push is unavailable.
              </p>
            </div>
          </div>
        </section>

        {loadingPage ? (
          <div className="grid gap-4 lg:grid-cols-[1fr,1.15fr]">
            <div className="h-64 animate-pulse rounded-[32px] bg-slate-800/45" />
            <div className="h-64 animate-pulse rounded-[32px] bg-slate-800/45" />
          </div>
        ) : (
          <div className="grid gap-6 lg:grid-cols-[0.92fr,1.08fr]">
            <div className="space-y-6">
              <EnablePushButton status={status} onStatusChange={refresh} />

              <div className="rounded-[32px] border border-slate-700/80 bg-slate-900/70 p-6">
                <p className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.22em] text-slate-400">
                  <ShieldCheck className="h-4 w-4 text-emerald-300" />
                  Delivery Notes
                </p>
                <div className="mt-4 space-y-3 text-sm leading-6 text-slate-300">
                  <p>Push reminders require a supported browser and permission.</p>
                  <p>On iPhone, web push only works after the app is installed to the home screen.</p>
                  <p>Critical workout-fueling reminders can fall back to email if push fails.</p>
                </div>
              </div>
            </div>

            <div className="rounded-[32px] border border-slate-700/80 bg-slate-900/70 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold uppercase tracking-[0.22em] text-slate-400">
                    Upcoming Reminders
                  </p>
                  <h2 className="mt-2 text-2xl font-semibold text-white">What will fire next</h2>
                </div>
                <button
                  type="button"
                  onClick={refresh}
                  className="rounded-2xl border border-slate-700/80 bg-slate-950/55 px-4 py-2 text-sm text-slate-200 transition hover:border-slate-500"
                >
                  Refresh
                </button>
              </div>

              <div className="mt-5 space-y-3">
                {reminders.length === 0 ? (
                  <div className="rounded-3xl border border-slate-800 bg-slate-950/55 p-6 text-sm text-slate-400">
                    No pending reminders yet. Once your next training day is scheduled, they&apos;ll appear here.
                  </div>
                ) : (
                  reminders.map((reminder) => (
                    <div
                      key={reminder.id}
                      className="rounded-3xl border border-slate-800 bg-slate-950/55 p-5"
                    >
                      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                        <div>
                          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-green-300/80">
                            {getReminderLabel(reminder.kind)}
                          </p>
                          <p className="mt-2 text-lg font-semibold text-white">
                            {reminder.payload?.title || 'Planned reminder'}
                          </p>
                          <p className="mt-1 text-sm text-slate-400">
                            {reminder.payload?.body || 'Scheduled from your active nutrition plan.'}
                          </p>
                        </div>
                        <div className="rounded-2xl border border-slate-700/80 bg-slate-900/60 px-3 py-2 text-right">
                          <p className="text-sm font-semibold text-white">
                            {new Date(reminder.scheduled_at).toLocaleString('en-GB', {
                              day: 'numeric',
                              month: 'short',
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </p>
                          <p className="mt-1 inline-flex items-center gap-1 text-xs text-slate-400">
                            <CheckCircle2 className="h-3.5 w-3.5" />
                            {reminder.status}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
