"""Tests for error messages (message-content-triggered errors) in chat and responses endpoints."""

from collections.abc import AsyncGenerator

import httpx
import pytest

from llmock.app import create_app
from llmock.config import Config, get_config

# Test API key used across all tests
TEST_API_KEY = "test-api-key"


@pytest.fixture
def test_config() -> Config:
    """Provide test config with models and error messages for testing."""
    return {
        "models": [
            {"id": "gpt-4", "created": 1700000000, "owned_by": "openai"},
        ],
        "api-key": TEST_API_KEY,
        "strategies": ["ErrorStrategy"],
        "error-messages": {
            "trigger-500": {
                "status-code": 500,
                "message": "Internal server error",
                "type": "server_error",
                "code": "internal_error",
            },
            "trigger-503": {
                "status-code": 503,
                "message": "Service unavailable",
                "type": "api_error",
                "code": "service_unavailable",
            },
        },
    }


@pytest.fixture
async def client(test_config: Config) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provide an async HTTP client for testing."""
    app = create_app(config=test_config)
    app.dependency_overrides[get_config] = lambda: test_config

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
    ) as http_client:
        yield http_client


# ============================================================================
# Chat Completions - Error Messages
# ============================================================================


async def test_chat_configured_error(client: httpx.AsyncClient) -> None:
    """Test that a configured error message triggers the correct HTTP error response."""
    response = await client.post(
        "/v1/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "trigger-500"}],
        },
    )

    assert response.status_code == 500
    data = response.json()
    assert data["error"]["message"] == "Internal server error"
    assert data["error"]["type"] == "server_error"
    assert data["error"]["param"] is None
    assert data["error"]["code"] == "internal_error"


async def test_chat_error_with_streaming(client: httpx.AsyncClient) -> None:
    """Test error message returns error even when stream=true (not SSE)."""
    response = await client.post(
        "/v1/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "trigger-500"}],
            "stream": True,
        },
    )

    # Should return directly as JSON error, not SSE
    assert response.status_code == 500
    data = response.json()
    assert data["error"]["code"] == "internal_error"


async def test_chat_normal_message_not_affected(client: httpx.AsyncClient) -> None:
    """Test that normal messages are not treated as error triggers."""
    response = await client.post(
        "/v1/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "hello"}],
        },
    )

    assert response.status_code == 200


async def test_chat_error_uses_last_user_message(
    client: httpx.AsyncClient,
) -> None:
    """Test error check uses the last user message, not earlier ones."""
    response = await client.post(
        "/v1/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [
                {"role": "user", "content": "trigger-500"},
                {"role": "assistant", "content": "ok"},
                {"role": "user", "content": "hello"},
            ],
        },
    )

    # Last user message is "hello", not an error trigger → normal 200
    assert response.status_code == 200


async def test_chat_invalid_model_returns_404(
    client: httpx.AsyncClient,
) -> None:
    """Test that invalid model returns 404 even with error message."""
    response = await client.post(
        "/v1/chat/completions",
        json={
            "model": "nonexistent-model",
            "messages": [{"role": "user", "content": "trigger-500"}],
        },
    )

    # Model validation happens first → 404
    assert response.status_code == 404


# ============================================================================
# Responses - Error Messages
# ============================================================================


async def test_responses_configured_error(client: httpx.AsyncClient) -> None:
    """Test that a configured error message triggers the correct HTTP error in responses endpoint."""
    response = await client.post(
        "/v1/responses",
        json={
            "model": "gpt-4",
            "input": "trigger-500",
        },
    )

    assert response.status_code == 500
    data = response.json()
    assert data["error"]["message"] == "Internal server error"
    assert data["error"]["type"] == "server_error"
    assert data["error"]["code"] == "internal_error"


async def test_responses_error_with_streaming(client: httpx.AsyncClient) -> None:
    """Test error message in responses endpoint with streaming returns JSON error."""
    response = await client.post(
        "/v1/responses",
        json={
            "model": "gpt-4",
            "input": "trigger-500",
            "stream": True,
        },
    )

    assert response.status_code == 500
    data = response.json()
    assert data["error"]["code"] == "internal_error"
