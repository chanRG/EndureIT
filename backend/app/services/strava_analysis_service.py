"""Services for advanced Strava analytics (e.g., heart rate zones)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.strava_activity import StravaActivity
from app.models.user import User
from app.services.strava_service import (
    StravaService,
    StravaAPIError,
    create_strava_service,
)

logger = get_logger(__name__)


@dataclass
class HeartRateZone:
    name: str
    min_pct: float
    max_pct: float

    def bpm_range(self, max_hr: float) -> Tuple[int, int]:
        lower = int(round(max_hr * self.min_pct))
        upper = int(round(max_hr * self.max_pct))
        return lower, upper


DEFAULT_ZONES: List[HeartRateZone] = [
    HeartRateZone("Zone 1", 0.50, 0.60),
    HeartRateZone("Zone 2", 0.60, 0.70),
    HeartRateZone("Zone 3", 0.70, 0.80),
    HeartRateZone("Zone 4", 0.80, 0.90),
    HeartRateZone("Zone 5", 0.90, 1.00),
]


class StravaHeartRateAnalysisService:
    """Performs heart rate zone analysis using cached Strava activity data."""

    def __init__(
        self, db: Session, user: User, zones: Optional[List[HeartRateZone]] = None
    ):
        self.db = db
        self.user = user
        self.zones = zones or DEFAULT_ZONES
        self.strava_service: Optional[StravaService] = None

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def get_last_month_zone_analysis(
        self, max_hr_override: Optional[int] = None
    ) -> Dict[str, Any]:
        """Return heart rate zone analysis for the last 30 days of running activities."""
        end_dt = datetime.utcnow()
        start_dt = end_dt - timedelta(days=30)

        activities = self._get_recent_running_activities(start_dt)
        if not activities:
            return {
                "analysis_window": self._format_window(start_dt, end_dt),
                "activity_count": 0,
                "zones": [],
                "notes": [
                    "No running activities with heart rate data in the last 30 days."
                ],
            }

        updated = self._ensure_streams_cached(activities)
        if updated:
            try:
                self.db.commit()
            except Exception as exc:
                self.db.rollback()
                logger.exception("Failed to persist stream data: %s", exc)

        hr_max_computed = self._determine_max_hr(activities)
        hr_max = max_hr_override or hr_max_computed
        if hr_max is None:
            return {
                "analysis_window": self._format_window(start_dt, end_dt),
                "activity_count": len(activities),
                "zones": [],
                "notes": ["Could not determine heart rate maximum for analysis."],
            }

        zone_stats = self._aggregate_zone_stats(activities, hr_max)
        total_time = sum(z["time_seconds"] for z in zone_stats)
        total_distance = sum(z["distance_m"] for z in zone_stats)

        for zone in zone_stats:
            zone["time_formatted"] = self._format_seconds(zone["time_seconds"])
            zone["percent_time"] = (
                round((zone["time_seconds"] / total_time) * 100, 1)
                if total_time
                else 0.0
            )
            zone["distance_km"] = round(zone["distance_m"] / 1000, 2)
            zone["average_pace"] = self._format_pace(
                zone["time_seconds"], zone["distance_m"]
            )
            # Remove internal field
            zone.pop("distance_m", None)

        notes = [
            (
                "Heart rate zones derived using max HR observed in the period."
                if max_hr_override is None
                else "Heart rate zones calculated using manual max HR override."
            ),
            "Average pace calculated from velocity stream data (m/s).",
        ]

        return {
            "analysis_window": self._format_window(start_dt, end_dt),
            "activity_count": len(activities),
            "total_time_seconds": total_time,
            "total_time_formatted": self._format_seconds(total_time),
            "total_distance_km": round(total_distance / 1000, 2),
            "hr_max": hr_max,
            "hr_max_computed": hr_max_computed,
            "hr_max_override": max_hr_override,
            "zones": zone_stats,
            "notes": notes,
        }

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------
    def _get_recent_running_activities(
        self, start_dt: datetime
    ) -> List[StravaActivity]:
        return (
            self.db.query(StravaActivity)
            .filter(
                StravaActivity.user_id == self.user.id,
                StravaActivity.activity_type.ilike("%run%"),
                StravaActivity.has_heartrate.is_(True),
                StravaActivity.start_date >= start_dt,
            )
            .order_by(StravaActivity.start_date.desc())
            .all()
        )

    def _ensure_streams_cached(self, activities: List[StravaActivity]) -> bool:
        """Fetch and cache streams for activities missing them. Returns True if any records were updated."""
        updated = False
        for activity in activities:
            if (
                activity.heartrate_stream
                and activity.time_stream
                and activity.velocity_stream
            ):
                continue

            try:
                logger.info("Fetching streams for activity %s", activity.strava_id)
                streams = self._get_strava_service().get_activity_streams(
                    activity.strava_id,
                    keys=["time", "heartrate", "velocity_smooth", "distance"],
                )
            except StravaAPIError as exc:
                logger.warning(
                    "Unable to fetch streams for activity %s: %s",
                    activity.strava_id,
                    exc,
                )
                continue

            # Strava returns a dict keyed by stream name when key_by_type=true
            time_data = self._extract_stream(streams, "time")
            hr_data = self._extract_stream(streams, "heartrate")
            velocity_data = self._extract_stream(streams, "velocity_smooth")
            distance_data = self._extract_stream(streams, "distance")

            if not time_data or not hr_data:
                logger.warning(
                    "Missing core streams for activity %s", activity.strava_id
                )
                continue

            min_length = min(
                len(time_data),
                len(hr_data),
                len(velocity_data) if velocity_data else len(time_data),
            )
            if min_length < 2:
                logger.warning(
                    "Insufficient stream data for activity %s", activity.strava_id
                )
                continue

            activity.time_stream = time_data
            activity.heartrate_stream = hr_data
            activity.velocity_stream = (
                velocity_data[:min_length] if velocity_data else None
            )
            activity.distance_stream = (
                distance_data[:min_length] if distance_data else None
            )
            activity.last_synced = datetime.utcnow()
            updated = True

        return updated

    def _determine_max_hr(self, activities: List[StravaActivity]) -> Optional[int]:
        max_values: List[float] = []
        for activity in activities:
            if activity.max_heartrate:
                max_values.append(activity.max_heartrate)
            if activity.heartrate_stream:
                max_values.append(max(activity.heartrate_stream))

        if not max_values:
            return None

        return int(round(max(max_values)))

    def _aggregate_zone_stats(
        self, activities: List[StravaActivity], max_hr: int
    ) -> List[Dict[str, Any]]:
        zone_stats = [
            {
                "zone": idx + 1,
                "label": zone.name,
                "hr_range": zone.bpm_range(max_hr),
                "time_seconds": 0.0,
                "distance_m": 0.0,
            }
            for idx, zone in enumerate(self.zones)
        ]

        def assign_zone(hr: float) -> Optional[int]:
            if hr <= 0:
                return None
            for idx, zone in enumerate(self.zones):
                lower, upper = zone.bpm_range(max_hr)
                upper = upper if idx < len(self.zones) - 1 else max_hr
                if lower <= hr <= upper:
                    return idx
            if hr > max_hr * self.zones[-1].min_pct:
                return len(self.zones) - 1
            return None

        for activity in activities:
            if not activity.heartrate_stream or not activity.time_stream:
                continue

            hr_stream = activity.heartrate_stream
            time_stream = activity.time_stream
            velocity_stream = activity.velocity_stream or [0.0] * len(time_stream)

            length = min(len(hr_stream), len(time_stream), len(velocity_stream))
            if length < 2:
                continue

            for idx in range(1, length):
                hr_value = hr_stream[idx]
                time_prev = time_stream[idx - 1]
                time_curr = time_stream[idx]
                dt = time_curr - time_prev
                if dt <= 0:
                    continue

                zone_idx = assign_zone(hr_value)
                if zone_idx is None:
                    continue

                zone_stats[zone_idx]["time_seconds"] += dt
                velocity = velocity_stream[idx] if idx < len(velocity_stream) else 0.0
                if velocity and velocity > 0:
                    zone_stats[zone_idx]["distance_m"] += velocity * dt

        return zone_stats

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------
    def _get_strava_service(self) -> StravaService:
        if not self.strava_service:
            self.strava_service = create_strava_service(
                access_token=self.user.strava_access_token,
                refresh_token=self.user.strava_refresh_token,
            )
        return self.strava_service

    @staticmethod
    def _extract_stream(streams: Dict[str, Any], key: str) -> List[float]:
        stream = streams.get(key)
        if isinstance(stream, dict):
            data = stream.get("data")
            if isinstance(data, list):
                return data
        return []

    @staticmethod
    def _format_window(start: datetime, end: datetime) -> Dict[str, Any]:
        return {
            "start": start.isoformat() + "Z",
            "end": end.isoformat() + "Z",
            "days": (end - start).days,
        }

    @staticmethod
    def _format_seconds(seconds: float) -> str:
        total_seconds = int(round(seconds))
        hours, remainder = divmod(total_seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        if hours:
            return f"{hours}:{str(minutes).zfill(2)}:{str(secs).zfill(2)}"
        return f"{minutes}:{str(secs).zfill(2)}"

    @staticmethod
    def _format_pace(time_seconds: float, distance_m: float) -> Optional[str]:
        if distance_m <= 0 or time_seconds <= 0:
            return None
        seconds_per_km = time_seconds / (distance_m / 1000)
        minutes, secs = divmod(int(round(seconds_per_km)), 60)
        return f"{minutes}:{str(secs).zfill(2)} /km"
