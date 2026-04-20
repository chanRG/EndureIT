"""
Dashboard service - provides aggregated data for user dashboard.
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.workout import Workout, Goal
from app.schemas.workout import UserDashboard, WorkoutListResponse
from app.services.workout_service import WorkoutService
from app.services.progress_service import ProgressService
from app.core.logging import get_logger

logger = get_logger(__name__)


class DashboardService:
    """Service for dashboard data aggregation."""

    @staticmethod
    def get_user_dashboard(db: Session, user_id: int) -> UserDashboard:
        """Get comprehensive dashboard data for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            User dashboard data
        """
        logger.info(f"Generating dashboard for user {user_id}")

        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # Total workouts
        total_workouts = (
            db.query(func.count(Workout.id))
            .filter(Workout.user_id == user_id, Workout.is_completed == True)
            .scalar()
            or 0
        )

        # Workouts this week
        workouts_this_week = (
            db.query(func.count(Workout.id))
            .filter(
                Workout.user_id == user_id,
                Workout.is_completed == True,
                Workout.start_time >= week_ago,
            )
            .scalar()
            or 0
        )

        # Workouts this month
        workouts_this_month = (
            db.query(func.count(Workout.id))
            .filter(
                Workout.user_id == user_id,
                Workout.is_completed == True,
                Workout.start_time >= month_ago,
            )
            .scalar()
            or 0
        )

        # Goals stats
        active_goals = (
            db.query(func.count(Goal.id))
            .filter(
                Goal.user_id == user_id,
                Goal.is_active == True,
                Goal.is_completed == False,
            )
            .scalar()
            or 0
        )

        completed_goals = (
            db.query(func.count(Goal.id))
            .filter(Goal.user_id == user_id, Goal.is_completed == True)
            .scalar()
            or 0
        )

        # Progress data
        latest_weight = ProgressService.get_latest_weight(db, user_id)
        weight_change_30_days = ProgressService.get_weight_change(db, user_id, days=30)

        # Recent workouts
        recent_workouts_data = WorkoutService.get_workouts(
            db=db, user_id=user_id, skip=0, limit=5
        )
        recent_workouts = [
            WorkoutListResponse.model_validate(w) for w in recent_workouts_data
        ]

        return UserDashboard(
            total_workouts=total_workouts,
            workouts_this_week=workouts_this_week,
            workouts_this_month=workouts_this_month,
            active_goals=active_goals,
            completed_goals=completed_goals,
            latest_weight=latest_weight,
            weight_change_30_days=weight_change_30_days,
            recent_workouts=recent_workouts,
        )
