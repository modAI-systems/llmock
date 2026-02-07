"""FastAPI application factory and setup."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from llmock.config import Config, get_config
from llmock.routers import chat, health, models, responses


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware to validate API key for all requests except health."""

    def __init__(self, app, config: Config):
        """Initialize middleware with config."""
        super().__init__(app)
        self.config = config

    async def dispatch(self, request: Request, call_next):
        """Check API key before processing request."""
        # Skip auth for OPTIONS preflight requests (CORS)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Skip auth for health endpoint
        if request.url.path == "/health":
            return await call_next(request)

        config_api_key = self.config.get("api-key")

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


def create_app(config: Config = get_config()) -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="llmock")

    # Get CORS origins from config
    cors_config = config.get("cors", {})
    allow_origins = cors_config.get("allow-origins", ["http://localhost:8000"])

    # Add CORS middleware to allow browser connections
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add API key middleware
    app.add_middleware(APIKeyMiddleware, config=config)

    # Include routers
    app.include_router(health.router)
    app.include_router(models.router)
    app.include_router(chat.router)
    app.include_router(responses.router)

    return app


# Application instance for uvicorn
app = create_app()
