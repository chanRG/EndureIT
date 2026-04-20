"""
Dashboard endpoint for EndureIT API.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.db.database import get_db
from app.models.user import User
from app.schemas.workout import UserDashboard
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("", response_model=UserDashboard)
def get_dashboard(
    db: Session = Depends(get_db), current_user: User = Depends(deps.get_current_user)
):
    """Get comprehensive dashboard data for the current user.

    Returns aggregated statistics including:
    - Total workouts and recent activity
    - Active and completed goals
    - Latest weight and weight change
    - Recent workout summaries
    """
    return DashboardService.get_user_dashboard(db, current_user.id)
