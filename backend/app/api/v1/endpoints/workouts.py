"""
Workout endpoints for EndureIT API.
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.db.database import get_db
from app.models.user import User
from app.models.workout import WorkoutType
from app.schemas.workout import (
    WorkoutCreate,
    WorkoutUpdate,
    WorkoutResponse,
    WorkoutListResponse,
    WorkoutStats,
    ExerciseCreate,
    ExerciseResponse
)
from app.services.workout_service import WorkoutService

router = APIRouter()


@router.post("", response_model=WorkoutResponse, status_code=status.HTTP_201_CREATED)
def create_workout(
    workout: WorkoutCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Create a new workout with optional exercises."""
    return WorkoutService.create_workout(db, current_user, workout)


@router.get("", response_model=List[WorkoutListResponse])
def get_workouts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    workout_type: Optional[WorkoutType] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Get all workouts for the current user with optional filters."""
    workouts = WorkoutService.get_workouts(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        workout_type=workout_type,
        start_date=start_date,
        end_date=end_date
    )
    return [WorkoutListResponse.model_validate(w) for w in workouts]


@router.get("/stats", response_model=WorkoutStats)
def get_workout_stats(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Get workout statistics for the current user."""
    return WorkoutService.get_workout_stats(db, current_user.id, days)


@router.get("/{workout_id}", response_model=WorkoutResponse)
def get_workout(
    workout_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Get a specific workout by ID."""
    workout = WorkoutService.get_workout(db, workout_id, current_user.id)
    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found"
        )
    return workout


@router.put("/{workout_id}", response_model=WorkoutResponse)
def update_workout(
    workout_id: int,
    workout_update: WorkoutUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Update a workout."""
    workout = WorkoutService.update_workout(db, workout_id, current_user.id, workout_update)
    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found"
        )
    return workout


@router.delete("/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workout(
    workout_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Delete a workout."""
    success = WorkoutService.delete_workout(db, workout_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found"
        )
    return None


@router.post("/{workout_id}/exercises", response_model=ExerciseResponse, status_code=status.HTTP_201_CREATED)
def add_exercise_to_workout(
    workout_id: int,
    exercise: ExerciseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Add an exercise to an existing workout."""
    exercise_obj = WorkoutService.add_exercise_to_workout(
        db, workout_id, current_user.id, exercise
    )
    if not exercise_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found"
        )
    return exercise_obj

