"""Pytest fixtures and configuration."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from llmock3.app import create_app
from llmock3.config import Config, get_config

# Test API key used across all tests
TEST_API_KEY = "test-api-key"


@pytest.fixture
def test_config() -> Config:
    """Provide test configuration."""
    return {
        "models": [],
        "api-key": TEST_API_KEY,
    }


@pytest.fixture
async def client(test_config: Config) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client for testing."""
    app = create_app(config_getter=lambda: test_config)

    # Override the config dependency for testing
    app.dependency_overrides[get_config] = lambda: test_config

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
    ) as ac:
        yield ac
