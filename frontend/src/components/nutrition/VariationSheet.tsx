'use client';

import { useState } from 'react';
import { X, RefreshCw, Check } from 'lucide-react';
import { nutritionAPI } from '@/lib/api';

interface Variation {
  id: number;
  name: string;
  calories: number | null;
  protein_g: number | null;
  carbs_g: number | null;
  fat_g: number | null;
  macro_drift: Record<string, number>;
  ingredients: string[];
}

interface Meal {
  id: number;
  name: string;
  calories: number | null;
  protein_g: number | null;
}

interface VariationSheetProps {
  meal: Meal;
  variations: Variation[];
  onClose: () => void;
  onSelected: () => void;
}

function DriftChip({ label, value }: { label: string; value: number | undefined }) {
  if (value == null) return null;
  const pct = Math.round(value * 100);
  const color = Math.abs(pct) <= 5
    ? 'text-emerald-400'
    : Math.abs(pct) <= 10
    ? 'text-yellow-400'
    : 'text-red-400';
  return (
    <span className={`text-[10px] font-medium ${color}`}>
      {pct > 0 ? '+' : ''}{pct}% {label}
    </span>
  );
}

export default function VariationSheet({ meal, variations, onClose, onSelected }: VariationSheetProps) {
  const [selecting, setSelecting] = useState<number | null>(null);
  const [requesting, setRequesting] = useState(false);

  async function handleSelect(variationId: number) {
    setSelecting(variationId);
    try {
      await nutritionAPI.selectVariation(meal.id, variationId);
      onSelected();
    } catch {
      setSelecting(null);
    }
  }

  async function handleRegenerate() {
    setRequesting(true);
    try {
      await nutritionAPI.requestVariations(meal.id);
    } finally {
      setRequesting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-lg bg-slate-900 border border-slate-700 rounded-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-700">
          <div>
            <h2 className="text-sm font-semibold text-white">Swap: {meal.name}</h2>
            <p className="text-xs text-slate-400">Pick a macro-preserving alternative</p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Variations list */}
        <div className="p-4 space-y-3 max-h-[60vh] overflow-y-auto">
          {variations.length === 0 ? (
            <div className="text-center text-slate-400 py-8 space-y-3">
              <p className="text-sm">No variations yet.</p>
              <button
                onClick={handleRegenerate}
                disabled={requesting}
                className="inline-flex items-center gap-2 text-sm text-[var(--accent-nutrition)] hover:underline disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${requesting ? 'animate-spin' : ''}`} />
                {requesting ? 'Generating...' : 'Generate with AI'}
              </button>
            </div>
          ) : (
            variations.map((v) => (
              <div
                key={v.id}
                className="rounded-xl border border-slate-700 bg-slate-800/60 p-4 space-y-2"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium text-white">{v.name}</p>
                    <div className="flex flex-wrap gap-2 mt-1">
                      <DriftChip label="cal" value={v.macro_drift?.calories} />
                      <DriftChip label="P" value={v.macro_drift?.protein_g} />
                      <DriftChip label="C" value={v.macro_drift?.carbs_g} />
                      <DriftChip label="F" value={v.macro_drift?.fat_g} />
                    </div>
                  </div>
                  <button
                    onClick={() => handleSelect(v.id)}
                    disabled={selecting === v.id}
                    className="shrink-0 flex items-center gap-1.5 text-xs bg-[var(--accent-nutrition)]/20 text-[var(--accent-nutrition)] hover:bg-[var(--accent-nutrition)]/30 px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50"
                  >
                    {selecting === v.id ? (
                      <RefreshCw className="w-3 h-3 animate-spin" />
                    ) : (
                      <Check className="w-3 h-3" />
                    )}
                    Select
                  </button>
                </div>

                {v.ingredients.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {v.ingredients.slice(0, 5).map((ing, i) => (
                      <span key={i} className="text-[10px] bg-slate-700 text-slate-300 px-1.5 py-0.5 rounded-full">
                        {ing}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        {variations.length > 0 && (
          <div className="px-4 pb-4">
            <button
              onClick={handleRegenerate}
              disabled={requesting}
              className="w-full flex items-center justify-center gap-2 text-sm text-slate-400 hover:text-[var(--accent-nutrition)] py-2 border border-slate-700 rounded-xl hover:border-[var(--accent-nutrition)]/40 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${requesting ? 'animate-spin' : ''}`} />
              {requesting ? 'Generating more...' : 'Regenerate with AI'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
