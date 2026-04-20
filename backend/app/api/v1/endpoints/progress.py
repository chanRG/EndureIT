"""
Progress tracking endpoints for EndureIT API.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.db.database import get_db
from app.models.user import User
from app.schemas.workout import (
    ProgressEntryCreate,
    ProgressEntryUpdate,
    ProgressEntryResponse,
)
from app.services.progress_service import ProgressService

router = APIRouter()


@router.post(
    "", response_model=ProgressEntryResponse, status_code=status.HTTP_201_CREATED
)
def create_progress_entry(
    entry: ProgressEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Create a new progress entry."""
    return ProgressService.create_progress_entry(db, current_user, entry)


@router.get("", response_model=List[ProgressEntryResponse])
def get_progress_entries(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Get all progress entries for the current user with optional filters."""
    return ProgressService.get_progress_entries(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/weight/latest")
def get_latest_weight(
    db: Session = Depends(get_db), current_user: User = Depends(deps.get_current_user)
):
    """Get the most recent weight entry."""
    weight = ProgressService.get_latest_weight(db, current_user.id)
    if weight is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No weight entries found"
        )
    return {"weight_kg": weight}


@router.get("/weight/change")
def get_weight_change(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Get weight change over a period."""
    change = ProgressService.get_weight_change(db, current_user.id, days)
    if change is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Not enough data to calculate weight change for {days} days",
        )
    return {
        "change_kg": change,
        "days": days,
        "trend": "gained" if change > 0 else "lost" if change < 0 else "stable",
    }


@router.get("/{entry_id}", response_model=ProgressEntryResponse)
def get_progress_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Get a specific progress entry by ID."""
    entry = ProgressService.get_progress_entry(db, entry_id, current_user.id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Progress entry not found"
        )
    return entry


@router.put("/{entry_id}", response_model=ProgressEntryResponse)
def update_progress_entry(
    entry_id: int,
    entry_update: ProgressEntryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Update a progress entry."""
    entry = ProgressService.update_progress_entry(
        db, entry_id, current_user.id, entry_update
    )
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Progress entry not found"
        )
    return entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_progress_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Delete a progress entry."""
    success = ProgressService.delete_progress_entry(db, entry_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Progress entry not found"
        )
    return None
