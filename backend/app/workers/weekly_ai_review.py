"""
Claude AI weekly training plan review.
Cron: Sunday 21:00 UTC — enqueued by scheduler.py for every active plan.

Flow:
  1. Load plan, last-7-day completed workouts, next-7-day planned workouts.
  2. Call suggest_week_adjustments (Claude tool-use with deterministic fallback).
  3. If injury_flag: pause plan + replace next 7 days with easy recovery runs.
  4. Otherwise: apply bounded proposals to the database.
  5. Stamp last_ai_review_at, persist ai_notes.
  6. Write a ClaudeAuditLog row (no PII, token counts only).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from app.core.logging import get_logger
from app.db.database import SessionLocal
from app.models.claude_audit import ClaudeAuditLog
from app.models.training_plan import (
    PlannedWorkout,
    PlanStatus,
    TrainingPace,
    TrainingPlan,
    WorkoutStatus,
    WorkoutType,
)
from app.services.training_plan.ai_adjuster import (
    apply_adjustments,
    suggest_week_adjustments,
)

logger = get_logger(__name__)

# Distance for recovery runs inserted during an injury-risk microcycle (5 km easy)
_RECOVERY_RUN_DISTANCE_M = 5_000.0


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _insert_recovery_microcycle(
    db,
    plan: TrainingPlan,
    from_date: date,
) -> int:
    """
    Replace all PLANNED (non-rest/non-recovery) workouts in the next 7 days
    with easy recovery runs at a conservative fixed distance.
    Returns the count of workouts replaced.
    """
    until_date = from_date + timedelta(days=7)
    workouts = (
        db.query(PlannedWorkout)
        .filter(
            PlannedWorkout.plan_id == plan.id,
            PlannedWorkout.scheduled_date >= from_date,
            PlannedWorkout.scheduled_date < until_date,
            PlannedWorkout.status == WorkoutStatus.PLANNED.value,
        )
        .all()
    )
    replaced = 0
    for w in workouts:
        wtype = w.workout_type
        if isinstance(wtype, str):
            try:
                wtype = WorkoutType(wtype)
            except ValueError:
                wtype = WorkoutType.EASY
        if wtype in {WorkoutType.REST, WorkoutType.RECOVERY}:
            continue
        w.workout_type = WorkoutType.RECOVERY
        w.target_distance_m = _RECOVERY_RUN_DISTANCE_M
        # ~30 min easy jog at roughly 6 min/km
        w.target_duration_s = 30 * 60
        w.rationale = "Recovery microcycle — AI flagged elevated injury risk. Ease back and see a professional if discomfort persists."
        replaced += 1
    return replaced


async def ai_weekly_review(ctx: dict, plan_id: int) -> dict:
    """
    arq job entry point. Accepts plan_id, runs the full review pipeline.
    Never raises — on any unhandled error returns a status dict so arq
    marks the job as succeeded (we don't want infinite retries on non-transient errors).
    """
    db = SessionLocal()
    outcome = "ok"
    error_summary: str | None = None
    result_data: dict = {}
    user_id: int | None = None

    try:
        plan = db.query(TrainingPlan).filter(TrainingPlan.id == plan_id).first()
        if plan is None:
            return {"status": "plan_not_found", "plan_id": plan_id}
        if plan.status != PlanStatus.ACTIVE:
            return {"status": "plan_not_active", "plan_id": plan_id}

        user_id = plan.user_id
        today = datetime.now(timezone.utc).date()

        # Last 7 days: completed workouts
        week_ago = today - timedelta(days=7)
        recent_completed = (
            db.query(PlannedWorkout)
            .filter(
                PlannedWorkout.plan_id == plan_id,
                PlannedWorkout.scheduled_date >= week_ago,
                PlannedWorkout.scheduled_date < today,
                PlannedWorkout.status == WorkoutStatus.COMPLETED.value,
            )
            .order_by(PlannedWorkout.scheduled_date.asc())
            .all()
        )

        # Next 7 days: planned workouts (the ones we may adjust)
        next_week_end = today + timedelta(days=7)
        next_week = (
            db.query(PlannedWorkout)
            .filter(
                PlannedWorkout.plan_id == plan_id,
                PlannedWorkout.scheduled_date >= today,
                PlannedWorkout.scheduled_date < next_week_end,
                PlannedWorkout.status == WorkoutStatus.PLANNED.value,
            )
            .order_by(PlannedWorkout.scheduled_date.asc())
            .all()
        )

        if not next_week:
            return {"status": "no_planned_workouts", "plan_id": plan_id}

        paces = (
            db.query(TrainingPace).filter(TrainingPace.user_id == plan.user_id).first()
        )

        # --- Call Claude (with deterministic fallback built in) ---
        review = suggest_week_adjustments(plan, next_week, recent_completed, paces)

        applied_count = 0
        replaced_count = 0

        if review.injury_flag:
            # Auto-pause plan and insert recovery microcycle
            plan.status = PlanStatus.PAUSED
            plan.ai_notes = (
                f"[{today}] AI flagged elevated injury risk: {review.injury_flag}. "
                "Plan paused. Resume after recovery."
            )
            replaced_count = _insert_recovery_microcycle(db, plan, today)
            logger.warning(
                "Plan %d paused — injury risk flag: %s", plan_id, review.injury_flag
            )
            result_data = {
                "status": "injury_flag",
                "reason": review.injury_flag,
                "workouts_replaced": replaced_count,
            }
        else:
            # Apply bounded proposals
            workout_map = {w.id: w for w in next_week}
            applied = apply_adjustments(review.proposals, workout_map, next_week)
            applied_count = len(applied)
            notes_parts = [
                f"[{today}] AI review: {len(review.proposals)} proposal(s), {applied_count} applied."
            ]
            for w, proposal in applied:
                notes_parts.append(
                    f"  • ID {w.id} ({w.scheduled_date}): {proposal.rationale}"
                )
            if applied_count:
                plan.ai_notes = "\n".join(notes_parts)
            result_data = {
                "status": "adjusted",
                "proposals": len(review.proposals),
                "applied": applied_count,
            }

        plan.last_ai_review_at = datetime.now(timezone.utc)

        # Audit log (token counts only, no PII)
        db.add(
            ClaudeAuditLog(
                user_id=user_id,
                feature="weekly_review",
                model="claude-sonnet-4-6",
                input_tokens=review.input_tokens,
                output_tokens=review.output_tokens,
                cache_read_tokens=review.cache_read_tokens,
                cache_write_tokens=review.cache_write_tokens,
                outcome=outcome,
            )
        )

        db.commit()
        logger.info(
            "Weekly review plan=%d: proposals=%d applied=%d replaced=%d injury=%s",
            plan_id,
            len(review.proposals),
            applied_count,
            replaced_count,
            bool(review.injury_flag),
        )
        return result_data

    except Exception as exc:
        db.rollback()
        outcome = "error"
        error_summary = str(exc)[:500]
        logger.exception("ai_weekly_review failed for plan %d", plan_id)

        # Still write the audit log so we can track error rates
        try:
            db.add(
                ClaudeAuditLog(
                    user_id=user_id,
                    feature="weekly_review",
                    model="claude-sonnet-4-6",
                    input_tokens=0,
                    output_tokens=0,
                    cache_read_tokens=0,
                    cache_write_tokens=0,
                    outcome="error",
                    error_summary=error_summary,
                )
            )
            db.commit()
        except Exception:
            db.rollback()

        return {"status": "error", "plan_id": plan_id, "error": error_summary}
    finally:
        db.close()
