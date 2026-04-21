'use client';

import { Bell, BellOff, Download, Loader2, ShieldAlert } from 'lucide-react';
import { useEffect, useState } from 'react';

import { pushAPI } from '@/lib/api';
import {
  createPushSubscription,
  getExistingSubscription,
  getPushEnvironment,
  removePushSubscription,
} from '@/lib/push';

interface PushStatus {
  configured: boolean;
  has_active_subscription: boolean;
}

interface EnablePushButtonProps {
  status: PushStatus | null;
  onStatusChange: () => Promise<void> | void;
}

function getErrorMessage(error: unknown, fallback: string): string {
  if (
    typeof error === 'object'
    && error !== null
    && 'response' in error
    && typeof (error as { response?: { data?: { detail?: unknown } } }).response?.data?.detail === 'string'
  ) {
    return (error as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? fallback;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return fallback;
}

export default function EnablePushButton({ status, onStatusChange }: EnablePushButtonProps) {
  const [working, setWorking] = useState(false);
  const [message, setMessage] = useState('');
  const [environment, setEnvironment] = useState(getPushEnvironment());

  useEffect(() => {
    setEnvironment(getPushEnvironment());
  }, []);

  async function handleEnable() {
    setWorking(true);
    setMessage('');
    try {
      const keyResponse = await pushAPI.getVapidPublicKey();
      const subscription = await createPushSubscription(keyResponse.public_key);
      await pushAPI.saveSubscription(subscription);
      await onStatusChange();
      setEnvironment(getPushEnvironment());
      setMessage('Push notifications are enabled.');
    } catch (error: unknown) {
      setMessage(getErrorMessage(error, 'Unable to enable notifications.'));
    } finally {
      setWorking(false);
    }
  }

  async function handleDisable() {
    setWorking(true);
    setMessage('');
    try {
      const existing = await getExistingSubscription();
      const endpoint = existing ? existing.endpoint : await removePushSubscription();
      await pushAPI.deleteSubscription(endpoint ?? undefined);
      if (existing) {
        await existing.unsubscribe();
      }
      await onStatusChange();
      setEnvironment(getPushEnvironment());
      setMessage('Push notifications are paused on this device.');
    } catch (error: unknown) {
      setMessage(getErrorMessage(error, 'Unable to disable notifications.'));
    } finally {
      setWorking(false);
    }
  }

  if (!status?.configured) {
    return (
      <div className="rounded-3xl border border-amber-400/20 bg-amber-500/10 p-5 text-amber-50">
        <p className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.22em]">
          <ShieldAlert className="h-4 w-4" />
          Push Unavailable
        </p>
        <p className="mt-3 text-sm text-amber-100/80">
          VAPID keys are not configured in the backend yet, so browser notifications cannot be enabled.
        </p>
      </div>
    );
  }

  if (!environment.supported) {
    return (
      <div className="rounded-3xl border border-slate-700/80 bg-slate-900/70 p-5 text-slate-200">
        <p className="text-sm font-semibold uppercase tracking-[0.22em] text-slate-400">Unsupported Device</p>
        <p className="mt-3 text-sm text-slate-400">
          This browser does not support the Web Push APIs EndureIT needs.
        </p>
      </div>
    );
  }

  if (environment.requires_install) {
    return (
      <div className="rounded-3xl border border-sky-400/20 bg-sky-500/10 p-5 text-sky-50">
        <p className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.22em]">
          <Download className="h-4 w-4" />
          Install Required on iPhone
        </p>
        <p className="mt-3 text-sm text-sky-100/85">
          Open Safari&apos;s share menu, choose <span className="font-semibold">Add to Home Screen</span>, then launch EndureIT from the installed app to enable push notifications.
        </p>
      </div>
    );
  }

  const enabled = status.has_active_subscription;

  return (
    <div className="rounded-3xl border border-slate-700/80 bg-slate-900/70 p-5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.22em] text-slate-400">
            Browser Push
          </p>
          <p className="mt-2 text-lg font-semibold text-white">
            {enabled ? 'Notifications are live on this device' : 'Enable alerts for workouts and fueling'}
          </p>
          <p className="mt-1 text-sm text-slate-400">
            Permission: <span className="text-slate-200">{environment.permission}</span>
          </p>
        </div>

        <button
          type="button"
          disabled={working}
          onClick={enabled ? handleDisable : handleEnable}
          className={`inline-flex items-center justify-center gap-2 rounded-2xl px-4 py-3 text-sm font-semibold transition ${
            enabled
              ? 'border border-slate-600 bg-slate-950/70 text-slate-200 hover:border-slate-400'
              : 'bg-[var(--accent-nutrition)] text-white hover:bg-green-400'
          } disabled:cursor-not-allowed disabled:opacity-60`}
        >
          {working ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : enabled ? (
            <BellOff className="h-4 w-4" />
          ) : (
            <Bell className="h-4 w-4" />
          )}
          {working ? 'Updating…' : enabled ? 'Disable Push' : 'Enable Push'}
        </button>
      </div>

      {message && (
        <p className="mt-4 rounded-2xl border border-slate-800 bg-slate-950/60 px-4 py-3 text-sm text-slate-300">
          {message}
        </p>
      )}
    </div>
  );
}
