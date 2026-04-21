'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { nutritionAPI } from '@/lib/api';
import MacroRing from '@/components/nutrition/MacroRing';
import MealCard from '@/components/nutrition/MealCard';
import VariationSheet from '@/components/nutrition/VariationSheet';
import { Upload, Loader2, AlertCircle, Leaf } from 'lucide-react';

interface NutritionPlan {
  id: number;
  status: string;
  source_filename: string | null;
  daily_calories_target: number | null;
  daily_protein_g: number | null;
  daily_carbs_g: number | null;
  daily_fat_g: number | null;
  notes: string | null;
  meals: any[];
}

export default function NutritionPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [plan, setPlan] = useState<NutritionPlan | null>(null);
  const [loadingPlan, setLoadingPlan] = useState(true);
  const [uploadError, setUploadError] = useState('');
  const [uploading, setUploading] = useState(false);
  const [swapMeal, setSwapMeal] = useState<any | null>(null);
  const [swapVariations, setSwapVariations] = useState<any[]>([]);
  const [loadingVariations, setLoadingVariations] = useState(false);

  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!authLoading && !user) router.push('/login');
  }, [user, authLoading, router]);

  useEffect(() => {
    if (!user) return;
    fetchPlan();
  }, [user]);

  async function fetchPlan() {
    setLoadingPlan(true);
    try {
      const data = await nutritionAPI.getActivePlan();
      setPlan(data);
    } catch {
      setPlan(null);
    } finally {
      setLoadingPlan(false);
    }
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadError('');
    try {
      await nutritionAPI.uploadPdf(file);
      // Plan is parsing — poll or just show status
      await fetchPlan();
    } catch (err: any) {
      setUploadError(err?.response?.data?.detail ?? 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = '';
    }
  }

  async function handleSwapClick(meal: any) {
    setSwapMeal(meal);
    setLoadingVariations(true);
    try {
      const data = await nutritionAPI.getMeal(meal.id);
      setSwapVariations(data.variations ?? []);
    } catch {
      setSwapVariations([]);
    } finally {
      setLoadingVariations(false);
    }
  }

  if (authLoading || !user) return null;

  const sortedMeals = plan?.meals ? [...plan.meals].sort((a, b) => a.ordering - b.ordering) : [];

  return (
    <div className="min-h-screen bg-[#0f172a] text-white">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-[#0f172a]/90 backdrop-blur border-b border-slate-800 px-4 py-3 flex items-center justify-between">
        <h1 className="text-lg font-semibold">Nutrition</h1>
        <button
          onClick={() => fileRef.current?.click()}
          disabled={uploading}
          className="flex items-center gap-1.5 bg-[var(--accent-nutrition)]/20 hover:bg-[var(--accent-nutrition)]/30 text-[var(--accent-nutrition)] text-sm font-medium px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50"
        >
          {uploading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Upload className="w-4 h-4" />
          )}
          {uploading ? 'Uploading...' : 'Upload PDF'}
        </button>
        <input ref={fileRef} type="file" accept=".pdf" className="hidden" onChange={handleUpload} />
      </div>

      <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
        {uploadError && (
          <div className="flex items-center gap-2 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 text-sm">
            <AlertCircle className="w-4 h-4 shrink-0" />
            {uploadError}
          </div>
        )}

        {/* Loading state */}
        {loadingPlan && (
          <div className="space-y-3">
            <div className="h-32 rounded-2xl bg-slate-800/40 animate-pulse" />
            <div className="h-20 rounded-2xl bg-slate-800/40 animate-pulse" />
            <div className="h-20 rounded-2xl bg-slate-800/40 animate-pulse" />
          </div>
        )}

        {/* Parsing state */}
        {!loadingPlan && plan?.status === 'parsing' && (
          <div className="rounded-2xl bg-slate-800/60 border border-slate-700 p-8 text-center space-y-3">
            <Loader2 className="w-8 h-8 text-[var(--accent-nutrition)] mx-auto animate-spin" />
            <p className="text-white font-medium">Parsing your nutrition plan…</p>
            <p className="text-sm text-slate-400">This usually takes under a minute.</p>
          </div>
        )}

        {/* Active plan */}
        {!loadingPlan && plan?.status === 'active' && (
          <>
            <MacroRing
              calories={plan.daily_calories_target}
              protein_g={plan.daily_protein_g}
              carbs_g={plan.daily_carbs_g}
              fat_g={plan.daily_fat_g}
            />

            {plan.notes && (
              <div className="rounded-xl bg-slate-800/40 border border-slate-700 px-4 py-3 text-sm text-slate-300">
                {plan.notes}
              </div>
            )}

            <section className="space-y-3">
              <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wide">
                Meal Plan ({sortedMeals.length} meals)
              </h2>
              {sortedMeals.map((meal) => (
                <MealCard key={meal.id} meal={meal} onSwap={handleSwapClick} />
              ))}
            </section>
          </>
        )}

        {/* No plan state */}
        {!loadingPlan && !plan && (
          <div className="rounded-2xl bg-slate-800/60 border border-slate-700 p-8 text-center space-y-4">
            <Leaf className="w-10 h-10 text-slate-600 mx-auto" />
            <div>
              <p className="text-white font-medium mb-1">No nutrition plan yet</p>
              <p className="text-sm text-slate-400">
                Upload your dietitian&apos;s PDF to get personalised meal guidance and fueling reminders.
              </p>
            </div>
            <button
              onClick={() => fileRef.current?.click()}
              disabled={uploading}
              className="inline-flex items-center gap-2 bg-[var(--accent-nutrition)] hover:bg-green-500 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
            >
              <Upload className="w-4 h-4" />
              Upload PDF
            </button>
          </div>
        )}
      </div>

      {/* Variation Sheet */}
      {swapMeal && (
        <VariationSheet
          meal={swapMeal}
          variations={loadingVariations ? [] : swapVariations}
          onClose={() => { setSwapMeal(null); setSwapVariations([]); }}
          onSelected={() => { setSwapMeal(null); setSwapVariations([]); fetchPlan(); }}
        />
      )}
    </div>
  );
}
