"""
User model for authentication and user management.
"""
from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.workout import Workout, Goal, ProgressEntry
    from app.models.strava_activity import StravaActivity


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
        "Workout",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    goals: Mapped[list["Goal"]] = relationship(
        "Goal",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    progress_entries: Mapped[list["ProgressEntry"]] = relationship(
        "ProgressEntry",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    strava_activities: Mapped[list["StravaActivity"]] = relationship(
        "StravaActivity",
        back_populates="user",
        cascade="all, delete-orphan"
    )