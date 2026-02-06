"""FastAPI application factory and setup."""

from collections.abc import Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from llmock3.config import Config, get_config
from llmock3.routers import health, models


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware to validate API key for all requests except health."""

    def __init__(self, app, config_getter: Callable[[], Config] = get_config):
        """Initialize middleware with config getter."""
        super().__init__(app)
        self.config_getter = config_getter

    async def dispatch(self, request: Request, call_next):
        """Check API key before processing request."""
        # Skip auth for health endpoint
        if request.url.path == "/health":
            return await call_next(request)

        config = self.config_getter()
        config_api_key = config.get("api-key")

        # If no API key configured, allow all requests
        if not config_api_key:
            return await call_next(request)

        # Check Authorization header (Bearer token format)
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"error": {"message": "Missing API key", "type": "auth_error"}},
            )

        provided_key = auth_header.removeprefix("Bearer ")
        if provided_key != config_api_key:
            return JSONResponse(
                status_code=401,
                content={"error": {"message": "Invalid API key", "type": "auth_error"}},
            )

        return await call_next(request)


def create_app(config_getter: Callable[[], Config] = get_config) -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="LLMock3")

    # Add API key middleware
    app.add_middleware(APIKeyMiddleware, config_getter=config_getter)

    # Include routers
    app.include_router(health.router)
    app.include_router(models.router)

    return app


# Application instance for uvicorn
app = create_app()
