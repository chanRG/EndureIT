"""
Strava Activity model for caching Strava data.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional, List
from datetime import datetime

from sqlalchemy import Text, JSON, BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class StravaActivity(Base):
    """Cached Strava activity data."""
    
    __tablename__ = "strava_activities"
    
    # Strava activity ID (not our internal ID)
    strava_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    
    # User who owns this activity
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Activity data
    name: Mapped[str] = mapped_column(nullable=False)
    activity_type: Mapped[str] = mapped_column(nullable=False)
    start_date: Mapped[datetime] = mapped_column(nullable=False)
    start_date_local: Mapped[datetime] = mapped_column(nullable=False)
    
    # Metrics
    distance: Mapped[float] = mapped_column(nullable=False)  # meters
    moving_time: Mapped[int] = mapped_column(nullable=False)  # seconds
    elapsed_time: Mapped[int] = mapped_column(nullable=False)  # seconds
    total_elevation_gain: Mapped[float] = mapped_column(default=0.0)
    
    # Heart rate data
    average_heartrate: Mapped[Optional[float]] = mapped_column(nullable=True)
    max_heartrate: Mapped[Optional[float]] = mapped_column(nullable=True)
    has_heartrate: Mapped[bool] = mapped_column(default=False)
    
    # Speed data
    average_speed: Mapped[Optional[float]] = mapped_column(nullable=True)
    max_speed: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # Other metrics
    calories: Mapped[Optional[float]] = mapped_column(nullable=True)
    achievement_count: Mapped[int] = mapped_column(default=0)
    kudos_count: Mapped[int] = mapped_column(default=0)
    
    # Best efforts (stored as JSON)
    best_efforts: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Map data (polyline for route visualization)
    map_polyline: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Location data
    start_latlng: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    end_latlng: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Cached streams
    time_stream: Mapped[Optional[List[float]]] = mapped_column(JSON, nullable=True)
    heartrate_stream: Mapped[Optional[List[float]]] = mapped_column(JSON, nullable=True)
    velocity_stream: Mapped[Optional[List[float]]] = mapped_column(JSON, nullable=True)
    distance_stream: Mapped[Optional[List[float]]] = mapped_column(JSON, nullable=True)
    
    # Full activity data (for future use)
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    last_synced: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="strava_activities")

