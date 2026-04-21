"""
Training plan endpoints.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.api import deps
from app.core.logging import get_logger
from app.db.database import get_db
from app.models.training_plan import (
    FitnessLevel,
    PlanStatus,
    TrainingPlan,
    WorkoutStatus,
)
from app.models.user import User
from app.services.training_plan.pace_calculator import (
    compute_vdot_from_db,
    upsert_training_paces,
)
from app.services.training_plan.plan_builder import build_plan, get_today_and_week
from app.services.training_plan.templates import weeks_for_distance

logger = get_logger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class CreatePlanRequest(BaseModel):
    goal_distance_km: float
    race_date: date
    days_per_week: int
    level: FitnessLevel
    race_name: Optional[str] = None
    start_date: Optional[date] = None

    @field_validator("days_per_week")
    @classmethod
    def validate_days(cls, v: int) -> int:
        if not 3 <= v <= 6:
            raise ValueError("days_per_week must be between 3 and 6")
        return v

    @field_validator("race_date")
    @classmethod
    def validate_race_date(cls, v: date) -> date:
        if v <= date.today():
            raise ValueError("race_date must be in the future")
        return v


def _serialize_plan(plan: TrainingPlan) -> dict:
    return {
        "id": plan.id,
        "goal_distance_km": plan.goal_distance_km,
        "race_name": plan.race_name,
        "race_date": plan.race_date.isoformat(),
        "start_date": plan.start_date.isoformat(),
        "days_per_week": plan.days_per_week,
        "level": plan.current_fitness_level.value,
        "status": plan.status.value,
        "total_weeks": plan.total_weeks,
        "current_phase": plan.current_phase.value if plan.current_phase else None,
        "vdot": plan.vdot,
        "template_key": plan.template_key,
        "created_at": plan.created_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED)
def create_plan(
    body: CreatePlanRequest,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Create a new training plan. Pauses any existing active plan."""
    try:
        # Refresh VDOT if Strava data available
        if current_user.strava_access_token:
            vdot, source_ids = compute_vdot_from_db(db, current_user)
            if vdot:
                upsert_training_paces(db, current_user, vdot, source_ids)

        plan = build_plan(
            db=db,
            user=current_user,
            goal_distance_km=body.goal_distance_km,
            race_date=body.race_date,
            days_per_week=body.days_per_week,
            level=body.level,
            race_name=body.race_name,
            start_date=body.start_date,
        )
        db.commit()
        db.refresh(plan)
        return _serialize_plan(plan)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to create plan: %s", exc)
        raise HTTPException(
            status_code=500, detail="Failed to create training plan"
        ) from exc


@router.get("/active")
def get_active_plan(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Get the user's current active training plan with today's workout."""
    plan = (
        db.query(TrainingPlan)
        .filter(
            TrainingPlan.user_id == current_user.id,
            TrainingPlan.status == PlanStatus.ACTIVE,
        )
        .first()
    )
    if plan is None:
        raise HTTPException(status_code=404, detail="No active training plan")

    today, week_idx = get_today_and_week(plan)

    # Today's workouts
    today_workouts = [
        _serialize_workout(w)
        for w in plan.planned_workouts
        if w.scheduled_date == today
    ]

    return {
        **_serialize_plan(plan),
        "current_week": week_idx + 1,
        "today_workouts": today_workouts,
    }


@router.get("/{plan_id}")
def get_plan(
    plan_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    plan = _get_plan_or_404(db, plan_id, current_user.id)
    return _serialize_plan(plan)


@router.patch("/{plan_id}")
def update_plan(
    plan_id: int,
    body: dict,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Pause, resume, or abandon a plan."""
    plan = _get_plan_or_404(db, plan_id, current_user.id)
    allowed_status = {s.value for s in PlanStatus}
    new_status = body.get("status")
    if new_status and new_status in allowed_status:
        plan.status = PlanStatus(new_status)
    db.commit()
    db.refresh(plan)
    return _serialize_plan(plan)


@router.get("/options/{distance_km}")
def plan_options(
    distance_km: float,
    level: FitnessLevel = FitnessLevel.INTERMEDIATE,
) -> Any:
    """Return available plan lengths for a given distance and level."""
    available_weeks = weeks_for_distance(distance_km, level)
    return {
        "distance_km": distance_km,
        "level": level.value,
        "available_weeks": available_weeks,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_plan_or_404(db: Session, plan_id: int, user_id: int) -> TrainingPlan:
    plan = (
        db.query(TrainingPlan)
        .filter(TrainingPlan.id == plan_id, TrainingPlan.user_id == user_id)
        .first()
    )
    if plan is None:
        raise HTTPException(status_code=404, detail="Training plan not found")
    return plan


def _serialize_workout(w: Any) -> dict:
    return {
        "id": w.id,
        "scheduled_date": w.scheduled_date.isoformat(),
        "week_number": w.week_number,
        "phase": w.phase.value,
        "workout_type": w.workout_type.value,
        "target_distance_m": w.target_distance_m,
        "target_duration_s": w.target_duration_s,
        "target_pace_min_per_km": w.target_pace_min_per_km,
        "target_hr_zone": w.target_hr_zone,
        "description": w.description,
        "status": w.status.value,
        "matched_strava_id": w.matched_strava_id,
        "match_confidence": w.match_confidence,
    }
