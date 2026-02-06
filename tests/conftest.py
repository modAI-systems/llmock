"""Pytest fixtures and configuration."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from llmock3.app import create_app
from llmock3.config import Config, get_config


@pytest.fixture
def test_config() -> Config:
    """Provide test configuration."""
    return {
        "models": [],
    }


@pytest.fixture
async def client(test_config: Config) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client for testing."""
    app = create_app()

    # Override the config dependency for testing
    app.dependency_overrides[get_config] = lambda: test_config

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
