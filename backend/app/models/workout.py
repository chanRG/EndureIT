"""
Database models for workouts and fitness tracking.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, Integer, Float, DateTime, Text, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.db.base import Base


class WorkoutType(str, enum.Enum):
    """Workout type enumeration."""
    RUNNING = "running"
    CYCLING = "cycling"
    SWIMMING = "swimming"
    WALKING = "walking"
    HIKING = "hiking"
    GYM = "gym"
    YOGA = "yoga"
    CROSSFIT = "crossfit"
    OTHER = "other"


class IntensityLevel(str, enum.Enum):
    """Workout intensity levels."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class Workout(Base):
    """Workout model - tracks individual workout sessions."""
    
    __tablename__ = "workouts"
    
    # Basic Information
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    workout_type: Mapped[WorkoutType] = mapped_column(
        Enum(WorkoutType, native_enum=False),
        nullable=False,
        index=True
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timing
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Distance & Location
    distance_meters: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Performance Metrics
    calories_burned: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    average_heart_rate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_heart_rate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    average_pace: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # min/km
    elevation_gain: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # meters
    
    # Intensity & Effort
    intensity: Mapped[Optional[IntensityLevel]] = mapped_column(
        Enum(IntensityLevel, native_enum=False),
        nullable=True
    )
    perceived_exertion: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-10 scale
    
    # Notes & Status
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="workouts")
    exercises: Mapped[list["Exercise"]] = relationship(
        "Exercise",
        back_populates="workout",
        cascade="all, delete-orphan"
    )


class Exercise(Base):
    """Exercise model - individual exercises within a workout."""
    
    __tablename__ = "exercises"
    
    workout_id: Mapped[int] = mapped_column(ForeignKey("workouts.id"), nullable=False, index=True)
    
    # Exercise Details
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    exercise_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Sets & Reps
    sets: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Time-based
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    distance_meters: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Order in workout
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    workout: Mapped["Workout"] = relationship("Workout", back_populates="exercises")


class Goal(Base):
    """Goal model - fitness goals and targets."""
    
    __tablename__ = "goals"
    
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    
    # Goal Information
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    goal_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Target Metrics
    target_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Timing
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    target_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="goals")


class ProgressEntry(Base):
    """Progress tracking - measurements and body composition."""
    
    __tablename__ = "progress_entries"
    
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    
    # Date of measurement
    entry_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    
    # Body Measurements
    weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    body_fat_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    muscle_mass_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Additional Measurements
    chest_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    waist_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hips_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    biceps_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    thighs_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Performance Metrics
    resting_heart_rate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Photos (store file paths or URLs)
    photo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="progress_entries")

