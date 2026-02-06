"""Pytest fixtures and configuration."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from llmock3.app import create_app
from llmock3.config import Settings, get_settings


@pytest.fixture
def test_settings() -> Settings:
    """Provide test settings."""
    return Settings(
        app_name="LLMock3-Test",
        app_version="0.1.0-test",
        debug=True,
    )


@pytest.fixture
async def client(test_settings: Settings) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client for testing."""
    app = create_app()

    # Override the settings dependency for testing
    app.dependency_overrides[get_settings] = lambda: test_settings

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
