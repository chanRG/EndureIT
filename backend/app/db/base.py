"""
Base model with common fields and utilities.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr

# Import all models here to ensure they're registered
def import_models():
    """Import all models to ensure they're registered with SQLAlchemy."""
    from app.models.user import User
    from app.models.workout import Workout, Exercise, Goal, ProgressEntry
    from app.models.strava_activity import StravaActivity


class Base(DeclarativeBase):
    """Base model with common fields."""
    
    # Generate __tablename__ automatically
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    # Common fields for all models
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, 
        default=func.now(), 
        onupdate=func.now(), 
        nullable=True
    )