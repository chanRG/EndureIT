"""
Strava activity → PlannedWorkout matching.

Rules:
- Sport: Run/VirtualRun/TrailRun → run workout types; Ride → cross only
- Date window: ±1 day
- Distance within [0.7×, 1.4×] of target (wider for intervals/tempo, narrow for long)
- Duration sanity when distance is missing

Weighted score: sport 0.4, date 0.3, distance 0.2, duration 0.1
Auto-link threshold: ≥ 0.6
"""

from __future__ import annotations

from datetime import timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.strava_activity import StravaActivity
from app.models.training_plan import PlannedWorkout, WorkoutStatus, WorkoutType
from app.models.user import User

logger = get_logger(__name__)

AUTO_LINK_THRESHOLD = 0.6

_RUN_TYPES = {"run", "virtualrun", "trailrun", "treadmill"}
_RIDE_TYPES = {"ride", "virtualride", "ebikeride"}

# Wider distance tolerance for quality sessions; narrower for long runs
_DIST_TOLERANCE: dict[WorkoutType, tuple[float, float]] = {
    WorkoutType.INTERVALS: (0.65, 1.50),
    WorkoutType.TEMPO: (0.70, 1.45),
    WorkoutType.LONG: (0.80, 1.30),
    WorkoutType.EASY: (0.70, 1.40),
    WorkoutType.RECOVERY: (0.60, 1.50),
    WorkoutType.RACE: (0.95, 1.05),
    WorkoutType.CROSS: (0.50, 2.00),
}


def _sport_score(activity: StravaActivity, workout_type: WorkoutType) -> float:
    sport = (activity.activity_type or "").lower().replace(" ", "")
    if workout_type == WorkoutType.CROSS:
        return 1.0 if sport in _RIDE_TYPES else 0.0
    if sport in _RUN_TYPES:
        return 1.0
    if sport in _RIDE_TYPES:
        return 0.0
    return 0.3  # Unknown sport — partial credit


def _date_score(activity: StravaActivity, planned: PlannedWorkout) -> float:
    delta = abs((activity.start_date.date() - planned.scheduled_date).days)
    if delta == 0:
        return 1.0
    if delta == 1:
        return 0.5
    return 0.0


def _distance_score(activity: StravaActivity, planned: PlannedWorkout) -> float:
    if not planned.target_distance_m or planned.target_distance_m <= 0:
        return 0.5  # No target — neutral
    if not activity.distance or activity.distance <= 0:
        return 0.3  # No actual distance — low score
    ratio = activity.distance / planned.target_distance_m
    lo, hi = _DIST_TOLERANCE.get(planned.workout_type, (0.70, 1.40))
    if lo <= ratio <= hi:
        # Score peaks at 1.0 when ratio == 1.0
        return 1.0 - abs(ratio - 1.0) / max(1.0 - lo, hi - 1.0)
    return 0.0


def _duration_score(activity: StravaActivity, planned: PlannedWorkout) -> float:
    if not planned.target_duration_s or planned.target_duration_s <= 0:
        return 0.5
    actual = activity.moving_time or activity.elapsed_time
    if not actual or actual <= 0:
        return 0.3
    ratio = actual / planned.target_duration_s
    if 0.70 <= ratio <= 1.40:
        return 1.0 - abs(ratio - 1.0) / 0.40
    return 0.0


def score_match(activity: StravaActivity, planned: PlannedWorkout) -> float:
    """Return a weighted match score in [0.0, 1.0]."""
    return (
        0.4 * _sport_score(activity, planned.workout_type)
        + 0.3 * _date_score(activity, planned)
        + 0.2 * _distance_score(activity, planned)
        + 0.1 * _duration_score(activity, planned)
    )


def find_best_match(
    db: Session,
    activity: StravaActivity,
) -> Optional[tuple[PlannedWorkout, float]]:
    """
    Find the best-matching PlannedWorkout for a Strava activity.
    Returns (workout, score) if score >= AUTO_LINK_THRESHOLD, else None.
    """
    activity_date = activity.start_date.date()
    window_start = activity_date - timedelta(days=1)
    window_end = activity_date + timedelta(days=1)

    candidates = (
        db.query(PlannedWorkout)
        .filter(
            PlannedWorkout.user_id == activity.user_id,
            PlannedWorkout.status == WorkoutStatus.PLANNED,
            PlannedWorkout.scheduled_date >= window_start,
            PlannedWorkout.scheduled_date <= window_end,
            PlannedWorkout.matched_strava_id.is_(None),
        )
        .all()
    )

    if not candidates:
        return None

    scored = [(w, score_match(activity, w)) for w in candidates]
    best_workout, best_score = max(scored, key=lambda x: x[1])

    if best_score < AUTO_LINK_THRESHOLD:
        logger.debug(
            "No confident match for activity %d (best score %.2f)",
            activity.strava_id,
            best_score,
        )
        return None

    return best_workout, best_score


def link_activity(
    db: Session,
    activity: StravaActivity,
    planned: PlannedWorkout,
    confidence: float,
) -> None:
    """Mark a PlannedWorkout as completed and record the matched Strava activity."""
    planned.status = WorkoutStatus.COMPLETED
    planned.matched_strava_id = activity.strava_id
    planned.match_confidence = confidence
    db.flush()
    logger.info(
        "Matched activity %d → planned workout %d (confidence %.2f)",
        activity.strava_id,
        planned.id,
        confidence,
    )


def run_matcher(db: Session, user: User, activity: StravaActivity) -> bool:
    """
    Top-level entry point called from the arq worker.
    Returns True if a match was made.
    """
    result = find_best_match(db, activity)
    if result is None:
        return False
    planned, confidence = result
    link_activity(db, activity, planned, confidence)
    return True
