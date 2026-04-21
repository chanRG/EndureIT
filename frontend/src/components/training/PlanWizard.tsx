'use client';

import { useState } from 'react';
import { trainingAPI } from '@/lib/api';

interface PlanWizardProps {
  onCreated: () => void;
  onCancel: () => void;
}

const DISTANCES = [
  { label: '5K', km: 5.0 },
  { label: '10K', km: 10.0 },
  { label: 'Half Marathon', km: 21.0975 },
  { label: 'Marathon', km: 42.195 },
];

const LEVELS = [
  { label: 'Beginner', value: 'beginner' },
  { label: 'Intermediate', value: 'intermediate' },
];

export default function PlanWizard({ onCreated, onCancel }: PlanWizardProps) {
  const [step, setStep] = useState(0);
  const [distanceKm, setDistanceKm] = useState<number | null>(null);
  const [level, setLevel] = useState('intermediate');
  const [raceDate, setRaceDate] = useState('');
  const [raceName, setRaceName] = useState('');
  const [daysPerWeek, setDaysPerWeek] = useState(4);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const minDate = new Date();
  minDate.setDate(minDate.getDate() + 28);
  const minDateStr = minDate.toISOString().split('T')[0];

  async function handleCreate() {
    if (!distanceKm || !raceDate) return;
    setLoading(true);
    setError('');
    try {
      await trainingAPI.createPlan({
        goal_distance_km: distanceKm,
        race_date: raceDate,
        days_per_week: daysPerWeek,
        level,
        race_name: raceName || undefined,
      });
      onCreated();
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? 'Failed to create plan. Try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-2xl bg-slate-800/80 border border-slate-700 p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Create Training Plan</h2>
        <button onClick={onCancel} className="text-slate-500 hover:text-slate-300 text-sm">
          Cancel
        </button>
      </div>

      {step === 0 && (
        <div className="space-y-4">
          <p className="text-sm text-slate-400">What distance are you training for?</p>
          <div className="grid grid-cols-2 gap-3">
            {DISTANCES.map((d) => (
              <button
                key={d.km}
                onClick={() => { setDistanceKm(d.km); setStep(1); }}
                className={`rounded-xl border p-4 text-left transition-all hover:border-orange-500/60 ${
                  distanceKm === d.km
                    ? 'border-orange-500 bg-orange-500/10'
                    : 'border-slate-600 bg-slate-700/40'
                }`}
              >
                <div className="text-base font-semibold text-white">{d.label}</div>
                <div className="text-xs text-slate-400">{d.km} km</div>
              </button>
            ))}
          </div>
        </div>
      )}

      {step === 1 && (
        <div className="space-y-4">
          <p className="text-sm text-slate-400">What's your fitness level?</p>
          <div className="grid grid-cols-2 gap-3">
            {LEVELS.map((l) => (
              <button
                key={l.value}
                onClick={() => { setLevel(l.value); setStep(2); }}
                className={`rounded-xl border p-4 text-left transition-all hover:border-orange-500/60 ${
                  level === l.value
                    ? 'border-orange-500 bg-orange-500/10'
                    : 'border-slate-600 bg-slate-700/40'
                }`}
              >
                <div className="text-base font-semibold text-white">{l.label}</div>
              </button>
            ))}
          </div>
          <button onClick={() => setStep(0)} className="text-xs text-slate-500 hover:text-slate-300">
            ← Back
          </button>
        </div>
      )}

      {step === 2 && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1">Race name (optional)</label>
            <input
              type="text"
              value={raceName}
              onChange={(e) => setRaceName(e.target.value)}
              placeholder="e.g. Berlin Marathon 2025"
              className="w-full rounded-lg bg-slate-700 border border-slate-600 text-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500/50"
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Race date</label>
            <input
              type="date"
              value={raceDate}
              min={minDateStr}
              onChange={(e) => setRaceDate(e.target.value)}
              className="w-full rounded-lg bg-slate-700 border border-slate-600 text-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500/50"
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">
              Training days per week: <span className="text-white font-medium">{daysPerWeek}</span>
            </label>
            <input
              type="range"
              min={3}
              max={6}
              value={daysPerWeek}
              onChange={(e) => setDaysPerWeek(Number(e.target.value))}
              className="w-full accent-orange-500"
            />
            <div className="flex justify-between text-xs text-slate-500 mt-1">
              <span>3</span><span>4</span><span>5</span><span>6</span>
            </div>
          </div>

          {error && <p className="text-sm text-red-400">{error}</p>}

          <div className="flex gap-3">
            <button
              onClick={() => setStep(1)}
              className="flex-1 rounded-lg border border-slate-600 text-slate-300 py-2 text-sm hover:bg-slate-700"
            >
              Back
            </button>
            <button
              onClick={handleCreate}
              disabled={!raceDate || loading}
              className="flex-1 rounded-lg bg-orange-500 text-white py-2 text-sm font-medium hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Creating...' : 'Create Plan'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
