"""
Periodization templates for running race plans.
Templates are keyed by (distance_km, weeks, level) and define:
  - Phase breakdown (base/build/peak/taper weeks)
  - Weekly day patterns per phase
  - Mileage progression targets
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from app.models.training_plan import FitnessLevel, PlanPhase, WorkoutType


@dataclass
class DayPlan:
    workout_type: WorkoutType
    distance_fraction: float  # fraction of weekly total
    hr_zone: int  # 1-5
    description_template: str
    pace_key: str  # which pace zone to use: easy/marathon/threshold/interval


@dataclass
class WeekPattern:
    """Day-by-day prescription for one week type."""

    phase: PlanPhase
    days: Dict[int, DayPlan]  # 0=Mon … 6=Sun; missing = REST


@dataclass
class PlanTemplate:
    distance_km: float
    weeks: int
    level: FitnessLevel
    peak_weekly_km: float
    # (phase, week_count) in order
    phases: List[Tuple[PlanPhase, int]]
    # Pattern per phase — used for each non-stepback week
    phase_patterns: Dict[PlanPhase, WeekPattern]
    # Override for stepback weeks (every 4th week: ~80% volume)
    stepback_fraction: float = 0.80


# ---------------------------------------------------------------------------
# Day plan shorthands
# ---------------------------------------------------------------------------


def _easy(frac: float, zone: int = 2) -> DayPlan:
    return DayPlan(
        WorkoutType.EASY, frac, zone, "Easy run at conversational effort", "easy"
    )


def _long(frac: float) -> DayPlan:
    return DayPlan(WorkoutType.LONG, frac, 2, "Long run — build aerobic base", "easy")


def _tempo(frac: float) -> DayPlan:
    return DayPlan(
        WorkoutType.TEMPO, frac, 4, "Tempo run at comfortably hard effort", "threshold"
    )


def _intervals(frac: float) -> DayPlan:
    return DayPlan(
        WorkoutType.INTERVALS, frac, 5, "Interval session — quality work", "interval"
    )


def _recovery(frac: float) -> DayPlan:
    return DayPlan(WorkoutType.RECOVERY, frac, 1, "Recovery run — very easy", "easy")


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

TEMPLATES: Dict[Tuple[float, int, str], PlanTemplate] = {}


def _register(t: PlanTemplate) -> None:
    key = (t.distance_km, t.weeks, t.level.value)
    TEMPLATES[key] = t


# --- Half Marathon (21.0975 km) ---

_register(
    PlanTemplate(
        distance_km=21.0975,
        weeks=12,
        level=FitnessLevel.INTERMEDIATE,
        peak_weekly_km=65,
        phases=[
            (PlanPhase.BASE, 4),
            (PlanPhase.BUILD, 5),
            (PlanPhase.PEAK, 2),
            (PlanPhase.TAPER, 1),
        ],
        phase_patterns={
            PlanPhase.BASE: WeekPattern(
                PlanPhase.BASE,
                {
                    1: _easy(0.18),
                    3: _easy(0.20),
                    4: _tempo(0.16),
                    6: _long(0.30),
                },
            ),
            PlanPhase.BUILD: WeekPattern(
                PlanPhase.BUILD,
                {
                    1: _easy(0.15),
                    2: _intervals(0.18),
                    4: _tempo(0.17),
                    5: _easy(0.15),
                    6: _long(0.32),
                },
            ),
            PlanPhase.PEAK: WeekPattern(
                PlanPhase.PEAK,
                {
                    1: _easy(0.12),
                    2: _intervals(0.20),
                    4: _tempo(0.18),
                    6: _long(0.28),
                },
            ),
            PlanPhase.TAPER: WeekPattern(
                PlanPhase.TAPER,
                {
                    1: _easy(0.20),
                    3: _tempo(0.15),
                    5: _recovery(0.10),
                    6: _easy(0.12),
                },
            ),
        },
    )
)

_register(
    PlanTemplate(
        distance_km=21.0975,
        weeks=16,
        level=FitnessLevel.INTERMEDIATE,
        peak_weekly_km=75,
        phases=[
            (PlanPhase.BASE, 5),
            (PlanPhase.BUILD, 7),
            (PlanPhase.PEAK, 3),
            (PlanPhase.TAPER, 1),
        ],
        phase_patterns={
            PlanPhase.BASE: WeekPattern(
                PlanPhase.BASE,
                {
                    1: _easy(0.18),
                    3: _easy(0.20),
                    4: _tempo(0.16),
                    6: _long(0.30),
                },
            ),
            PlanPhase.BUILD: WeekPattern(
                PlanPhase.BUILD,
                {
                    1: _easy(0.15),
                    2: _intervals(0.18),
                    4: _tempo(0.17),
                    5: _easy(0.15),
                    6: _long(0.32),
                },
            ),
            PlanPhase.PEAK: WeekPattern(
                PlanPhase.PEAK,
                {
                    1: _easy(0.12),
                    2: _intervals(0.20),
                    4: _tempo(0.18),
                    6: _long(0.28),
                },
            ),
            PlanPhase.TAPER: WeekPattern(
                PlanPhase.TAPER,
                {
                    1: _easy(0.20),
                    3: _tempo(0.15),
                    5: _recovery(0.10),
                    6: _easy(0.12),
                },
            ),
        },
    )
)

# --- Marathon (42.195 km) ---

_register(
    PlanTemplate(
        distance_km=42.195,
        weeks=16,
        level=FitnessLevel.INTERMEDIATE,
        peak_weekly_km=90,
        phases=[
            (PlanPhase.BASE, 5),
            (PlanPhase.BUILD, 7),
            (PlanPhase.PEAK, 2),
            (PlanPhase.TAPER, 2),
        ],
        phase_patterns={
            PlanPhase.BASE: WeekPattern(
                PlanPhase.BASE,
                {
                    1: _easy(0.16),
                    3: _easy(0.18),
                    4: _tempo(0.14),
                    6: _long(0.32),
                },
            ),
            PlanPhase.BUILD: WeekPattern(
                PlanPhase.BUILD,
                {
                    1: _easy(0.13),
                    2: _intervals(0.16),
                    4: _tempo(0.16),
                    5: _easy(0.14),
                    6: _long(0.35),
                },
            ),
            PlanPhase.PEAK: WeekPattern(
                PlanPhase.PEAK,
                {
                    1: _easy(0.12),
                    2: _intervals(0.18),
                    4: _tempo(0.17),
                    6: _long(0.30),
                },
            ),
            PlanPhase.TAPER: WeekPattern(
                PlanPhase.TAPER,
                {
                    1: _easy(0.18),
                    3: _tempo(0.14),
                    5: _recovery(0.09),
                    6: _easy(0.10),
                },
            ),
        },
    )
)

# --- 10 km ---

_register(
    PlanTemplate(
        distance_km=10.0,
        weeks=8,
        level=FitnessLevel.INTERMEDIATE,
        peak_weekly_km=45,
        phases=[
            (PlanPhase.BASE, 2),
            (PlanPhase.BUILD, 4),
            (PlanPhase.PEAK, 1),
            (PlanPhase.TAPER, 1),
        ],
        phase_patterns={
            PlanPhase.BASE: WeekPattern(
                PlanPhase.BASE,
                {
                    1: _easy(0.20),
                    3: _easy(0.22),
                    6: _long(0.32),
                },
            ),
            PlanPhase.BUILD: WeekPattern(
                PlanPhase.BUILD,
                {
                    1: _easy(0.16),
                    2: _intervals(0.20),
                    4: _tempo(0.18),
                    6: _long(0.28),
                },
            ),
            PlanPhase.PEAK: WeekPattern(
                PlanPhase.PEAK,
                {
                    1: _easy(0.14),
                    2: _intervals(0.22),
                    4: _tempo(0.20),
                    6: _long(0.24),
                },
            ),
            PlanPhase.TAPER: WeekPattern(
                PlanPhase.TAPER,
                {
                    1: _easy(0.22),
                    3: _tempo(0.16),
                    5: _recovery(0.12),
                },
            ),
        },
    )
)

# --- 5 km ---

_register(
    PlanTemplate(
        distance_km=5.0,
        weeks=6,
        level=FitnessLevel.BEGINNER,
        peak_weekly_km=25,
        phases=[
            (PlanPhase.BASE, 2),
            (PlanPhase.BUILD, 3),
            (PlanPhase.TAPER, 1),
        ],
        phase_patterns={
            PlanPhase.BASE: WeekPattern(
                PlanPhase.BASE,
                {
                    1: _easy(0.25),
                    3: _easy(0.28),
                    6: _long(0.30),
                },
            ),
            PlanPhase.BUILD: WeekPattern(
                PlanPhase.BUILD,
                {
                    1: _easy(0.20),
                    2: _intervals(0.22),
                    4: _tempo(0.20),
                    6: _long(0.26),
                },
            ),
            PlanPhase.TAPER: WeekPattern(
                PlanPhase.TAPER,
                {
                    1: _easy(0.25),
                    3: _tempo(0.18),
                    5: _recovery(0.12),
                },
            ),
        },
    )
)


def get_template(
    distance_km: float, total_weeks: int, level: FitnessLevel
) -> PlanTemplate:
    key = (distance_km, total_weeks, level.value)
    if key not in TEMPLATES:
        # Fall back to closest match by distance + level
        candidates = [
            (abs(d - distance_km), w, t)
            for (d, w, lv), t in TEMPLATES.items()
            if lv == level.value
        ]
        if not candidates:
            candidates = [
                (abs(d - distance_km), w, t) for (d, w, _), t in TEMPLATES.items()
            ]
        candidates.sort(key=lambda x: (x[0], abs(x[1] - total_weeks)))
        return candidates[0][2]
    return TEMPLATES[key]


def weeks_for_distance(distance_km: float, level: FitnessLevel) -> List[int]:
    """Return available plan lengths for a given distance + level."""
    return sorted(
        w for (d, w, lv) in TEMPLATES if abs(d - distance_km) < 1 and lv == level.value
    )


def phase_for_week(template: PlanTemplate, week_idx: int) -> PlanPhase:
    """Return the phase for a given 0-indexed week number."""
    cursor = 0
    for phase, count in template.phases:
        if week_idx < cursor + count:
            return phase
        cursor += count
    return PlanPhase.TAPER


def is_stepback_week(week_idx: int) -> bool:
    """Every 4th week (0-indexed: 3, 7, 11 …) is a stepback recovery week."""
    return (week_idx + 1) % 4 == 0


def weekly_km_for_week(template: PlanTemplate, week_idx: int) -> float:
    """Linearly ramp from 60 % to 100 % of peak, with stepback at 80 %."""
    phase = phase_for_week(template, week_idx)
    if phase == PlanPhase.TAPER:
        taper_start = template.weeks - dict(template.phases)[PlanPhase.TAPER]
        taper_progress = (week_idx - taper_start) / max(
            dict(template.phases)[PlanPhase.TAPER], 1
        )
        return template.peak_weekly_km * (1.0 - 0.35 * taper_progress)

    ramp_progress = week_idx / max(
        template.weeks - dict(template.phases).get(PlanPhase.TAPER, 1), 1
    )
    target = template.peak_weekly_km * (0.60 + 0.40 * ramp_progress)

    if is_stepback_week(week_idx):
        return target * template.stepback_fraction
    return target
