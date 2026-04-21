'use client';

import { Flame, RefreshCw } from 'lucide-react';

interface Meal {
  id: number;
  meal_slot: string;
  default_time_local: string | null;
  name: string;
  description: string | null;
  calories: number | null;
  protein_g: number | null;
  carbs_g: number | null;
  fat_g: number | null;
  ingredients: string[];
}

interface MealCardProps {
  meal: Meal;
  onSwap?: (meal: Meal) => void;
}

const SLOT_LABELS: Record<string, string> = {
  breakfast: 'Breakfast',
  snack_am: 'Morning Snack',
  lunch: 'Lunch',
  snack_pm: 'Afternoon Snack',
  dinner: 'Dinner',
  pre_workout: 'Pre-Workout',
  during_workout: 'During Workout',
  post_workout: 'Post-Workout',
};

const SLOT_COLORS: Record<string, string> = {
  pre_workout: 'text-[var(--accent-run)]',
  during_workout: 'text-[var(--accent-run)]',
  post_workout: 'text-[var(--accent-recovery)]',
  breakfast: 'text-yellow-400',
  lunch: 'text-[var(--accent-nutrition)]',
  dinner: 'text-[var(--accent-nutrition)]',
  snack_am: 'text-slate-300',
  snack_pm: 'text-slate-300',
};

function MacroPill({ label, value, unit = 'g' }: { label: string; value: number | null; unit?: string }) {
  if (value == null) return null;
  return (
    <span className="text-xs text-slate-400">
      <span className="text-slate-200 font-medium">{Math.round(value)}{unit}</span> {label}
    </span>
  );
}

export default function MealCard({ meal, onSwap }: MealCardProps) {
  const slotLabel = SLOT_LABELS[meal.meal_slot] ?? meal.meal_slot;
  const slotColor = SLOT_COLORS[meal.meal_slot] ?? 'text-slate-300';

  return (
    <div className="rounded-2xl bg-slate-800/60 border border-slate-700 p-4 space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <span className={`text-xs font-semibold uppercase tracking-wide ${slotColor}`}>
              {slotLabel}
            </span>
            {meal.default_time_local && (
              <span className="text-xs text-slate-500">{meal.default_time_local}</span>
            )}
          </div>
          <h3 className="text-sm font-medium text-white leading-snug">{meal.name}</h3>
          {meal.description && (
            <p className="text-xs text-slate-400 mt-0.5 line-clamp-2">{meal.description}</p>
          )}
        </div>
        {onSwap && (
          <button
            onClick={() => onSwap(meal)}
            className="shrink-0 flex items-center gap-1.5 text-xs text-slate-400 hover:text-[var(--accent-nutrition)] transition-colors px-2 py-1 rounded-lg hover:bg-slate-700"
          >
            <RefreshCw className="w-3 h-3" />
            Swap
          </button>
        )}
      </div>

      {/* Macros row */}
      <div className="flex flex-wrap gap-x-4 gap-y-1">
        {meal.calories && (
          <span className="flex items-center gap-1 text-xs text-slate-400">
            <Flame className="w-3 h-3 text-orange-400" />
            <span className="text-slate-200 font-medium">{Math.round(meal.calories)}</span> kcal
          </span>
        )}
        <MacroPill label="P" value={meal.protein_g} />
        <MacroPill label="C" value={meal.carbs_g} />
        <MacroPill label="F" value={meal.fat_g} />
      </div>

      {/* Ingredients */}
      {meal.ingredients.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {meal.ingredients.slice(0, 6).map((ing, i) => (
            <span
              key={i}
              className="text-xs bg-slate-700/60 text-slate-300 px-2 py-0.5 rounded-full"
            >
              {ing}
            </span>
          ))}
          {meal.ingredients.length > 6 && (
            <span className="text-xs text-slate-500">+{meal.ingredients.length - 6} more</span>
          )}
        </div>
      )}
    </div>
  );
}
