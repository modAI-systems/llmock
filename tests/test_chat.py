"""Tests for the /v1/chat/completions endpoint using official OpenAI client."""

from collections.abc import AsyncGenerator

import httpx
import pytest
from openai import AsyncOpenAI

from llmock.app import create_app
from llmock.config import Config, get_config

# Test API key used across all tests
TEST_API_KEY = "test-api-key"


@pytest.fixture
def test_config() -> Config:
    """Provide test config with a model for chat."""
    return {
        "models": [
            {"id": "gpt-4", "created": 1700000000, "owned_by": "openai"},
        ],
        "api-key": TEST_API_KEY,
    }


@pytest.fixture
async def openai_client(test_config: Config) -> AsyncGenerator[AsyncOpenAI, None]:
    """Provide an AsyncOpenAI client using ASGI transport (no real server needed)."""
    app = create_app(config_getter=lambda: test_config)
    app.dependency_overrides[get_config] = lambda: test_config

    # Use httpx with ASGITransport to test without spinning up a real server
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as http_client:
        client = AsyncOpenAI(
            api_key=TEST_API_KEY,
            http_client=http_client,
            base_url="http://testserver/v1",
        )
        yield client


async def test_chat_completions_non_streaming(openai_client: AsyncOpenAI) -> None:
    """Test non-streaming chat completion returns valid response."""
    user_message = "Hello, how are you?"
    response = await openai_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": user_message},
        ],
        stream=False,
    )

    # Verify response structure
    assert response.id.startswith("chatcmpl-")
    assert response.object == "chat.completion"
    assert response.model == "gpt-4"
    assert response.created > 0

    # Verify choices
    assert len(response.choices) == 1
    choice = response.choices[0]
    assert choice.index == 0
    assert choice.message.role == "assistant"
    # ContentMirrorStrategy should return the user's message
    assert choice.message.content == user_message
    assert choice.finish_reason == "stop"

    # Verify usage
    assert response.usage is not None
    assert response.usage.prompt_tokens > 0
    assert response.usage.completion_tokens > 0
    assert response.usage.total_tokens == (
        response.usage.prompt_tokens + response.usage.completion_tokens
    )


async def test_chat_completions_streaming(openai_client: AsyncOpenAI) -> None:
    """Test streaming chat completion returns valid chunks."""
    user_message = "Hello world!"
    stream = await openai_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": user_message},
        ],
        stream=True,
    )

    chunks = []
    async for chunk in stream:
        chunks.append(chunk)

    # Should have at least 3 chunks: role, content, finish
    assert len(chunks) >= 3

    # First chunk should have role
    first_chunk = chunks[0]
    assert first_chunk.id.startswith("chatcmpl-")
    assert first_chunk.object == "chat.completion.chunk"
    assert first_chunk.model == "gpt-4"
    assert len(first_chunk.choices) == 1
    assert first_chunk.choices[0].delta.role == "assistant"

    # Last chunk should have finish_reason
    last_chunk = chunks[-1]
    assert last_chunk.choices[0].finish_reason == "stop"

    # Collect content from all chunks
    content_parts = []
    for chunk in chunks:
        if chunk.choices[0].delta.content:
            content_parts.append(chunk.choices[0].delta.content)

    # ContentMirrorStrategy should return the user's message (streamed in chunks)
    full_content = "".join(content_parts)
    assert full_content == user_message
