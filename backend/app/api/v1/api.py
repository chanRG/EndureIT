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
    training_plans,
    planned_workouts,
    nutrition,
    push,
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

# Training Plans
api_router.include_router(
    training_plans.router, prefix="/training-plans", tags=["training-plans"]
)
api_router.include_router(
    planned_workouts.router, prefix="/planned-workouts", tags=["planned-workouts"]
)

# Nutrition
api_router.include_router(nutrition.router, prefix="/nutrition", tags=["nutrition"])
api_router.include_router(push.router, prefix="/push", tags=["push"])
