"""
Builds NutritionReminder rows for the next 24 h based on the active
NutritionPlan and PlannedWorkout schedule. Runs daily at 04:00 local time.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

from app.core.logging import get_logger
from app.db.database import SessionLocal
from app.models.nutrition import (
    NutritionPlan,
    NutritionPlanMeal,
    NutritionPlanStatus,
    NutritionReminder,
    ReminderKind,
    ReminderStatus,
)
from app.models.training_plan import PlannedWorkout

logger = get_logger(__name__)


def _parse_time(value: str | None, fallback: tuple[int, int]) -> time:
    if value:
        try:
            hour, minute = value.split(":")
            return time(hour=int(hour), minute=int(minute), tzinfo=timezone.utc)
        except ValueError:
            logger.warning("Invalid meal reminder time %s, using fallback", value)
    return time(hour=fallback[0], minute=fallback[1], tzinfo=timezone.utc)


def _combine(day: date, value: str | None, fallback: tuple[int, int]) -> datetime:
    return datetime.combine(day, _parse_time(value, fallback))


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def _ensure_reminder(
    db,
    *,
    user_id: int,
    meal_id: int | None,
    planned_workout_id: int | None,
    scheduled_at: datetime,
    kind: ReminderKind,
    payload: dict,
) -> bool:
    scheduled_at_iso = _iso(scheduled_at)
    query = db.query(NutritionReminder).filter(
        NutritionReminder.user_id == user_id,
        NutritionReminder.scheduled_at == scheduled_at_iso,
        NutritionReminder.kind == kind.value,
        NutritionReminder.planned_workout_id == planned_workout_id,
    )
    if meal_id is None:
        query = query.filter(NutritionReminder.meal_id.is_(None))
    else:
        query = query.filter(NutritionReminder.meal_id == meal_id)

    if query.first() is not None:
        return False

    db.add(
        NutritionReminder(
            user_id=user_id,
            meal_id=meal_id,
            planned_workout_id=planned_workout_id,
            scheduled_at=scheduled_at_iso,
            kind=kind.value,
            payload=payload,
            status=ReminderStatus.PENDING.value,
        )
    )
    return True


def _workout_start_for_day(
    scheduled_day: date,
    workout: PlannedWorkout,
    meals_by_slot: dict[str, NutritionPlanMeal],
) -> datetime:
    pre_meal = meals_by_slot.get("pre_workout")
    post_meal = meals_by_slot.get("post_workout")

    if pre_meal and pre_meal.default_time_local:
        return _combine(scheduled_day, pre_meal.default_time_local, (5, 30)) + timedelta(minutes=90)

    if post_meal and post_meal.default_time_local and workout.target_duration_s:
        end_plus_thirty = _combine(scheduled_day, post_meal.default_time_local, (9, 0))
        return end_plus_thirty - timedelta(seconds=workout.target_duration_s) - timedelta(minutes=30)

    return _combine(scheduled_day, None, (7, 0))


async def schedule_daily_reminders(ctx: dict, user_id: int) -> dict:
    db = SessionLocal()
    try:
        today = datetime.now(timezone.utc).date()
        plan = (
            db.query(NutritionPlan)
            .filter(
                NutritionPlan.user_id == user_id,
                NutritionPlan.status == NutritionPlanStatus.ACTIVE.value,
            )
            .first()
        )
        if plan is None:
            return {"status": "no_active_plan", "created": 0}

        meals_by_slot = {meal.meal_slot.value if hasattr(meal.meal_slot, "value") else meal.meal_slot: meal for meal in plan.meals}
        workouts = (
            db.query(PlannedWorkout)
            .filter(
                PlannedWorkout.user_id == user_id,
                PlannedWorkout.scheduled_date == today,
            )
            .order_by(PlannedWorkout.day_of_week.asc())
            .all()
        )

        created = 0
        regular_slots = [
            ("breakfast", (7, 30)),
            ("snack_am", (10, 30)),
            ("lunch", (13, 0)),
            ("snack_pm", (16, 30)),
            ("dinner", (19, 30)),
        ]

        for slot, fallback in regular_slots:
            meal = meals_by_slot.get(slot)
            if meal is None:
                continue
            when = _combine(today, meal.default_time_local, fallback)
            created += int(
                _ensure_reminder(
                    db,
                    user_id=user_id,
                    meal_id=meal.id,
                    planned_workout_id=None,
                    scheduled_at=when,
                    kind=ReminderKind.MEAL,
                    payload={
                        "title": meal.name,
                        "body": meal.description or "Time for your scheduled meal.",
                        "url": "/nutrition",
                        "slot": slot,
                    },
                )
            )

        for workout in workouts:
            duration_s = workout.target_duration_s or 3600
            start_dt = _workout_start_for_day(today, workout, meals_by_slot)
            end_dt = start_dt + timedelta(seconds=duration_s)

            pre_meal = meals_by_slot.get("pre_workout")
            created += int(
                _ensure_reminder(
                    db,
                    user_id=user_id,
                    meal_id=pre_meal.id if pre_meal else None,
                    planned_workout_id=workout.id,
                    scheduled_at=start_dt - timedelta(minutes=90),
                    kind=ReminderKind.PRE_WORKOUT_FUEL,
                    payload={
                        "title": "Pre-workout fuel",
                        "body": f"Fuel up before {workout.description.lower()}",
                        "url": "/settings/notifications",
                    },
                )
            )

            if duration_s > 90 * 60:
                gel_time = start_dt + timedelta(minutes=45)
                during_meal = meals_by_slot.get("during_workout")
                while gel_time < end_dt:
                    created += int(
                        _ensure_reminder(
                            db,
                            user_id=user_id,
                            meal_id=during_meal.id if during_meal else None,
                            planned_workout_id=workout.id,
                            scheduled_at=gel_time,
                            kind=ReminderKind.IN_WORKOUT_GEL,
                            payload={
                                "title": "Fuel mid-session",
                                "body": "Take a gel or carbs to stay on top of the workload.",
                                "url": "/settings/notifications",
                            },
                        )
                    )
                    gel_time += timedelta(minutes=30)

            post_meal = meals_by_slot.get("post_workout")
            created += int(
                _ensure_reminder(
                    db,
                    user_id=user_id,
                    meal_id=post_meal.id if post_meal else None,
                    planned_workout_id=workout.id,
                    scheduled_at=end_dt + timedelta(minutes=30),
                    kind=ReminderKind.POST_WORKOUT_RECOVERY,
                    payload={
                        "title": "Recovery window",
                        "body": "Refuel soon after the session to support recovery.",
                        "url": "/settings/notifications",
                    },
                )
            )

        db.commit()
        return {"status": "scheduled", "created": created, "workouts": len(workouts)}
    except Exception:
        db.rollback()
        logger.exception("schedule_daily_reminders failed for user %s", user_id)
        raise
    finally:
        db.close()
