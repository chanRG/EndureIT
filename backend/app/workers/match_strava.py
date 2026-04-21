"""
Matches a newly synced Strava activity to a PlannedWorkout.
Enqueued by StravaSyncService after a new activity is saved.
"""

from app.core.logging import get_logger
from app.db.database import SessionLocal
from app.models.strava_activity import StravaActivity
from app.models.user import User
from app.services.training_plan.matcher import run_matcher

logger = get_logger(__name__)


async def match_planned_workout(
    ctx: dict, strava_activity_id: int, user_id: int
) -> dict:
    db = SessionLocal()
    try:
        activity = (
            db.query(StravaActivity)
            .filter(StravaActivity.strava_id == strava_activity_id)
            .first()
        )
        if activity is None:
            logger.warning("Activity %d not found", strava_activity_id)
            return {"status": "activity_not_found"}

        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            logger.warning("User %d not found", user_id)
            return {"status": "user_not_found"}

        matched = run_matcher(db, user, activity)
        if matched:
            db.commit()
            return {"status": "matched"}
        return {"status": "no_match"}
    except Exception as exc:
        db.rollback()
        logger.exception("match_planned_workout failed: %s", exc)
        raise
    finally:
        db.close()
