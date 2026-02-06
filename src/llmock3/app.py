"""FastAPI application factory and setup."""

from fastapi import FastAPI

from llmock3.config import get_settings
from llmock3.routers import health, models


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
    )

    # Include routers
    app.include_router(health.router)
    app.include_router(models.router)

    return app


# Application instance for uvicorn
app = create_app()
