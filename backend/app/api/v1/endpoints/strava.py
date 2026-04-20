"""
Strava integration endpoints.
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core.logging import get_logger
from app.db.database import get_db
from app.models.user import User
from app.services.strava_service import (
    StravaService,
    StravaAPIError,
    create_strava_service,
)
from app.services.strava_sync_service import StravaSyncService
from app.services.strava_analysis_service import StravaHeartRateAnalysisService

logger = get_logger(__name__)

router = APIRouter()


@router.get("/activities", response_model=List[dict])
def get_strava_activities(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(30, ge=1, le=200, description="Activities per page"),
    after: Optional[int] = Query(
        None, description="Unix timestamp to get activities after"
    ),
    before: Optional[int] = Query(
        None, description="Unix timestamp to get activities before"
    ),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get Strava activities for the authenticated user.
    Uses cached data when available to avoid rate limits.
    """
    # Check if user has Strava credentials
    if not current_user.strava_access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have Strava credentials. Please connect your Strava account.",
        )

    try:
        # Create sync service
        sync_service = StravaSyncService(db, current_user)

        # Try to sync activities (will use cache if recent)
        try:
            sync_result = sync_service.sync_activities(force_full_sync=False)
            logger.info(f"Sync result: {sync_result}")
        except StravaAPIError as e:
            # If rate limited, just use whatever is in cache
            if "rate limit" in str(e).lower():
                logger.warning(
                    f"Rate limited, using cached data for user {current_user.username}"
                )
            else:
                raise

        # Get cached activities
        cached_activities = sync_service.get_cached_activities()

        # Convert to dict format for API response
        activities = []
        for activity in cached_activities:
            activities.append(
                {
                    "id": activity.strava_id,
                    "name": activity.name,
                    "type": activity.activity_type,
                    "distance": activity.distance,
                    "moving_time": activity.moving_time,
                    "elapsed_time": activity.elapsed_time,
                    "total_elevation_gain": activity.total_elevation_gain,
                    "start_date": activity.start_date.isoformat() + "Z",
                    "start_date_local": activity.start_date_local.isoformat(),
                    "average_speed": activity.average_speed,
                    "max_speed": activity.max_speed,
                    "average_heartrate": activity.average_heartrate,
                    "max_heartrate": activity.max_heartrate,
                    "calories": activity.calories,
                    "achievement_count": activity.achievement_count,
                }
            )

        # Apply pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated = activities[start_idx:end_idx]

        logger.info(
            f"Returned {len(paginated)} cached activities for user {current_user.username}"
        )
        return paginated

    except StravaAPIError as e:
        logger.error(f"Strava API error for user {current_user.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching Strava activities: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching activities",
        )


