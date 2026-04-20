"""
Pydantic schemas for workout-related models.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from app.models.workout import WorkoutType, IntensityLevel


# Exercise Schemas
class ExerciseBase(BaseModel):
    """Base exercise schema."""

    name: str = Field(..., min_length=1, max_length=200)
    exercise_type: Optional[str] = Field(None, max_length=100)
    sets: Optional[int] = Field(None, ge=0)
    reps: Optional[int] = Field(None, ge=0)
    weight_kg: Optional[float] = Field(None, ge=0)
    duration_seconds: Optional[int] = Field(None, ge=0)
    distance_meters: Optional[float] = Field(None, ge=0)
    order_index: int = Field(default=0, ge=0)
    notes: Optional[str] = None


class ExerciseCreate(ExerciseBase):
    """Schema for creating an exercise."""

    pass


class ExerciseUpdate(BaseModel):
    """Schema for updating an exercise."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    exercise_type: Optional[str] = Field(None, max_length=100)
    sets: Optional[int] = Field(None, ge=0)
    reps: Optional[int] = Field(None, ge=0)
    weight_kg: Optional[float] = Field(None, ge=0)
    duration_seconds: Optional[int] = Field(None, ge=0)
    distance_meters: Optional[float] = Field(None, ge=0)
    order_index: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None


class ExerciseResponse(ExerciseBase):
    """Schema for exercise response."""

    id: int
    workout_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Workout Schemas
class WorkoutBase(BaseModel):
    """Base workout schema."""

    title: str = Field(..., min_length=1, max_length=200)
    workout_type: WorkoutType
    description: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = Field(None, ge=0)
    distance_meters: Optional[float] = Field(None, ge=0)
    location: Optional[str] = Field(None, max_length=200)
    calories_burned: Optional[int] = Field(None, ge=0)
    average_heart_rate: Optional[int] = Field(None, ge=0, le=300)
    max_heart_rate: Optional[int] = Field(None, ge=0, le=300)
    average_pace: Optional[float] = Field(None, ge=0)
    elevation_gain: Optional[float] = None
    intensity: Optional[IntensityLevel] = None
    perceived_exertion: Optional[int] = Field(None, ge=1, le=10)
    notes: Optional[str] = None
    is_completed: bool = True


class WorkoutCreate(WorkoutBase):
    """Schema for creating a workout."""

    exercises: Optional[List[ExerciseCreate]] = []


class WorkoutUpdate(BaseModel):
    """Schema for updating a workout."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    workout_type: Optional[WorkoutType] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = Field(None, ge=0)
    distance_meters: Optional[float] = Field(None, ge=0)
    location: Optional[str] = Field(None, max_length=200)
    calories_burned: Optional[int] = Field(None, ge=0)
    average_heart_rate: Optional[int] = Field(None, ge=0, le=300)
    max_heart_rate: Optional[int] = Field(None, ge=0, le=300)
    average_pace: Optional[float] = Field(None, ge=0)
    elevation_gain: Optional[float] = None
    intensity: Optional[IntensityLevel] = None
    perceived_exertion: Optional[int] = Field(None, ge=1, le=10)
    notes: Optional[str] = None
    is_completed: Optional[bool] = None


class WorkoutResponse(WorkoutBase):
    """Schema for workout response."""

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    exercises: List[ExerciseResponse] = []

    model_config = ConfigDict(from_attributes=True)


class WorkoutListResponse(BaseModel):
    """Schema for workout list response (without exercises)."""

    id: int
    user_id: int
    title: str
    workout_type: WorkoutType
    start_time: datetime
    duration_seconds: Optional[int]
    distance_meters: Optional[float]
    calories_burned: Optional[int]
    is_completed: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Goal Schemas
class GoalBase(BaseModel):
    """Base goal schema."""

    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    goal_type: str = Field(..., min_length=1, max_length=100)
    target_value: Optional[float] = Field(None, ge=0)
    current_value: Optional[float] = Field(None, ge=0)
    unit: Optional[str] = Field(None, max_length=50)
    start_date: datetime
    target_date: Optional[datetime] = None
    is_active: bool = True


class GoalCreate(GoalBase):
    """Schema for creating a goal."""

    pass


class GoalUpdate(BaseModel):
    """Schema for updating a goal."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    goal_type: Optional[str] = Field(None, min_length=1, max_length=100)
    target_value: Optional[float] = Field(None, ge=0)
    current_value: Optional[float] = Field(None, ge=0)
    unit: Optional[str] = Field(None, max_length=50)
    target_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    is_completed: Optional[bool] = None


class GoalResponse(GoalBase):
    """Schema for goal response."""

    id: int
    user_id: int
    completed_date: Optional[datetime]
    is_completed: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Progress Entry Schemas
class ProgressEntryBase(BaseModel):
    """Base progress entry schema."""

    entry_date: datetime
    weight_kg: Optional[float] = Field(None, ge=0)
    body_fat_percentage: Optional[float] = Field(None, ge=0, le=100)
    muscle_mass_kg: Optional[float] = Field(None, ge=0)
    chest_cm: Optional[float] = Field(None, ge=0)
    waist_cm: Optional[float] = Field(None, ge=0)
    hips_cm: Optional[float] = Field(None, ge=0)
    biceps_cm: Optional[float] = Field(None, ge=0)
    thighs_cm: Optional[float] = Field(None, ge=0)
    resting_heart_rate: Optional[int] = Field(None, ge=0, le=200)
    notes: Optional[str] = None
    photo_url: Optional[str] = Field(None, max_length=500)


class ProgressEntryCreate(ProgressEntryBase):
    """Schema for creating a progress entry."""

    pass


class ProgressEntryUpdate(BaseModel):
    """Schema for updating a progress entry."""

    entry_date: Optional[datetime] = None
    weight_kg: Optional[float] = Field(None, ge=0)
    body_fat_percentage: Optional[float] = Field(None, ge=0, le=100)
    muscle_mass_kg: Optional[float] = Field(None, ge=0)
    chest_cm: Optional[float] = Field(None, ge=0)
    waist_cm: Optional[float] = Field(None, ge=0)
    hips_cm: Optional[float] = Field(None, ge=0)
    biceps_cm: Optional[float] = Field(None, ge=0)
    thighs_cm: Optional[float] = Field(None, ge=0)
    resting_heart_rate: Optional[int] = Field(None, ge=0, le=200)
    notes: Optional[str] = None
    photo_url: Optional[str] = Field(None, max_length=500)


class ProgressEntryResponse(ProgressEntryBase):
    """Schema for progress entry response."""

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Statistics Schemas
class WorkoutStats(BaseModel):
    """Workout statistics schema."""

    total_workouts: int
    total_duration_minutes: float
    total_distance_km: float
    total_calories: int
    average_duration_minutes: float
    workouts_by_type: dict[str, int]
    most_common_workout_type: Optional[str]


class UserDashboard(BaseModel):
    """User dashboard summary schema."""

    total_workouts: int
    workouts_this_week: int
    workouts_this_month: int
    active_goals: int
    completed_goals: int
    latest_weight: Optional[float]
    weight_change_30_days: Optional[float]
    recent_workouts: List[WorkoutListResponse]
