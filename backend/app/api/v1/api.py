"""
API v1 router configuration.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    users,
    health,
    workouts,
    goals,
    progress,
    dashboard,
    strava,
)
from app.core.settings import settings

api_router = APIRouter()

# Health and Authentication
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Users
api_router.include_router(users.router, prefix="/users", tags=["users"])

# Fitness Tracking
api_router.include_router(workouts.router, prefix="/workouts", tags=["workouts"])
api_router.include_router(goals.router, prefix="/goals", tags=["goals"])
api_router.include_router(progress.router, prefix="/progress", tags=["progress"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])

# Strava Integration
api_router.include_router(strava.router, prefix="/strava", tags=["strava"])
