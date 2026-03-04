"""Tests for error messages (trigger phrase-triggered errors) in chat and responses endpoints."""

from collections.abc import AsyncGenerator

import httpx
import pytest

from llmock.app import create_app
from llmock.config import Config, get_config

# Test API key used across all tests
TEST_API_KEY = "test-api-key"


@pytest.fixture
def test_config() -> Config:
    """Provide test config with ErrorStrategy and MirrorStrategy."""
    return {
        "models": [
            {"id": "gpt-4", "created": 1700000000, "owned_by": "openai"},
        ],
        "api-key": TEST_API_KEY,
        "strategies": ["ErrorStrategy", "MirrorStrategy"],
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
# Chat Completions - Trigger phrase
# ============================================================================


async def test_chat_trigger_phrase_429(client: httpx.AsyncClient) -> None:
    """raise error trigger phrase returns the correct HTTP 429 error."""
    response = await client.post(
        "/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [
                {
                    "role": "user",
                    "content": 'raise error {"code": 429, "message": "Rate limit exceeded"}',
                }
            ],
        },
    )

    assert response.status_code == 429
    data = response.json()
    assert data["error"]["message"] == "Rate limit exceeded"
    assert data["error"]["param"] is None


async def test_chat_trigger_phrase_with_type_and_error_code(
    client: httpx.AsyncClient,
) -> None:
    """raise error trigger phrase honours optional 'type' and 'error_code' fields."""
    response = await client.post(
        "/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [
                {
                    "role": "user",
                    "content": (
                        'raise error {"code": 503, "message": "Service unavailable",'
                        ' "type": "server_error", "error_code": "service_unavailable"}'
                    ),
                }
            ],
        },
    )

    assert response.status_code == 503
    data = response.json()
    assert data["error"]["message"] == "Service unavailable"
    assert data["error"]["type"] == "server_error"
    assert data["error"]["code"] == "service_unavailable"


async def test_chat_trigger_phrase_in_multiline_message(
    client: httpx.AsyncClient,
) -> None:
    """raise error trigger phrase is detected even within a longer multiline message."""
    response = await client.post(
        "/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Some preamble text\n"
                        'raise error {"code": 500, "message": "Internal error"}\n'
                        "Some trailing text"
                    ),
                }
            ],
        },
    )

    assert response.status_code == 500
    data = response.json()
    assert data["error"]["message"] == "Internal error"


async def test_chat_trigger_phrase_with_streaming(client: httpx.AsyncClient) -> None:
    """raise error trigger phrase returns JSON error even when stream=true (not SSE)."""
    response = await client.post(
        "/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [
                {
                    "role": "user",
                    "content": 'raise error {"code": 500, "message": "Internal server error"}',
                }
            ],
            "stream": True,
        },
    )

    # Should return directly as JSON error, not SSE
    assert response.status_code == 500
    data = response.json()
    assert data["error"]["message"] == "Internal server error"


async def test_chat_normal_message_not_affected(client: httpx.AsyncClient) -> None:
    """Normal messages without a trigger phrase fall through to MirrorStrategy."""
    response = await client.post(
        "/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "hello"}],
        },
    )

    assert response.status_code == 200


async def test_chat_error_uses_last_user_message(
    client: httpx.AsyncClient,
) -> None:
    """Error check uses the last user message, not earlier ones."""
    response = await client.post(
        "/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [
                {
                    "role": "user",
                    "content": 'raise error {"code": 500, "message": "Internal error"}',
                },
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
    """Model validation happens before error strategy — invalid model returns 404."""
    response = await client.post(
        "/chat/completions",
        json={
            "model": "nonexistent-model",
            "messages": [
                {
                    "role": "user",
                    "content": 'raise error {"code": 500, "message": "Internal error"}',
                }
            ],
        },
    )

    assert response.status_code == 404


async def test_chat_trigger_phrase_invalid_json_falls_through(
    client: httpx.AsyncClient,
) -> None:
    """A raise error line with invalid JSON is skipped; request falls through."""
    response = await client.post(
        "/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "raise error {not valid json}"}],
        },
    )

    assert response.status_code == 200


# ============================================================================
# Responses - Trigger phrase
# ============================================================================


async def test_responses_trigger_phrase_429(client: httpx.AsyncClient) -> None:
    """raise error trigger phrase works on the /responses endpoint."""
    response = await client.post(
        "/responses",
        json={
            "model": "gpt-4",
            "input": 'raise error {"code": 429, "message": "Rate limit exceeded"}',
        },
    )

    assert response.status_code == 429
    data = response.json()
    assert data["error"]["message"] == "Rate limit exceeded"


async def test_responses_trigger_phrase_with_streaming(
    client: httpx.AsyncClient,
) -> None:
    """raise error trigger phrase on /responses with stream=true returns JSON error."""
    response = await client.post(
        "/responses",
        json={
            "model": "gpt-4",
            "input": 'raise error {"code": 500, "message": "Internal server error"}',
            "stream": True,
        },
    )

    assert response.status_code == 500
    data = response.json()
    assert data["error"]["message"] == "Internal server error"
