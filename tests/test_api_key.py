"""Tests for API key authentication middleware."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from llmock.app import create_app
from llmock.config import Config, get_config

TEST_API_KEY = "test-secret-key"


@pytest.fixture
def config_with_api_key() -> Config:
    """Provide config with API key set."""
    return {"models": [], "api-key": TEST_API_KEY}


@pytest.fixture
def config_without_api_key() -> Config:
    """Provide config without API key (auth disabled)."""
    return {"models": []}


@pytest.fixture
async def client_with_auth(
    config_with_api_key: Config,
) -> AsyncGenerator[AsyncClient, None]:
    """Client for app with API key configured."""
    app = create_app(config=config_with_api_key)
    app.dependency_overrides[get_config] = lambda: config_with_api_key

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def client_no_auth(
    config_without_api_key: Config,
) -> AsyncGenerator[AsyncClient, None]:
    """Client for app without API key configured."""
    app = create_app(config=config_without_api_key)
    app.dependency_overrides[get_config] = lambda: config_without_api_key

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_request_without_api_key_returns_401(
    client_with_auth: AsyncClient,
) -> None:
    """Test that requests without API key are rejected."""
    response = await client_with_auth.get("/v1/models")
    assert response.status_code == 401
    assert response.json()["error"]["type"] == "auth_error"


async def test_request_with_invalid_api_key_returns_401(
    client_with_auth: AsyncClient,
) -> None:
    """Test that requests with wrong API key are rejected."""
    response = await client_with_auth.get(
        "/v1/models",
        headers={"Authorization": "Bearer wrong-key"},
    )
    assert response.status_code == 401


async def test_request_with_valid_api_key_succeeds(
    client_with_auth: AsyncClient,
) -> None:
    """Test that requests with correct API key are allowed."""
    response = await client_with_auth.get(
        "/v1/models",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
    )
    assert response.status_code == 200


async def test_health_endpoint_bypasses_auth(client_with_auth: AsyncClient) -> None:
    """Test that health endpoint does not require authentication."""
    response = await client_with_auth.get("/health")
    assert response.status_code == 200


async def test_no_auth_required_when_api_key_not_configured(
    client_no_auth: AsyncClient,
) -> None:
    """Test that requests succeed when no API key is configured."""
    response = await client_no_auth.get("/v1/models")
    assert response.status_code == 200


async def test_malformed_auth_header_returns_401(
    client_with_auth: AsyncClient,
) -> None:
    """Test that malformed Authorization header is rejected."""
    response = await client_with_auth.get(
        "/v1/models",
        headers={"Authorization": "Basic sometoken"},
    )
    assert response.status_code == 401
