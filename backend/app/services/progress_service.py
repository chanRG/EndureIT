"""
Progress service - business logic for progress tracking.
"""
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.user import User
from app.models.workout import ProgressEntry
from app.schemas.workout import ProgressEntryCreate, ProgressEntryUpdate
from app.core.logging import get_logger

logger = get_logger(__name__)


class ProgressService:
    """Service for progress tracking operations."""

    @staticmethod
    def create_progress_entry(
        db: Session, user: User, entry_data: ProgressEntryCreate
    ) -> ProgressEntry:
        """Create a new progress entry.

        Args:
            db: Database session
            user: User creating the entry
            entry_data: Progress entry data

        Returns:
            Created progress entry
        """
        logger.info(f"Creating progress entry for user {user.id}")

        entry = ProgressEntry(user_id=user.id, **entry_data.model_dump())
        db.add(entry)
        db.commit()
        db.refresh(entry)

        logger.info(f"Created progress entry {entry.id}")
        return entry

    @staticmethod
    def get_progress_entry(
        db: Session, entry_id: int, user_id: int
    ) -> Optional[ProgressEntry]:
        """Get a progress entry by ID for a specific user.

        Args:
            db: Database session
            entry_id: Progress entry ID
            user_id: User ID

        Returns:
            Progress entry if found, None otherwise
        """
        return (
            db.query(ProgressEntry)
            .filter(ProgressEntry.id == entry_id, ProgressEntry.user_id == user_id)
            .first()
        )

    @staticmethod
    def get_progress_entries(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[ProgressEntry]:
        """Get progress entries for a user with optional filters.

        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            start_date: Filter entries after this date
            end_date: Filter entries before this date

        Returns:
            List of progress entries
        """
        query = db.query(ProgressEntry).filter(ProgressEntry.user_id == user_id)

        if start_date:
            query = query.filter(ProgressEntry.entry_date >= start_date)
        if end_date:
            query = query.filter(ProgressEntry.entry_date <= end_date)

        return (
            query.order_by(desc(ProgressEntry.entry_date))
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def update_progress_entry(
        db: Session, entry_id: int, user_id: int, entry_data: ProgressEntryUpdate
    ) -> Optional[ProgressEntry]:
        """Update a progress entry.

        Args:
            db: Database session
            entry_id: Progress entry ID
            user_id: User ID
            entry_data: Update data

        Returns:
            Updated progress entry if found, None otherwise
        """
        entry = ProgressService.get_progress_entry(db, entry_id, user_id)
        if not entry:
            return None

        # Update fields
        update_data = entry_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(entry, field, value)

        db.commit()
        db.refresh(entry)

        logger.info(f"Updated progress entry {entry_id}")
        return entry

    @staticmethod
    def delete_progress_entry(db: Session, entry_id: int, user_id: int) -> bool:
        """Delete a progress entry.

        Args:
            db: Database session
            entry_id: Progress entry ID
            user_id: User ID

        Returns:
            True if deleted, False if not found
        """
        entry = ProgressService.get_progress_entry(db, entry_id, user_id)
        if not entry:
            return False

        db.delete(entry)
        db.commit()

        logger.info(f"Deleted progress entry {entry_id}")
        return True

    @staticmethod
    def get_latest_weight(db: Session, user_id: int) -> Optional[float]:
        """Get the most recent weight entry for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Latest weight or None
        """
        entry = (
            db.query(ProgressEntry)
            .filter(
                ProgressEntry.user_id == user_id, ProgressEntry.weight_kg.isnot(None)
            )
            .order_by(desc(ProgressEntry.entry_date))
            .first()
        )

        return entry.weight_kg if entry else None

    @staticmethod
    def get_weight_change(db: Session, user_id: int, days: int = 30) -> Optional[float]:
        """Calculate weight change over a period.

        Args:
            db: Database session
            user_id: User ID
            days: Number of days to look back

        Returns:
            Weight change (positive = gained, negative = lost) or None
        """
        since_date = datetime.utcnow() - timedelta(days=days)

        # Get oldest entry in period
        oldest = (
            db.query(ProgressEntry)
            .filter(
                ProgressEntry.user_id == user_id,
                ProgressEntry.weight_kg.isnot(None),
                ProgressEntry.entry_date >= since_date,
            )
            .order_by(ProgressEntry.entry_date)
            .first()
        )

        # Get latest entry
        latest = (
            db.query(ProgressEntry)
            .filter(
                ProgressEntry.user_id == user_id, ProgressEntry.weight_kg.isnot(None)
            )
            .order_by(desc(ProgressEntry.entry_date))
            .first()
        )

        if oldest and latest and oldest.weight_kg and latest.weight_kg:
            return latest.weight_kg - oldest.weight_kg

        return None
