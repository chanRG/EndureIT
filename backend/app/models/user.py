"""
User model for authentication and user management.
"""

from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.workout import Workout, Goal, ProgressEntry
    from app.models.strava_activity import StravaActivity
    from app.models.training_plan import TrainingPlan, PlannedWorkout, TrainingPace
    from app.models.nutrition import NutritionPlan, PushSubscription


class User(Base):
    """User model."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(nullable=True)
    hashed_password: Mapped[str] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Strava Integration
    strava_access_token: Mapped[Optional[str]] = mapped_column(nullable=True)
    strava_refresh_token: Mapped[Optional[str]] = mapped_column(nullable=True)
    strava_athlete_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    strava_token_expires_at: Mapped[Optional[int]] = mapped_column(nullable=True)

    # Relationships
    workouts: Mapped[list["Workout"]] = relationship(
        "Workout", back_populates="user", cascade="all, delete-orphan"
    )
    goals: Mapped[list["Goal"]] = relationship(
        "Goal", back_populates="user", cascade="all, delete-orphan"
    )
    progress_entries: Mapped[list["ProgressEntry"]] = relationship(
        "ProgressEntry", back_populates="user", cascade="all, delete-orphan"
    )
    strava_activities: Mapped[list["StravaActivity"]] = relationship(
        "StravaActivity", back_populates="user", cascade="all, delete-orphan"
    )
    training_plans: Mapped[list["TrainingPlan"]] = relationship(
        "TrainingPlan", back_populates="user", cascade="all, delete-orphan"
    )
    planned_workouts: Mapped[list["PlannedWorkout"]] = relationship(
        "PlannedWorkout", back_populates="user", cascade="all, delete-orphan"
    )
    training_paces: Mapped[Optional["TrainingPace"]] = relationship(
        "TrainingPace",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    nutrition_plans: Mapped[list["NutritionPlan"]] = relationship(
        "NutritionPlan", back_populates="user", cascade="all, delete-orphan"
    )
    push_subscriptions: Mapped[list["PushSubscription"]] = relationship(
        "PushSubscription", back_populates="user", cascade="all, delete-orphan"
    )
