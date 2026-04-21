"""
Deterministic training plan builder.

`build_plan` is the source of truth — it creates a TrainingPlan and all
PlannedWorkout rows from a periodization template without any AI involvement.
AI adjustments are applied separately via `apply_adjustments`.
"""

from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.training_plan import (
    FitnessLevel,
    PlanPhase,
    PlanStatus,
    PlannedWorkout,
    TrainingPace,
    TrainingPlan,
    WorkoutStatus,
)
from app.models.user import User
from app.services.training_plan.templates import (
    PlanTemplate,
    get_template,
    is_stepback_week,
    phase_for_week,
    weekly_km_for_week,
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_today_and_week(plan: TrainingPlan) -> tuple[date, int]:
    """Return (today, current_week_index) for an active plan."""
    today = date.today()
    delta = (today - plan.start_date).days
    week_idx = max(0, delta // 7)
    return today, week_idx


def _monday_of_week(start_date: date, week_idx: int) -> date:
    """Return the Monday for week_idx (0-based)."""
    return start_date + timedelta(weeks=week_idx)


def _pace_description(pace_key: str, paces: Optional[TrainingPace]) -> str:
    """Format a human-readable pace hint from the user's TrainingPace record."""
    if paces is None:
        return ""
    mapping = {
        "easy": paces.easy_pace,
        "marathon": paces.marathon_pace,
        "threshold": paces.threshold_pace,
        "interval": paces.interval_pace,
    }
    pace_val = mapping.get(pace_key)
    if pace_val is None:
        return ""
    minutes = int(pace_val)
    seconds = round((pace_val - minutes) * 60)
    return f" (~{minutes}:{seconds:02d}/km)"


def _build_workout_description(
    day_plan, distance_km: float, paces: Optional[TrainingPace]
) -> str:
    pace_hint = _pace_description(day_plan.pace_key, paces)
    return f"{day_plan.description_template}{pace_hint} — {distance_km:.1f} km"


# ---------------------------------------------------------------------------
# Core builder
# ---------------------------------------------------------------------------


def build_plan(
    db: Session,
    user: User,
    goal_distance_km: float,
    race_date: date,
    days_per_week: int,
    level: FitnessLevel,
    race_name: Optional[str] = None,
    start_date: Optional[date] = None,
) -> TrainingPlan:
    """
    Create a TrainingPlan + all PlannedWorkout rows for a user.

    Deactivates any existing active plan first (only one active plan per user).
    """
    today = date.today()
    if start_date is None:
        # Next Monday
        days_to_monday = (7 - today.weekday()) % 7 or 7
        start_date = today + timedelta(days=days_to_monday)

    total_weeks = math.ceil((race_date - start_date).days / 7)
    if total_weeks < 4:
        raise ValueError(
            f"Race date too soon: only {total_weeks} weeks available (min 4)."
        )

    template = get_template(goal_distance_km, total_weeks, level)

    # Deactivate existing active plan
    existing = (
        db.query(TrainingPlan)
        .filter(
            TrainingPlan.user_id == user.id, TrainingPlan.status == PlanStatus.ACTIVE
        )
        .first()
    )
    if existing:
        existing.status = PlanStatus.PAUSED
        logger.info("Paused existing active plan %d for user %d", existing.id, user.id)

    # Resolve training paces (optional — plan works without them)
    paces = db.query(TrainingPace).filter(TrainingPace.user_id == user.id).first()

    plan = TrainingPlan(
        user_id=user.id,
        goal_distance_km=goal_distance_km,
        race_name=race_name,
        race_date=race_date,
        start_date=start_date,
        days_per_week=days_per_week,
        current_fitness_level=level,
        template_key=f"{goal_distance_km}_{template.weeks}wk_{level.value}",
        status=PlanStatus.ACTIVE,
        total_weeks=template.weeks,
        current_phase=phase_for_week(template, 0),
        vdot=paces.vdot if paces else None,
        max_hr=paces.max_hr if paces else None,
        threshold_hr=paces.threshold_hr if paces else None,
    )
    db.add(plan)
    db.flush()  # get plan.id

    _generate_workouts(db, plan, template, paces)

    db.flush()
    logger.info(
        "Built plan %d for user %d: %s %d-week %s",
        plan.id,
        user.id,
        goal_distance_km,
        template.weeks,
        level.value,
    )
    return plan


def _generate_workouts(
    db: Session,
    plan: TrainingPlan,
    template: PlanTemplate,
    paces: Optional[TrainingPace],
) -> None:
    """Insert all PlannedWorkout rows for a plan."""
    for week_idx in range(template.weeks):
        phase = phase_for_week(template, week_idx)
        pattern = template.phase_patterns.get(phase)
        if pattern is None:
            continue

        week_km = weekly_km_for_week(template, week_idx)
        stepback = is_stepback_week(week_idx)
        monday = _monday_of_week(plan.start_date, week_idx)

        for day_offset, day_plan in pattern.days.items():
            scheduled = monday + timedelta(days=day_offset)
            distance_km = week_km * day_plan.distance_fraction
            if stepback:
                distance_km *= template.stepback_fraction

            distance_m = distance_km * 1000.0

            # Estimate duration from pace (use easy pace as baseline if no specific pace)
            target_pace = None
            if paces:
                pace_map = {
                    "easy": paces.easy_pace,
                    "marathon": paces.marathon_pace,
                    "threshold": paces.threshold_pace,
                    "interval": paces.interval_pace,
                }
                target_pace = pace_map.get(day_plan.pace_key, paces.easy_pace)

            duration_s: Optional[int] = None
            if target_pace and target_pace > 0:
                duration_s = int(round(target_pace * 60 * distance_km))

            description = _build_workout_description(day_plan, distance_km, paces)

            workout = PlannedWorkout(
                plan_id=plan.id,
                user_id=plan.user_id,
                scheduled_date=scheduled,
                day_of_week=day_offset,
                week_number=week_idx + 1,
                phase=phase,
                workout_type=day_plan.workout_type,
                target_distance_m=distance_m,
                target_duration_s=duration_s,
                target_pace_min_per_km=target_pace,
                target_pace_range=(
                    {
                        "min": round(target_pace * 0.95, 2),
                        "max": round(target_pace * 1.05, 2),
                    }
                    if target_pace
                    else None
                ),
                target_hr_zone=day_plan.hr_zone,
                description=description,
                status=WorkoutStatus.PLANNED,
            )
            db.add(workout)


# ---------------------------------------------------------------------------
# Post-build helpers
# ---------------------------------------------------------------------------


def regenerate_future_weeks(db: Session, plan: TrainingPlan, from_week: int) -> None:
    """
    Delete all planned (unmatched) workouts from from_week onward and regenerate.
    Used after AI adjustments or missed-week recovery.
    """
    from sqlalchemy import and_

    cutoff_date = _monday_of_week(plan.start_date, from_week)
    db.query(PlannedWorkout).filter(
        and_(
            PlannedWorkout.plan_id == plan.id,
            PlannedWorkout.scheduled_date >= cutoff_date,
            PlannedWorkout.status == WorkoutStatus.PLANNED,
        )
    ).delete(synchronize_session="fetch")

    template = get_template(
        plan.goal_distance_km, plan.total_weeks, plan.current_fitness_level
    )
    paces = db.query(TrainingPace).filter(TrainingPace.user_id == plan.user_id).first()

    for week_idx in range(from_week, template.weeks):
        phase = phase_for_week(template, week_idx)
        pattern = template.phase_patterns.get(phase)
        if pattern is None:
            continue

        week_km = weekly_km_for_week(template, week_idx)
        stepback = is_stepback_week(week_idx)
        monday = _monday_of_week(plan.start_date, week_idx)

        for day_offset, day_plan in pattern.days.items():
            scheduled = monday + timedelta(days=day_offset)
            distance_km = week_km * day_plan.distance_fraction
            if stepback:
                distance_km *= template.stepback_fraction

            target_pace = None
            if paces:
                pace_map = {
                    "easy": paces.easy_pace,
                    "marathon": paces.marathon_pace,
                    "threshold": paces.threshold_pace,
                    "interval": paces.interval_pace,
                }
                target_pace = pace_map.get(day_plan.pace_key, paces.easy_pace)

            duration_s = None
            if target_pace and target_pace > 0:
                duration_s = int(round(target_pace * 60 * distance_km))

            description = _build_workout_description(
                day_plan, distance_km * 1000 / 1000, paces
            )

            workout = PlannedWorkout(
                plan_id=plan.id,
                user_id=plan.user_id,
                scheduled_date=scheduled,
                day_of_week=day_offset,
                week_number=week_idx + 1,
                phase=phase,
                workout_type=day_plan.workout_type,
                target_distance_m=distance_km * 1000,
                target_duration_s=duration_s,
                target_pace_min_per_km=target_pace,
                target_hr_zone=day_plan.hr_zone,
                description=description,
                status=WorkoutStatus.PLANNED,
            )
            db.add(workout)

    db.flush()
    logger.info("Regenerated workouts from week %d for plan %d", from_week, plan.id)
