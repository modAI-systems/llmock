"""Tests for the health endpoint."""

from datetime import UTC, datetime

from httpx import AsyncClient


async def test_health_endpoint_returns_200(client: AsyncClient) -> None:
    """Test that the health endpoint returns a 200 status code."""
    response = await client.get("/health")
    assert response.status_code == 200


async def test_health_endpoint_returns_healthy_status(client: AsyncClient) -> None:
    """Test that the health endpoint returns healthy status."""
    response = await client.get("/health")
    data = response.json()
    assert data["status"] == "healthy"


async def test_health_endpoint_returns_app_info(client: AsyncClient) -> None:
    """Test that the health endpoint returns correct app information."""
    response = await client.get("/health")
    data = response.json()

    # These values come from test_settings fixture
    assert data["app_name"] == "LLMock3-Test"
    assert data["version"] == "0.1.0-test"


async def test_health_endpoint_returns_timestamp(client: AsyncClient) -> None:
    """Test that the health endpoint returns a valid timestamp."""
    before = datetime.now(UTC)
    response = await client.get("/health")
    after = datetime.now(UTC)

    data = response.json()
    timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))

    assert before <= timestamp <= after


async def test_health_response_schema(client: AsyncClient) -> None:
    """Test that the health endpoint response has all required fields."""
    response = await client.get("/health")
    data = response.json()

    required_fields = {"status", "app_name", "version", "timestamp"}
    assert required_fields == set(data.keys())
