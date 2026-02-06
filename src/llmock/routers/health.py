"""Health check endpoint."""

from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(description="Health status")
    timestamp: datetime = Field(description="Current server timestamp")


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Check the health status of the application.

    Returns health status and current timestamp.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(UTC),
    )
