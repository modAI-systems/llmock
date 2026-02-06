"""Tests for the /v1/responses endpoint."""

from collections.abc import AsyncGenerator

import httpx
import pytest

from llmock.app import create_app
from llmock.config import Config, get_config

# Test API key used across all tests
TEST_API_KEY = "test-api-key"


@pytest.fixture
def test_config() -> Config:
    """Provide test config with a model for responses."""
    return {
        "models": [
            {"id": "gpt-4o", "created": 1700000000, "owned_by": "openai"},
        ],
        "api-key": TEST_API_KEY,
    }


@pytest.fixture
async def client(test_config: Config) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provide an async HTTP client for testing."""
    app = create_app(config_getter=lambda: test_config)
    app.dependency_overrides[get_config] = lambda: test_config

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
    ) as http_client:
        yield http_client


async def test_responses_simple_string_input(client: httpx.AsyncClient) -> None:
    """Test response creation with simple string input."""
    input_text = "Tell me a story about a unicorn."
    response = await client.post(
        "/v1/responses",
        json={
            "model": "gpt-4o",
            "input": input_text,
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert data["id"].startswith("resp_")
    assert data["object"] == "response"
    assert data["status"] == "completed"
    assert data["model"] == "gpt-4o"
    assert data["created_at"] > 0
    assert data["completed_at"] is not None

    # Verify output
    assert len(data["output"]) == 1
    output_item = data["output"][0]
    assert output_item["type"] == "message"
    assert output_item["id"].startswith("msg_")
    assert output_item["status"] == "completed"
    assert output_item["role"] == "assistant"

    # ContentMirrorStrategy should return the input
    assert len(output_item["content"]) == 1
    content = output_item["content"][0]
    assert content["type"] == "output_text"
    assert content["text"] == input_text
    assert content["annotations"] == []

    # Verify usage
    assert data["usage"] is not None
    assert data["usage"]["input_tokens"] > 0
    assert data["usage"]["output_tokens"] > 0
    assert data["usage"]["total_tokens"] == (
        data["usage"]["input_tokens"] + data["usage"]["output_tokens"]
    )


async def test_responses_message_list_input(client: httpx.AsyncClient) -> None:
    """Test response creation with message list input."""
    user_message = "What is the capital of France?"
    response = await client.post(
        "/v1/responses",
        json={
            "model": "gpt-4o",
            "input": [
                {"role": "user", "content": user_message},
            ],
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response
    assert data["status"] == "completed"
    assert len(data["output"]) == 1

    # ContentMirrorStrategy should return the user's message
    content = data["output"][0]["content"][0]
    assert content["text"] == user_message


async def test_responses_with_instructions(client: httpx.AsyncClient) -> None:
    """Test response creation with instructions."""
    input_text = "Hello!"
    instructions = "You are a helpful assistant."
    response = await client.post(
        "/v1/responses",
        json={
            "model": "gpt-4o",
            "input": input_text,
            "instructions": instructions,
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Verify instructions are stored
    assert data["instructions"] == instructions


async def test_responses_with_metadata(client: httpx.AsyncClient) -> None:
    """Test response creation with metadata."""
    input_text = "Test input"
    metadata = {"user_id": "123", "session": "abc"}
    response = await client.post(
        "/v1/responses",
        json={
            "model": "gpt-4o",
            "input": input_text,
            "metadata": metadata,
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Verify metadata is stored
    assert data["metadata"] == metadata


async def test_responses_invalid_model(client: httpx.AsyncClient) -> None:
    """Test response creation with non-existent model returns 404."""
    response = await client.post(
        "/v1/responses",
        json={
            "model": "non-existent-model",
            "input": "Hello",
        },
    )

    assert response.status_code == 404
    data = response.json()
    assert "error" in data["detail"]
    assert data["detail"]["error"]["code"] == "model_not_found"


async def test_responses_streaming(client: httpx.AsyncClient) -> None:
    """Test streaming response returns valid SSE events."""
    input_text = "Hello world!"
    async with client.stream(
        "POST",
        "/v1/responses",
        json={
            "model": "gpt-4o",
            "input": input_text,
            "stream": True,
        },
    ) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        events = []
        async for line in response.aiter_lines():
            if line.startswith("event:"):
                event_type = line.removeprefix("event:").strip()
                events.append(event_type)

    # Verify key events are present
    assert "response.created" in events
    assert "response.in_progress" in events
    assert "response.output_item.added" in events
    assert "response.content_part.added" in events
    assert "response.output_text.delta" in events
    assert "response.output_text.done" in events
    assert "response.content_part.done" in events
    assert "response.output_item.done" in events
    assert "response.completed" in events


async def test_responses_streaming_content(client: httpx.AsyncClient) -> None:
    """Test streaming response content matches expected output."""
    import json

    input_text = "Hello world!"
    async with client.stream(
        "POST",
        "/v1/responses",
        json={
            "model": "gpt-4o",
            "input": input_text,
            "stream": True,
        },
    ) as response:
        assert response.status_code == 200

        delta_texts = []
        final_text = None
        current_event = None

        async for line in response.aiter_lines():
            line = line.strip()
            if line.startswith("event:"):
                current_event = line.removeprefix("event:").strip()
            elif line.startswith("data:"):
                data = json.loads(line.removeprefix("data:").strip())
                if current_event == "response.output_text.delta":
                    delta_texts.append(data["delta"])
                elif current_event == "response.output_text.done":
                    final_text = data["text"]

    # Verify streamed deltas reconstruct the full text
    assert "".join(delta_texts) == input_text
    assert final_text == input_text


async def test_responses_multi_turn_conversation(client: httpx.AsyncClient) -> None:
    """Test response with multi-turn conversation input."""
    response = await client.post(
        "/v1/responses",
        json={
            "model": "gpt-4o",
            "input": [
                {"role": "user", "content": "Hi there!"},
                {"role": "assistant", "content": "Hello! How can I help you?"},
                {"role": "user", "content": "What time is it?"},
            ],
        },
    )

    assert response.status_code == 200
    data = response.json()

    # ContentMirrorStrategy should return the last user message
    content = data["output"][0]["content"][0]
    assert content["text"] == "What time is it?"


async def test_responses_optional_parameters(client: httpx.AsyncClient) -> None:
    """Test response creation with optional parameters."""
    response = await client.post(
        "/v1/responses",
        json={
            "model": "gpt-4o",
            "input": "Test",
            "temperature": 0.5,
            "top_p": 0.9,
            "max_output_tokens": 100,
            "truncation": "auto",
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Verify parameters are reflected in response
    assert data["temperature"] == 0.5
    assert data["top_p"] == 0.9
    assert data["max_output_tokens"] == 100
    assert data["truncation"] == "auto"
