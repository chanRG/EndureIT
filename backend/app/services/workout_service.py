"""
Workout service - business logic for workout operations.
"""
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc

from app.models.user import User
from app.models.workout import Workout, Exercise, WorkoutType
from app.schemas.workout import (
    WorkoutCreate,
    WorkoutUpdate,
    ExerciseCreate,
    WorkoutStats,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class WorkoutService:
    """Service for workout-related operations."""

    @staticmethod
    def create_workout(db: Session, user: User, workout_data: WorkoutCreate) -> Workout:
        """Create a new workout with exercises.

        Args:
            db: Database session
            user: User creating the workout
            workout_data: Workout creation data

        Returns:
            Created workout
        """
        logger.info(f"Creating workout for user {user.id}: {workout_data.title}")

        # Create workout
        workout = Workout(
            user_id=user.id, **workout_data.model_dump(exclude={"exercises"})
        )
        db.add(workout)
        db.flush()  # Get workout ID

        # Add exercises if provided
        if workout_data.exercises:
            for exercise_data in workout_data.exercises:
                exercise = Exercise(workout_id=workout.id, **exercise_data.model_dump())
                db.add(exercise)

        db.commit()
        db.refresh(workout)

        logger.info(
            f"Created workout {workout.id} with {len(workout_data.exercises)} exercises"
        )
        return workout

    @staticmethod
    def get_workout(db: Session, workout_id: int, user_id: int) -> Optional[Workout]:
        """Get a workout by ID for a specific user.

        Args:
            db: Database session
            workout_id: Workout ID
            user_id: User ID

        Returns:
            Workout if found, None otherwise
        """
        return (
            db.query(Workout)
            .options(joinedload(Workout.exercises))
            .filter(Workout.id == workout_id, Workout.user_id == user_id)
            .first()
        )

    @staticmethod
    def get_workouts(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        workout_type: Optional[WorkoutType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Workout]:
        """Get workouts for a user with optional filters.

        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            workout_type: Filter by workout type
            start_date: Filter workouts after this date
            end_date: Filter workouts before this date

        Returns:
            List of workouts
        """
        query = db.query(Workout).filter(Workout.user_id == user_id)

        if workout_type:
            query = query.filter(Workout.workout_type == workout_type)
        if start_date:
            query = query.filter(Workout.start_time >= start_date)
        if end_date:
            query = query.filter(Workout.start_time <= end_date)

        return query.order_by(desc(Workout.start_time)).offset(skip).limit(limit).all()

    @staticmethod
    def update_workout(
        db: Session, workout_id: int, user_id: int, workout_data: WorkoutUpdate
    ) -> Optional[Workout]:
        """Update a workout.

        Args:
            db: Database session
            workout_id: Workout ID
            user_id: User ID
            workout_data: Update data

        Returns:
            Updated workout if found, None otherwise
        """
        workout = WorkoutService.get_workout(db, workout_id, user_id)
        if not workout:
            return None

        # Update fields
        update_data = workout_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(workout, field, value)

        db.commit()
        db.refresh(workout)

        logger.info(f"Updated workout {workout_id}")
        return workout

    @staticmethod
    def delete_workout(db: Session, workout_id: int, user_id: int) -> bool:
        """Delete a workout.

        Args:
            db: Database session
            workout_id: Workout ID
            user_id: User ID

        Returns:
            True if deleted, False if not found
        """
        workout = WorkoutService.get_workout(db, workout_id, user_id)
        if not workout:
            return False

        db.delete(workout)
        db.commit()

        logger.info(f"Deleted workout {workout_id}")
        return True

    @staticmethod
    def get_workout_stats(db: Session, user_id: int, days: int = 30) -> WorkoutStats:
        """Get workout statistics for a user.

        Args:
            db: Database session
            user_id: User ID
            days: Number of days to analyze

        Returns:
            Workout statistics
        """
        since_date = datetime.utcnow() - timedelta(days=days)

        workouts = (
            db.query(Workout)
            .filter(
                Workout.user_id == user_id,
                Workout.start_time >= since_date,
                Workout.is_completed == True,
            )
            .all()
        )

        total_workouts = len(workouts)
        total_duration = sum(w.duration_seconds or 0 for w in workouts)
        total_distance = sum(w.distance_meters or 0 for w in workouts)
        total_calories = sum(w.calories_burned or 0 for w in workouts)

        # Count workouts by type
        workouts_by_type = {}
        for workout in workouts:
            workout_type = workout.workout_type.value
            workouts_by_type[workout_type] = workouts_by_type.get(workout_type, 0) + 1

        most_common = (
            max(workouts_by_type.items(), key=lambda x: x[1])[0]
            if workouts_by_type
            else None
        )

        return WorkoutStats(
            total_workouts=total_workouts,
            total_duration_minutes=total_duration / 60 if total_duration else 0,
            total_distance_km=total_distance / 1000 if total_distance else 0,
            total_calories=total_calories,
            average_duration_minutes=(total_duration / 60 / total_workouts)
            if total_workouts
            else 0,
            workouts_by_type=workouts_by_type,
            most_common_workout_type=most_common,
        )

    @staticmethod
    def add_exercise_to_workout(
        db: Session, workout_id: int, user_id: int, exercise_data: ExerciseCreate
    ) -> Optional[Exercise]:
        """Add an exercise to an existing workout.

        Args:
            db: Database session
            workout_id: Workout ID
            user_id: User ID
            exercise_data: Exercise data

        Returns:
            Created exercise if workout found, None otherwise
        """
        workout = WorkoutService.get_workout(db, workout_id, user_id)
        if not workout:
            return None

        exercise = Exercise(workout_id=workout_id, **exercise_data.model_dump())
        db.add(exercise)
        db.commit()
        db.refresh(exercise)

        logger.info(f"Added exercise to workout {workout_id}")
        return exercise
