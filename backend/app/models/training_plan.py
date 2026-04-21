"""
Training plan models: TrainingPlan, PlannedWorkout, TrainingPace.
"""

from __future__ import annotations

import enum
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.strava_activity import StravaActivity


class FitnessLevel(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class PlanStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class PlanPhase(str, enum.Enum):
    BASE = "base"
    BUILD = "build"
    PEAK = "peak"
    TAPER = "taper"


class WorkoutType(str, enum.Enum):
    EASY = "easy"
    LONG = "long"
    TEMPO = "tempo"
    INTERVALS = "intervals"
    RECOVERY = "recovery"
    RACE = "race"
    REST = "rest"
    CROSS = "cross"


class WorkoutStatus(str, enum.Enum):
    PLANNED = "planned"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    MISSED = "missed"
    MODIFIED = "modified"


class TrainingPlan(Base):
    """A periodized running plan targeting a specific race goal."""

    __tablename__ = "training_plans"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    goal_distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    race_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    race_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    days_per_week: Mapped[int] = mapped_column(Integer, nullable=False)
    current_fitness_level: Mapped[FitnessLevel] = mapped_column(
        Enum(FitnessLevel, native_enum=False), nullable=False
    )
    template_key: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[PlanStatus] = mapped_column(
        Enum(PlanStatus, native_enum=False),
        nullable=False,
        default=PlanStatus.DRAFT,
        index=True,
    )
    total_weeks: Mapped[int] = mapped_column(Integer, nullable=False)
    current_phase: Mapped[Optional[PlanPhase]] = mapped_column(
        Enum(PlanPhase, native_enum=False), nullable=True
    )
    vdot: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_hr: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    threshold_hr: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_ai_review_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    ai_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="training_plans")
    planned_workouts: Mapped[list["PlannedWorkout"]] = relationship(
        "PlannedWorkout", back_populates="plan", cascade="all, delete-orphan"
    )

    __table_args__ = (
        # Only one active plan per user
        Index(
            "ix_training_plans_user_active",
            "user_id",
            "status",
            unique=True,
            postgresql_where="status = 'active'",
        ),
    )


class PlannedWorkout(Base):
    """A single prescribed workout within a training plan."""

    __tablename__ = "planned_workouts"

    plan_id: Mapped[int] = mapped_column(
        ForeignKey("training_plans.id"), nullable=False, index=True
    )
    # Denormalised for fast "today" queries without joining through the plan
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Mon
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    phase: Mapped[PlanPhase] = mapped_column(
        Enum(PlanPhase, native_enum=False), nullable=False
    )
    workout_type: Mapped[WorkoutType] = mapped_column(
        Enum(WorkoutType, native_enum=False), nullable=False
    )
    target_distance_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    target_duration_s: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    target_pace_min_per_km: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    target_pace_range: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    target_hr_zone: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    structured_steps: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[WorkoutStatus] = mapped_column(
        Enum(WorkoutStatus, native_enum=False),
        nullable=False,
        default=WorkoutStatus.PLANNED,
        index=True,
    )
    matched_strava_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("strava_activities.strava_id"), nullable=True, index=True
    )
    match_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    perceived_effort: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    user_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    plan: Mapped["TrainingPlan"] = relationship(
        "TrainingPlan", back_populates="planned_workouts"
    )
    user: Mapped["User"] = relationship("User", back_populates="planned_workouts")
    strava_activity: Mapped[Optional["StravaActivity"]] = relationship(
        "StravaActivity",
        foreign_keys=[matched_strava_id],
        primaryjoin="PlannedWorkout.matched_strava_id == StravaActivity.strava_id",
    )

    __table_args__ = (
        Index("ix_planned_workouts_user_date", "user_id", "scheduled_date"),
    )


class TrainingPace(Base):
    """Jack Daniels training paces derived from the user's Strava PRs."""

    __tablename__ = "training_paces"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, unique=True, index=True
    )
    vdot: Mapped[float] = mapped_column(Float, nullable=False)
    # All paces in min/km
    easy_pace: Mapped[float] = mapped_column(Float, nullable=False)
    marathon_pace: Mapped[float] = mapped_column(Float, nullable=False)
    threshold_pace: Mapped[float] = mapped_column(Float, nullable=False)
    interval_pace: Mapped[float] = mapped_column(Float, nullable=False)
    repetition_pace: Mapped[float] = mapped_column(Float, nullable=False)
    max_hr: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    threshold_hr: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    resting_hr: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_activity_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="training_paces")
