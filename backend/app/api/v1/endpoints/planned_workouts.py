"""
Planned workout endpoints.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api import deps
from app.core.logging import get_logger
from app.db.database import get_db
from app.models.strava_activity import StravaActivity
from app.models.training_plan import PlannedWorkout, WorkoutStatus
from app.models.user import User
from app.services.training_plan.matcher import link_activity, score_match

logger = get_logger(__name__)
router = APIRouter()


def _serialize(w: PlannedWorkout) -> dict:
    return {
        "id": w.id,
        "plan_id": w.plan_id,
        "scheduled_date": w.scheduled_date.isoformat(),
        "day_of_week": w.day_of_week,
        "week_number": w.week_number,
        "phase": w.phase.value,
        "workout_type": w.workout_type.value,
        "target_distance_m": w.target_distance_m,
        "target_duration_s": w.target_duration_s,
        "target_pace_min_per_km": w.target_pace_min_per_km,
        "target_pace_range": w.target_pace_range,
        "target_hr_zone": w.target_hr_zone,
        "structured_steps": w.structured_steps,
        "description": w.description,
        "rationale": w.rationale,
        "status": w.status.value,
        "matched_strava_id": w.matched_strava_id,
        "match_confidence": w.match_confidence,
        "perceived_effort": w.perceived_effort,
        "user_notes": w.user_notes,
    }


@router.get("/today")
def get_today_workouts(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Return all planned workouts for today."""
    today = date.today()
    workouts = (
        db.query(PlannedWorkout)
        .filter(
            PlannedWorkout.user_id == current_user.id,
            PlannedWorkout.scheduled_date == today,
        )
        .all()
    )
    return [_serialize(w) for w in workouts]


@router.get("/week")
def get_week_workouts(
    start: date = Query(..., description="Monday of the week (YYYY-MM-DD)"),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Return all workouts for the 7-day window starting at `start`."""
    from datetime import timedelta

    end = start + timedelta(days=6)
    workouts = (
        db.query(PlannedWorkout)
        .filter(
            PlannedWorkout.user_id == current_user.id,
            PlannedWorkout.scheduled_date >= start,
            PlannedWorkout.scheduled_date <= end,
        )
        .order_by(PlannedWorkout.scheduled_date)
        .all()
    )
    return [_serialize(w) for w in workouts]


@router.get("/{workout_id}")
def get_workout(
    workout_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    return _serialize(_get_or_404(db, workout_id, current_user.id))


class UpdateWorkoutRequest(BaseModel):
    perceived_effort: Optional[int] = None
    user_notes: Optional[str] = None
    status: Optional[str] = None


@router.patch("/{workout_id}")
def update_workout(
    workout_id: int,
    body: UpdateWorkoutRequest,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Update user-provided fields on a planned workout."""
    w = _get_or_404(db, workout_id, current_user.id)
    if body.perceived_effort is not None:
        if not 1 <= body.perceived_effort <= 10:
            raise HTTPException(status_code=400, detail="perceived_effort must be 1-10")
        w.perceived_effort = body.perceived_effort
    if body.user_notes is not None:
        w.user_notes = body.user_notes
    if body.status is not None:
        allowed = {s.value for s in WorkoutStatus}
        if body.status not in allowed:
            raise HTTPException(
                status_code=400, detail=f"Invalid status: {body.status}"
            )
        w.status = WorkoutStatus(body.status)
    db.commit()
    db.refresh(w)
    return _serialize(w)


@router.post("/{workout_id}/match/{strava_id}")
def manual_match(
    workout_id: int,
    strava_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Manually link a Strava activity to a planned workout."""
    w = _get_or_404(db, workout_id, current_user.id)
    activity = (
        db.query(StravaActivity)
        .filter(
            StravaActivity.strava_id == strava_id,
            StravaActivity.user_id == current_user.id,
        )
        .first()
    )
    if activity is None:
        raise HTTPException(status_code=404, detail="Strava activity not found")

    confidence = score_match(activity, w)
    link_activity(db, activity, w, confidence)
    db.commit()
    db.refresh(w)
    return _serialize(w)


def _get_or_404(db: Session, workout_id: int, user_id: int) -> PlannedWorkout:
    w = (
        db.query(PlannedWorkout)
        .filter(PlannedWorkout.id == workout_id, PlannedWorkout.user_id == user_id)
        .first()
    )
    if w is None:
        raise HTTPException(status_code=404, detail="Planned workout not found")
    return w
