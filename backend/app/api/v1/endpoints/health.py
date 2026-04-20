"""
Health check endpoints.
"""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    message: str


@router.get("/", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """
    Health check endpoint.
    """
    return HealthResponse(status="healthy", message="Service is running")