@router.get("/activity/{activity_id}", response_model=dict)
def get_strava_activity(
    activity_id: int,
    include_all_efforts: bool = Query(True, description="Include all segment efforts"),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get detailed information about a specific Strava activity from cache.
    Returns cached data to avoid API rate limits.
    """
    if not current_user.strava_access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have Strava credentials",
        )

    try:
        from app.models.strava_activity import StravaActivity

        # Get activity from cache
        activity = (
            db.query(StravaActivity)
            .filter(
                StravaActivity.strava_id == activity_id,
                StravaActivity.user_id == current_user.id,
            )
            .first()
        )

        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found in cache. Try refreshing your activities.",
            )

        # Convert to API response format
        activity_data = {
            "id": activity.strava_id,
            "name": activity.name,
            "type": activity.activity_type,
            "distance": activity.distance,
            "moving_time": activity.moving_time,
            "elapsed_time": activity.elapsed_time,
            "total_elevation_gain": activity.total_elevation_gain,
            "start_date": activity.start_date.isoformat() + "Z",
            "start_date_local": activity.start_date_local.isoformat(),
            "average_speed": activity.average_speed,
            "max_speed": activity.max_speed,
            "average_heartrate": activity.average_heartrate,
            "max_heartrate": activity.max_heartrate,
            "has_heartrate": activity.has_heartrate,
            "calories": activity.calories,
            "achievement_count": activity.achievement_count,
            "kudos_count": activity.kudos_count,
            "best_efforts": activity.best_efforts or [],
            "map": (
                {"summary_polyline": activity.map_polyline}
                if activity.map_polyline
                else None
            ),
            "start_latlng": activity.start_latlng,
            "end_latlng": activity.end_latlng,
            "description": None,  # Not stored in cache
            "workout_type": None,  # Not stored in cache
            "suffer_score": None,  # Not stored in cache
        }

        return activity_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch activity from cache: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch activity: {str(e)}",
        )


@router.get("/best-efforts", response_model=dict)
def get_best_efforts(
    force_sync: bool = Query(False, description="Force sync from Strava API"),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get all-time best efforts (personal records) from cached Strava activities.
    Uses database cache to avoid rate limits. Set force_sync=true to fetch fresh data.
    """
    if not current_user.strava_access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have Strava credentials",
        )

    try:
        # Create sync service
        sync_service = StravaSyncService(db, current_user)

        # Try to sync activities (uses cache if recent)
        sync_result = {}
        try:
            sync_result = sync_service.sync_activities(force_full_sync=force_sync)
            logger.info(f"Sync result for user {current_user.id}: {sync_result}")

            # Sync best efforts for ALL activities that don't have them yet (no limit)
            # This only makes API calls for activities missing best_efforts data
            if sync_result.get("synced", False):
                # On first sync, get ALL best efforts (no limit)
                efforts_synced = sync_service.sync_best_efforts(limit=None)
                logger.info(f"Synced best efforts for {efforts_synced} activities")
            else:
                # Even if we didn't sync new activities, check if any existing ones need best efforts
                efforts_synced = sync_service.sync_best_efforts(limit=None)
                if efforts_synced > 0:
                    logger.info(
                        f"Synced missing best efforts for {efforts_synced} existing activities"
                    )
        except StravaAPIError as e:
            # If rate limited, just use cached data
            if "rate limit" in str(e).lower():
                logger.warning(f"Rate limited, using cached data")
                sync_result = {"synced": False, "reason": "Rate limited"}
            else:
                raise

        # Get best efforts from cache
        best_efforts = sync_service.get_best_efforts()

        # Get total activity count
        total_activities = len(sync_service.get_cached_activities())

        return {
            "total_activities": total_activities,
            "best_efforts": best_efforts,
            "cached": not sync_result.get("synced", True),
            "cache_age_minutes": sync_result.get("cache_age_minutes", 0),
            "rate_limited": "rate limit" in sync_result.get("reason", "").lower(),
        }

    except StravaAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e)
        )


@router.get("/pr-history/{distance_name}", response_model=dict)
def get_pr_history(
    distance_name: str,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get historical PR progression for a specific distance from cached data.
    Returns ONLY the runs where a new PR was set (time improved), with heart rate data.
    """
    if not current_user.strava_access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have Strava credentials",
        )

    try:
        from app.models.strava_activity import StravaActivity

        # Query cached activities with best efforts for this distance
        activities = (
            db.query(StravaActivity)
            .filter(
                StravaActivity.user_id == current_user.id,
                StravaActivity.best_efforts != None,
            )
            .order_by(StravaActivity.start_date.asc())
            .all()
        )  # Oldest first for chronological order

        # Find all efforts for this distance
        all_attempts = []

        for activity in activities:
            if activity.best_efforts:
                for effort in activity.best_efforts:
                    if effort.get("name") == distance_name:
                        pr_record = {
                            "name": effort.get("name"),
                            "distance": effort.get("distance"),
                            "elapsed_time": effort.get("elapsed_time"),
                            "moving_time": effort.get("moving_time"),
                            "start_date": effort.get("start_date"),
                            "start_date_local": effort.get("start_date_local"),
                            "activity_id": activity.strava_id,
                            "activity_name": activity.name,
                            "pr_rank": effort.get("pr_rank"),
                            "average_heartrate": activity.average_heartrate,
                            "max_heartrate": activity.max_heartrate,
                            "has_heartrate": activity.has_heartrate,
                        }
                        all_attempts.append(pr_record)
                        break

        # Filter to only include PRs (times that improved)
        pr_progression = []
        best_time_so_far = float("inf")

        for attempt in all_attempts:
            elapsed_time = attempt["elapsed_time"]
            # Only include if this is a new PR (faster than all previous)
            if elapsed_time < best_time_so_far:
                pr_progression.append(attempt)
                best_time_so_far = elapsed_time

        return {
            "distance_name": distance_name,
            "total_attempts": len(all_attempts),
            "pr_count": len(pr_progression),
            "pr_history": pr_progression,  # Only the PRs, in chronological order
        }

    except Exception as e:
        logger.error(f"Failed to fetch PR history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch PR history: {str(e)}",
        )


@router.get("/hr-zones", response_model=dict)
def get_heart_rate_zones(
    max_hr_override: Optional[int] = Query(
        None, ge=80, le=240, description="Override maximum heart rate in bpm"
    ),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get last-30-day heart rate zone analysis for running activities.
    """
    if not current_user.strava_access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have Strava credentials",
        )

    try:
        analysis_service = StravaHeartRateAnalysisService(db, current_user)
        return analysis_service.get_last_month_zone_analysis(
            max_hr_override=max_hr_override
        )
    except StravaAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to compute heart rate zones: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute heart rate zone analysis.",
        )


