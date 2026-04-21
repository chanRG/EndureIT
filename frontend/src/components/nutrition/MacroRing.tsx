'use client';

import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

interface MacroRingProps {
  calories: number | null;
  protein_g: number | null;
  carbs_g: number | null;
  fat_g: number | null;
  caloriesTarget?: number | null;
}

const COLORS = {
  protein: '#f97316',   // orange (run accent)
  carbs: '#3b82f6',     // blue
  fat: '#a855f7',       // violet (recovery accent)
};

function MacroBar({
  label,
  value,
  color,
}: {
  label: string;
  value: number | null;
  color: string;
}) {
  if (value == null) return null;
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="flex items-center gap-2 text-slate-300">
        <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
        {label}
      </span>
      <span className="font-medium text-white">{Math.round(value)}g</span>
    </div>
  );
}

export default function MacroRing({ calories, protein_g, carbs_g, fat_g, caloriesTarget }: MacroRingProps) {
  const total = (protein_g ?? 0) * 4 + (carbs_g ?? 0) * 4 + (fat_g ?? 0) * 9;

  const data = [
    { name: 'Protein', value: (protein_g ?? 0) * 4, color: COLORS.protein },
    { name: 'Carbs', value: (carbs_g ?? 0) * 4, color: COLORS.carbs },
    { name: 'Fat', value: (fat_g ?? 0) * 9, color: COLORS.fat },
  ].filter((d) => d.value > 0);

  return (
    <div className="rounded-2xl bg-slate-800/60 border border-slate-700 p-5">
      <h3 className="text-sm font-semibold text-[var(--accent-nutrition)] uppercase tracking-wide mb-4">
        Daily Nutrition
      </h3>
      <div className="flex items-center gap-6">
        {/* Ring chart */}
        <div className="relative w-24 h-24 shrink-0">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data.length ? data : [{ name: 'empty', value: 1, color: '#1e293b' }]}
                cx="50%"
                cy="50%"
                innerRadius={28}
                outerRadius={42}
                paddingAngle={2}
                dataKey="value"
                strokeWidth={0}
              >
                {(data.length ? data : [{ color: '#1e293b' }]).map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          {/* Center label */}
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span className="text-sm font-bold text-white">
              {calories ? Math.round(calories) : '—'}
            </span>
            <span className="text-[10px] text-slate-400">kcal</span>
          </div>
        </div>

        {/* Macro bars */}
        <div className="flex-1 space-y-2">
          <MacroBar label="Protein" value={protein_g} color={COLORS.protein} />
          <MacroBar label="Carbs" value={carbs_g} color={COLORS.carbs} />
          <MacroBar label="Fat" value={fat_g} color={COLORS.fat} />
          {caloriesTarget && calories && (
            <div className="pt-1">
              <div className="flex justify-between text-xs text-slate-500 mb-1">
                <span>Target {Math.round(caloriesTarget)} kcal</span>
                <span>{Math.round((calories / caloriesTarget) * 100)}%</span>
              </div>
              <div className="h-1 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-[var(--accent-nutrition)] rounded-full"
                  style={{ width: `${Math.min(100, (calories / caloriesTarget) * 100)}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
