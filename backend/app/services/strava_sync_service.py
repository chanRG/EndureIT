"""
Strava sync service for caching Strava data in the database.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.strava_activity import StravaActivity
from app.models.user import User
from app.services.strava_service import StravaAPIError, create_strava_service

logger = get_logger(__name__)


def _fire_match_job(strava_id: int) -> None:
    """
    Fire-and-forget: enqueue a Strava ↔ PlannedWorkout match job from sync
    (non-async) context. Uses a fresh event loop to bridge sync → async.
    Never raises — failure to enqueue must not break the sync pipeline.
    """
    try:
        from app.workers.queue import enqueue

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(
                enqueue("match_planned_workout", strava_activity_id=strava_id)
            )
        finally:
            loop.close()
    except Exception as exc:
        logger.debug(
            "Could not enqueue match job for Strava activity %s: %s", strava_id, exc
        )


class StravaSyncService:
    """Service for syncing Strava data to database."""

    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user

        # Define callback to update user tokens when refreshed
        def save_refreshed_tokens(
            access_token: str, refresh_token: str, expires_at: int
        ):
            """Persist refreshed tokens to database."""
            logger.info(f"Updating refreshed Strava tokens for user {user.id}")
            user.strava_access_token = access_token
            user.strava_refresh_token = refresh_token
            # Note: We don't commit here - let the calling code handle transaction
            # But we do need to flush to update the session
            self.db.flush()

        self.strava_service = create_strava_service(
            access_token=user.strava_access_token,
            refresh_token=user.strava_refresh_token,
            on_token_refresh=save_refreshed_tokens,
        )

    def sync_activities(self, force_full_sync: bool = False) -> Dict[str, Any]:
        """
        Sync activities from Strava to database.
        Only fetches new activities unless force_full_sync is True.
        """
        # Get the most recent activity date from DB
        last_activity = (
            self.db.query(StravaActivity)
            .filter(StravaActivity.user_id == self.user.id)
            .order_by(StravaActivity.start_date.desc())
            .first()
        )

        # If we have cached data less than 1 hour old and not forcing, skip sync
        if not force_full_sync and last_activity and last_activity.last_synced:
            time_since_sync = datetime.utcnow() - last_activity.last_synced
            if time_since_sync < timedelta(hours=1):
                logger.info(
                    f"Using cached data for user {self.user.id}, last synced {time_since_sync.seconds // 60} minutes ago"
                )
                return {
                    "synced": False,
                    "reason": "Recent cache available",
                    "cache_age_minutes": time_since_sync.seconds // 60,
                }

        # Determine the starting point for sync
        after = None
        if not force_full_sync and last_activity:
            # Get activities after the last synced date
            after = int(last_activity.start_date.timestamp())

        # Fetch activities from Strava
        new_activities = []
        page = 1
        per_page = 200

        try:
            while True:
                activities = self.strava_service.get_activities(
                    page=page, per_page=per_page, after=after
                )

                if not activities:
                    break

                for activity_data in activities:
                    # Check if activity already exists
                    existing = (
                        self.db.query(StravaActivity)
                        .filter(
                            StravaActivity.strava_id == activity_data["id"],
                            StravaActivity.user_id == self.user.id,
                        )
                        .first()
                    )

                    if existing:
                        # Update existing activity
                        self._update_activity(existing, activity_data)
                    else:
                        # Create new activity
                        new_activity = self._create_activity(activity_data)
                        new_activities.append(new_activity)

                if len(activities) < per_page:
                    break

                page += 1

            self.db.commit()

            # Enqueue auto-match jobs for each new activity (after commit so
            # the rows are visible to the worker's separate DB session).
            for activity in new_activities:
                _fire_match_job(activity.strava_id)

            return {
                "synced": True,
                "new_activities": len(new_activities),
                "total_cached": self.db.query(StravaActivity)
                .filter(StravaActivity.user_id == self.user.id)
                .count(),
            }

        except StravaAPIError as e:
            logger.error(f"Failed to sync activities for user {self.user.id}: {str(e)}")
            raise

    def sync_best_efforts(self, limit: int = None) -> int:
        """
        Sync best efforts for ALL running activities that don't have them cached.
        Only makes API calls for activities missing best_efforts data.

        Args:
            limit: Max number to sync. If None, syncs ALL running activities needing efforts.

        Returns:
            Number of activities updated.
        """
        # Get ALL running activities that DON'T have best efforts cached yet
        # This prevents making API calls for data we already have
        query = (
            self.db.query(StravaActivity)
            .filter(
                StravaActivity.user_id == self.user.id,
                StravaActivity.activity_type.ilike(
                    "%run%"
                ),  # All runs, not just those with achievements
                StravaActivity.best_efforts == None,  # Only fetch if not already cached
            )
            .order_by(StravaActivity.start_date.desc())
        )

        if limit:
            query = query.limit(limit)

        activities_needing_efforts = query.all()

        if not activities_needing_efforts:
            logger.info(f"All running activities already have best_efforts cached")
            return 0

        logger.info(
            f"Fetching best_efforts for {len(activities_needing_efforts)} running activities"
        )

        updated = 0
        for activity in activities_needing_efforts:
            try:
                detailed = self.strava_service.get_activity_by_id(
                    activity.strava_id, include_all_efforts=True
                )

                # Cache the best_efforts even if empty - prevents re-fetching
                activity.best_efforts = detailed.get("best_efforts", [])
                activity.last_synced = datetime.utcnow()
                updated += 1

                if activity.best_efforts:
                    logger.debug(
                        f"Cached {len(activity.best_efforts)} best_efforts for activity {activity.strava_id}"
                    )
                else:
                    logger.debug(
                        f"No best_efforts for activity {activity.strava_id} (cached empty list)"
                    )

            except Exception as e:
                logger.warning(
                    f"Failed to fetch best efforts for activity {activity.strava_id}: {str(e)}"
                )
                continue

        if updated > 0:
            self.db.commit()
            logger.info(f"Successfully cached best_efforts for {updated} activities")

        return updated

    def _create_activity(self, data: Dict[str, Any]) -> StravaActivity:
        """Create a new StravaActivity from API data."""
        # Extract map data if available
        map_data = data.get("map", {})
        map_polyline = (
            map_data.get("summary_polyline") if isinstance(map_data, dict) else None
        )

        activity = StravaActivity(
            strava_id=data["id"],
            user_id=self.user.id,
            name=data["name"],
            activity_type=data["type"],
            start_date=datetime.fromisoformat(
                data["start_date"].replace("Z", "+00:00")
            ),
            start_date_local=datetime.fromisoformat(
                data["start_date_local"].replace("Z", "+00:00")
            ),
            distance=data.get("distance", 0),
            moving_time=data.get("moving_time", 0),
            elapsed_time=data.get("elapsed_time", 0),
            total_elevation_gain=data.get("total_elevation_gain", 0),
            average_heartrate=data.get("average_heartrate"),
            max_heartrate=data.get("max_heartrate"),
            has_heartrate=data.get("has_heartrate", False),
            average_speed=data.get("average_speed"),
            max_speed=data.get("max_speed"),
            calories=data.get("calories"),
            achievement_count=data.get("achievement_count", 0),
            kudos_count=data.get("kudos_count", 0),
            map_polyline=map_polyline,
            start_latlng=data.get("start_latlng"),
            end_latlng=data.get("end_latlng"),
            last_synced=datetime.utcnow(),
        )

        self.db.add(activity)
        return activity

    def _update_activity(self, activity: StravaActivity, data: Dict[str, Any]):
        """Update an existing activity with fresh data."""
        activity.name = data["name"]
        activity.kudos_count = data.get("kudos_count", 0)
        activity.achievement_count = data.get("achievement_count", 0)
        activity.last_synced = datetime.utcnow()

    def get_cached_activities(self) -> List[StravaActivity]:
        """Get all cached activities for the user."""
        return (
            self.db.query(StravaActivity)
            .filter(StravaActivity.user_id == self.user.id)
            .order_by(StravaActivity.start_date.desc())
            .all()
        )

    def get_best_efforts(self) -> List[Dict[str, Any]]:
        """Get all best efforts from cached activities."""
        activities = (
            self.db.query(StravaActivity)
            .filter(
                StravaActivity.user_id == self.user.id,
                StravaActivity.best_efforts != None,
            )
            .all()
        )

        all_best_efforts = {}

        for activity in activities:
            if activity.best_efforts:
                for effort in activity.best_efforts:
                    name = effort.get("name")
                    if name:
                        # Keep the fastest time for each distance
                        if name not in all_best_efforts or effort.get(
                            "elapsed_time", 999999
                        ) < all_best_efforts[name].get("elapsed_time", 999999):
                            all_best_efforts[name] = {
                                **effort,
                                "activity_id": activity.strava_id,
                                "activity_name": activity.name,
                                "average_heartrate": activity.average_heartrate,
                                "max_heartrate": activity.max_heartrate,
                                "has_heartrate": activity.has_heartrate,
                            }

        return list(all_best_efforts.values())