@router.get("/athlete", response_model=dict)
def get_strava_athlete(
    current_user: User = Depends(deps.get_current_user), db: Session = Depends(get_db)
) -> Any:
    """
    Get the authenticated user's Strava athlete profile.
    """
    if not current_user.strava_access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have Strava credentials",
        )

    try:

        def save_tokens(access_token: str, refresh_token: str, expires_at: int):
            current_user.strava_access_token = access_token
            current_user.strava_refresh_token = refresh_token
            db.commit()

        strava_service = create_strava_service(
            access_token=current_user.strava_access_token,
            refresh_token=current_user.strava_refresh_token,
            on_token_refresh=save_tokens,
        )

        athlete = strava_service.get_athlete()
        return athlete

    except StravaAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch Strava athlete: {str(e)}",
        )


@router.get("/stats", response_model=dict)
def get_strava_stats(
    current_user: User = Depends(deps.get_current_user), db: Session = Depends(get_db)
) -> Any:
    """
    Get the authenticated user's Strava statistics.
    """
    if not current_user.strava_access_token or not current_user.strava_athlete_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have Strava credentials",
        )

    try:

        def save_tokens(access_token: str, refresh_token: str, expires_at: int):
            current_user.strava_access_token = access_token
            current_user.strava_refresh_token = refresh_token
            db.commit()

        strava_service = create_strava_service(
            access_token=current_user.strava_access_token,
            refresh_token=current_user.strava_refresh_token,
            on_token_refresh=save_tokens,
        )

        stats = strava_service.get_athlete_stats(current_user.strava_athlete_id)
        return stats

    except StravaAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch Strava stats: {str(e)}",
        )


@router.get("/activity/{activity_id}/streams", response_model=List[dict])
def get_strava_activity_streams(
    activity_id: int,
    keys: Optional[str] = Query(None, description="Comma-separated stream types"),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get detailed stream data for a specific activity.

    Stream keys can include: time, distance, latlng, altitude, velocity_smooth,
    heartrate, cadence, watts, temp, moving, grade_smooth
    """
    if not current_user.strava_access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have Strava credentials",
        )

    try:

        def save_tokens(access_token: str, refresh_token: str, expires_at: int):
            current_user.strava_access_token = access_token
            current_user.strava_refresh_token = refresh_token
            db.commit()

        strava_service = create_strava_service(
            access_token=current_user.strava_access_token,
            refresh_token=current_user.strava_refresh_token,
            on_token_refresh=save_tokens,
        )

        # Parse keys if provided
        stream_keys = keys.split(",") if keys else None

        streams = strava_service.get_activity_streams(activity_id, stream_keys)
        return streams

    except StravaAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch activity streams: {str(e)}",
        )
