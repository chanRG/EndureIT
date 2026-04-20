"""
Strava API integration service.
"""

import time
from typing import Optional, Dict, Any, List
import requests
from requests.exceptions import RequestException

from app.core.settings import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class StravaAPIError(Exception):
    """Exception raised for Strava API errors."""

    pass


class StravaService:
    """Service for interacting with the Strava API."""

    BASE_URL = "https://www.strava.com/api/v3"
    TOKEN_URL = "https://www.strava.com/api/v3/oauth/token"

    def __init__(
        self,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        on_token_refresh=None,
    ):
        """
        Initialize the Strava service.

        Args:
            access_token: Strava access token
            refresh_token: Strava refresh token for token renewal
            on_token_refresh: Optional callback function(access_token, refresh_token, expires_at)
                             to persist refreshed tokens
        """
        self.access_token = access_token or settings.STRAVA_ACCESS_TOKEN
        self.refresh_token = refresh_token or settings.STRAVA_REFRESH_TOKEN
        self.client_id = settings.STRAVA_CLIENT_ID
        self.client_secret = settings.STRAVA_CLIENT_SECRET
        self.on_token_refresh = on_token_refresh

        if not self.access_token:
            raise StravaAPIError("Strava access token is required")

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Strava API requests."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        retry_on_401: bool = True,
    ) -> Dict[str, Any]:
        """
        Make a request to the Strava API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            data: Request body data
            retry_on_401: Whether to retry after refreshing token on 401

        Returns:
            API response as dictionary

        Raises:
            StravaAPIError: If the request fails
        """
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        headers = self._get_headers()

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data,
                timeout=30,
            )

            # Check for rate limiting
            if response.status_code == 429:
                logger.warning("Strava API rate limit exceeded")
                rate_limit_msg = "Strava API rate limit exceeded (100 requests/15min, 1000/day). Please wait 15 minutes and try again."
                raise StravaAPIError(rate_limit_msg)

            # Check for unauthorized (expired token)
            if response.status_code == 401:
                logger.warning("Strava access token expired or invalid")

                # Try to refresh token and retry once
                if retry_on_401 and self.refresh_token:
                    try:
                        logger.info("Attempting to refresh expired Strava token")
                        self.refresh_access_token()
                        # Retry the request once with new token
                        return self._make_request(
                            method, endpoint, params, data, retry_on_401=False
                        )
                    except StravaAPIError as e:
                        logger.error(f"Token refresh failed: {str(e)}")
                        raise StravaAPIError(
                            "Access token expired and refresh failed. Please re-authenticate."
                        )
                else:
                    raise StravaAPIError(
                        "Access token expired or invalid. Please re-authenticate."
                    )

            # Check for forbidden (scope issues)
            if response.status_code == 403:
                logger.error(f"Strava API forbidden error: {response.text}")
                raise StravaAPIError(
                    "Access forbidden. Please ensure your Strava app has the required scopes (activity:read_all)."
                )

            # Raise exception for other error status codes
            response.raise_for_status()

            return response.json()

        except RequestException as e:
            logger.error(f"Strava API request failed: {str(e)}")
            raise StravaAPIError(f"Failed to connect to Strava API: {str(e)}")

    def refresh_access_token(self) -> Dict[str, Any]:
        """
        Refresh the Strava access token using refresh token.

        Returns:
            Dictionary containing new access_token, refresh_token, and expires_at

        Raises:
            StravaAPIError: If token refresh fails
        """
        if not self.refresh_token or not self.client_id or not self.client_secret:
            raise StravaAPIError("Missing credentials for token refresh")

        try:
            response = requests.post(
                self.TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token,
                },
                timeout=30,
            )

            response.raise_for_status()
            token_data = response.json()

            # Update internal access token
            self.access_token = token_data["access_token"]
            self.refresh_token = token_data["refresh_token"]

            # Call the callback to persist tokens if provided
            if self.on_token_refresh:
                try:
                    self.on_token_refresh(
                        token_data["access_token"],
                        token_data["refresh_token"],
                        token_data["expires_at"],
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to persist refreshed tokens via callback: {str(e)}"
                    )

            return {
                "access_token": token_data["access_token"],
                "refresh_token": token_data["refresh_token"],
                "expires_at": token_data["expires_at"],
            }

        except RequestException as e:
            logger.error(f"Failed to refresh Strava token: {str(e)}")
            raise StravaAPIError(f"Token refresh failed: {str(e)}")

    def get_athlete(self) -> Dict[str, Any]:
        """
        Get the authenticated athlete's profile.

        Returns:
            Athlete profile data
        """
        return self._make_request("GET", "/athlete")

    def get_activities(
        self,
        before: Optional[int] = None,
        after: Optional[int] = None,
        page: int = 1,
        per_page: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Get the authenticated athlete's activities.

        Args:
            before: Unix timestamp to retrieve activities before
            after: Unix timestamp to retrieve activities after
            page: Page number
            per_page: Number of items per page (max 200)

        Returns:
            List of activity data
        """
        params = {"page": page, "per_page": min(per_page, 200)}  # Strava max is 200

        if before:
            params["before"] = before
        if after:
            params["after"] = after

        logger.info(f"Fetching Strava activities (page {page}, per_page {per_page})")
        activities = self._make_request("GET", "/athlete/activities", params=params)

        logger.info(f"Retrieved {len(activities)} activities from Strava")
        return activities

    def get_activity_by_id(
        self, activity_id: int, include_all_efforts: bool = False
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific activity.

        Args:
            activity_id: Strava activity ID
            include_all_efforts: Include all segment efforts

        Returns:
            Detailed activity data
        """
        params = {"include_all_efforts": str(include_all_efforts).lower()}
        return self._make_request("GET", f"/activities/{activity_id}", params=params)

    def get_athlete_stats(self, athlete_id: int) -> Dict[str, Any]:
        """
        Get athlete statistics.

        Args:
            athlete_id: Strava athlete ID

        Returns:
            Athlete statistics
        """
        return self._make_request("GET", f"/athletes/{athlete_id}/stats")

    def get_activity_streams(
        self, activity_id: int, keys: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get activity streams (detailed data points).

        Args:
            activity_id: Strava activity ID
            keys: List of stream types (e.g., 'time', 'distance', 'heartrate', 'watts')

        Returns:
            List of stream data
        """
        if keys is None:
            keys = [
                "time",
                "distance",
                "latlng",
                "altitude",
                "velocity_smooth",
                "heartrate",
                "cadence",
                "watts",
                "temp",
            ]

        keys_param = ",".join(keys)
        return self._make_request(
            "GET",
            f"/activities/{activity_id}/streams",
            params={"keys": keys_param, "key_by_type": "true"},
        )


def create_strava_service(
    access_token: Optional[str] = None,
    refresh_token: Optional[str] = None,
    on_token_refresh=None,
) -> StravaService:
    """
    Factory function to create a StravaService instance.

    Args:
        access_token: Strava access token (uses settings if not provided)
        refresh_token: Strava refresh token (uses settings if not provided)
        on_token_refresh: Optional callback to persist refreshed tokens

    Returns:
        StravaService instance
    """
    return StravaService(
        access_token=access_token,
        refresh_token=refresh_token,
        on_token_refresh=on_token_refresh,
    )
