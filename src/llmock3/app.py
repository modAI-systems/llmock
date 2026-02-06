"""FastAPI application factory and setup."""

from fastapi import FastAPI

from llmock3.routers import health, models


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="LLMock3")

    # Include routers
    app.include_router(health.router)
    app.include_router(models.router)

    return app


# Application instance for uvicorn
app = create_app()
