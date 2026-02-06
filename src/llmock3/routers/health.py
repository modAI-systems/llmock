"""Health check endpoint."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from llmock3.config import Settings, get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(description="Health status")
    app_name: str = Field(description="Application name")
    version: str = Field(description="Application version")
    timestamp: datetime = Field(description="Current server timestamp")


@router.get("/health", response_model=HealthResponse)
async def health_check(
    settings: Annotated[Settings, Depends(get_settings)],
) -> HealthResponse:
    """Check the health status of the application.

    Returns basic application information and current timestamp.
    """
    return HealthResponse(
        status="healthy",
        app_name=settings.app_name,
        version=settings.app_version,
        timestamp=datetime.now(UTC),
    )
