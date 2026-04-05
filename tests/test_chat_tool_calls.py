"""Tests for tool calling support in /chat/completions."""

import json
from collections.abc import AsyncGenerator

import httpx
import pytest
from openai import AsyncOpenAI

from llmock.app import create_app
from llmock.config import Config, get_config

# Test API key used across all tests
TEST_API_KEY = "test-api-key"

# Standard tool definition for testing (Chat API style)
CALCULATOR_TOOL = {
    "type": "function",
    "function": {
        "name": "calculate",
        "description": "Evaluate a math expression",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The math expression to evaluate",
                }
            },
            "required": ["expression"],
        },
    },
}

SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search",
        "description": "Search the web",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
            },
            "required": ["query"],
        },
    },
}


@pytest.fixture
def test_config() -> Config:
    """Provide test config with ToolCallStrategy"""
    return {
        "models": [
            {"id": "gpt-4", "created": 1700000000, "owned_by": "openai"},
        ],
        "api-key": TEST_API_KEY,
        "strategies": ["ToolCallStrategy"],
    }


@pytest.fixture
async def openai_client(test_config: Config) -> AsyncGenerator[AsyncOpenAI, None]:
    """Provide an AsyncOpenAI client using ASGI transport."""
    app = create_app(config=test_config)
    app.dependency_overrides[get_config] = lambda: test_config

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as http_client:
        client = AsyncOpenAI(
            api_key=TEST_API_KEY,
            http_client=http_client,
            base_url="http://testserver",
        )
        yield client


@pytest.fixture
async def raw_client(test_config: Config) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provide a raw HTTP client for testing (no OpenAI SDK parsing)."""
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
# Tool Call - Initial Request (no tool result yet)
# ============================================================================


async def test_tool_call_streaming_first_request(raw_client: httpx.AsyncClient) -> None:
    """Test streaming tool call response when trigger phrase is present."""
    async with raw_client.stream(
        "POST",
        "/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [
                {
                    "role": "user",
                    "content": "call tool 'calculate' with '{\"expression\": \"2+2\"}'",
                },
            ],
            "tools": [CALCULATOR_TOOL],
            "stream": True,
            "stream_options": {"include_usage": True},
        },
    ) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        chunks = []
        async for line in response.aiter_lines():
            if line.startswith("data: ") and line != "data: [DONE]":
                data = json.loads(line.removeprefix("data: "))
                chunks.append(data)

    # Should have at least 3 chunks: first (role+tool call), finish, usage
    assert len(chunks) >= 3

    # First chunk: role=assistant, content=null, tool_calls[0] with id+name+args
    first = chunks[0]
    assert first["object"] == "chat.completion.chunk"
    assert first["model"] == "gpt-4"
    assert first["choices"][0]["delta"]["role"] == "assistant"
    assert first["choices"][0]["delta"]["content"] is None
    tool_calls = first["choices"][0]["delta"]["tool_calls"]
    assert len(tool_calls) == 1
    assert tool_calls[0]["id"].startswith("call_")
    assert tool_calls[0]["type"] == "function"
    assert tool_calls[0]["function"]["name"] == "calculate"

    # First chunk also contains arguments
    args_str = tool_calls[0]["function"]["arguments"]
    args = json.loads(args_str)
    assert args["expression"] == "2+2"

    # Finish chunk: finish_reason="tool_calls"
    finish_chunk = chunks[1]
    assert finish_chunk["choices"][0]["finish_reason"] == "tool_calls"

    # Usage chunk: no choices, has usage
    usage_chunk = chunks[2]
    assert usage_chunk["choices"] == []
    assert usage_chunk["usage"] is not None
    assert usage_chunk["usage"]["prompt_tokens"] > 0
    assert usage_chunk["usage"]["completion_tokens"] > 0
    assert usage_chunk["usage"]["total_tokens"] == (
        usage_chunk["usage"]["prompt_tokens"]
        + usage_chunk["usage"]["completion_tokens"]
    )


async def test_tool_call_streaming_has_unique_tool_call_id(
    raw_client: httpx.AsyncClient,
) -> None:
    """Test that each tool call gets a unique ID."""
    ids = []
    for _ in range(3):
        async with raw_client.stream(
            "POST",
            "/chat/completions",
            json={
                "model": "gpt-4",
                "messages": [
                    {"role": "user", "content": "call tool 'calculate' with '{}'"}
                ],
                "tools": [CALCULATOR_TOOL],
                "stream": True,
            },
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: ") and line != "data: [DONE]":
                    data = json.loads(line.removeprefix("data: "))
                    if data["choices"] and data["choices"][0]["delta"].get(
                        "tool_calls"
                    ):
                        tc = data["choices"][0]["delta"]["tool_calls"][0]
                        if tc.get("id"):
                            ids.append(tc["id"])

    assert len(ids) == 3
    assert len(set(ids)) == 3, "Tool call IDs should be unique"


async def test_tool_call_non_streaming(raw_client: httpx.AsyncClient) -> None:
    """Test non-streaming tool call response using trigger phrase arguments."""
    response = await raw_client.post(
        "/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [
                {
                    "role": "user",
                    "content": "call tool 'calculate' with '{\"expression\": \"2+2\"}'",
                },
            ],
            "tools": [CALCULATOR_TOOL],
            "stream": False,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["object"] == "chat.completion"
    assert data["model"] == "gpt-4"
    assert len(data["choices"]) == 1
    choice = data["choices"][0]
    assert choice["finish_reason"] == "tool_calls"
    assert choice["message"]["role"] == "assistant"
    assert choice["message"]["content"] is None
    assert len(choice["message"]["tool_calls"]) == 1

    tool_call = choice["message"]["tool_calls"][0]
    assert tool_call["id"].startswith("call_")
    assert tool_call["type"] == "function"
    assert tool_call["function"]["name"] == "calculate"

    # Arguments come from config, not from user message
    args = json.loads(tool_call["function"]["arguments"])
    assert args["expression"] == "2+2"


# ============================================================================
# Tool Call - Follow-up Request (tool result present)
# ============================================================================


async def test_tool_call_does_not_fire_when_last_message_is_tool_result(
    raw_client: httpx.AsyncClient,
) -> None:
    """In an agentic loop ToolCallStrategy returns the tool result as a text response.

    History: user(trigger) → assistant(tool_call) → tool(result)
    The last non-system message is 'tool', so the strategy should return a text
    response with the tool result content instead of another tool call.
    """
    response = await raw_client.post(
        "/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [
                {
                    "role": "user",
                    "content": "call tool 'calculate' with '{\"expression\": \"2+2\"}'",
                },
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_abc123",
                            "type": "function",
                            "function": {
                                "name": "calculate",
                                "arguments": '{"expression": "2+2"}',
                            },
                        }
                    ],
                },
                {
                    "role": "tool",
                    "content": "4",
                    "tool_call_id": "call_abc123",
                },
            ],
            "tools": [CALCULATOR_TOOL],
            "stream": False,
        },
    )

    assert response.status_code == 200
    data = response.json()
    # ToolCallStrategy returns the tool result as a text response, not another tool call.
    assert len(data["choices"]) == 1
    choice = data["choices"][0]
    assert choice["finish_reason"] == "stop"
    assert choice["message"]["content"] == "last tool call result is 4"
    assert choice["message"].get("tool_calls") is None


async def test_tool_call_does_not_fire_when_last_message_is_assistant(
    raw_client: httpx.AsyncClient,
) -> None:
    """In an agentic loop the ToolCallStrategy must NOT re-trigger when the last
    message is an assistant message (e.g. after the model replied with text).

    History: user(trigger) → assistant(text reply)
    """
    response = await raw_client.post(
        "/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [
                {
                    "role": "user",
                    "content": "call tool 'calculate' with '{\"expression\": \"2+2\"}'",
                },
                {
                    "role": "assistant",
                    "content": "The result is 4.",
                },
            ],
            "tools": [CALCULATOR_TOOL],
            "stream": False,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["choices"] == [], (
        "ToolCallStrategy should not fire when the last message is from the assistant"
    )


# ============================================================================
# Tool ignored when not in config
# ============================================================================


async def test_tool_call_unconfigured_tool_returns_warning(
    raw_client: httpx.AsyncClient,
) -> None:
    """Test that unconfigured tools return a warning text message."""
    unknown_tool = {
        "type": "function",
        "function": {
            "name": "unknown_func",
            "parameters": {
                "type": "object",
                "properties": {"x": {"type": "string"}},
            },
        },
    }
    response = await raw_client.post(
        "/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello world"}],
            "tools": [unknown_tool],
            "stream": False,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert (
        data["choices"] == []
    )  # no trigger phrase → ToolCallStrategy falls through → empty


# ============================================================================
# Tool picks only configured tools
# ============================================================================


async def test_tool_call_picks_configured_tool(raw_client: httpx.AsyncClient) -> None:
    """Test that multiple trigger lines each produce a separate tool call choice."""
    response = await raw_client.post(
        "/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "call tool 'calculate' with '{\"expression\": \"2+2\"}'"
                        "\ncall tool 'search' with '{\"query\": \"test search\"}'"
                    ),
                }
            ],
            "tools": [CALCULATOR_TOOL, SEARCH_TOOL],
            "stream": False,
        },
    )

    assert response.status_code == 200
    data = response.json()
    # Both trigger lines fire, each becomes its own choice
    assert len(data["choices"]) == 2
    assert (
        data["choices"][0]["message"]["tool_calls"][0]["function"]["name"]
        == "calculate"
    )
    assert (
        data["choices"][1]["message"]["tool_calls"][0]["function"]["name"] == "search"
    )


# ============================================================================
# No strategies config - falls back to MirrorStrategy
# ============================================================================


async def test_tool_call_without_config_returns_mirror() -> None:
    """Test that without strategies in config, MirrorStrategy is used as default."""
    config_no_strategy: Config = {
        "models": [{"id": "gpt-4", "created": 1700000000, "owned_by": "openai"}],
        "api-key": TEST_API_KEY,
        # No strategies key → defaults to [MirrorStrategy]
    }
    app = create_app(config=config_no_strategy)
    app.dependency_overrides[get_config] = lambda: config_no_strategy

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
    ) as client:
        response = await client.post(
            "/chat/completions",
            json={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": "Hello!"}],
                "tools": [CALCULATOR_TOOL],
                "stream": False,
            },
        )

    assert response.status_code == 200
    data = response.json()
    # Mirror strategy echoes back the user message, ignoring tools
    assert data["choices"][0]["message"]["content"] == "Hello!"
    assert data["choices"][0]["finish_reason"] == "stop"


# ============================================================================
# Normal text streaming still works
# ============================================================================


async def test_normal_streaming_without_tools() -> None:
    """Test that normal text streaming still works when no tools are present."""
    mirror_config: Config = {
        "models": [{"id": "gpt-4", "created": 1700000000, "owned_by": "openai"}],
        "api-key": TEST_API_KEY,
    }
    app = create_app(config=mirror_config)
    app.dependency_overrides[get_config] = lambda: mirror_config

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as http_client:
        openai_client = AsyncOpenAI(
            api_key=TEST_API_KEY,
            http_client=http_client,
            base_url="http://testserver",
        )
        user_message = "Hello world!"
        stream = await openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": user_message}],
            stream=True,
        )

        chunks = []
        async for chunk in stream:
            chunks.append(chunk)

    assert len(chunks) >= 3

    content_parts = []
    for chunk in chunks:
        if chunk.choices[0].delta.content:
            content_parts.append(chunk.choices[0].delta.content)

    assert "".join(content_parts) == user_message


# ============================================================================
# stream_options.include_usage tests
# ============================================================================


async def test_streaming_with_include_usage(raw_client: httpx.AsyncClient) -> None:
    """Test streaming includes usage chunk when stream_options.include_usage=true."""
    async with raw_client.stream(
        "POST",
        "/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": True,
            "stream_options": {"include_usage": True},
        },
    ) as response:
        chunks = []
        async for line in response.aiter_lines():
            if line.startswith("data: ") and line != "data: [DONE]":
                data = json.loads(line.removeprefix("data: "))
                chunks.append(data)

    # Find usage chunk (empty choices, has usage)
    usage_chunks = [c for c in chunks if not c["choices"] and c.get("usage")]
    assert len(usage_chunks) == 1
    assert usage_chunks[0]["usage"]["total_tokens"] > 0


async def test_streaming_without_include_usage(raw_client: httpx.AsyncClient) -> None:
    """Test streaming does not include usage chunk by default."""
    async with raw_client.stream(
        "POST",
        "/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": True,
        },
    ) as response:
        chunks = []
        async for line in response.aiter_lines():
            if line.startswith("data: ") and line != "data: [DONE]":
                data = json.loads(line.removeprefix("data: "))
                chunks.append(data)

    # No usage chunk should be present
    usage_chunks = [c for c in chunks if not c["choices"] and c.get("usage")]
    assert len(usage_chunks) == 0


# ============================================================================
# Full agentic loop: user trigger → assistant tool call → tool result
# ============================================================================


async def test_full_agentic_loop_mirrors_user_message_after_tool_result() -> None:
    """Full OpenAI function-calling loop: assert llmock's response on the second turn.

    Simulates the conversation history a real client sends after executing a tool:

    1. user      — original request containing a trigger phrase
                   ("call tool 'calculate' with '...'")
    2. assistant — tool call that llmock returned on the first turn
                   (role=assistant, content=None, tool_calls=[...])
    3. tool      — the result produced by the caller's tool executor
                   (role=tool, tool_call_id=..., content="4")

    All three messages are replayed to llmock in a single second-turn request.

    With the default composition [ErrorStrategy, ToolCallStrategy, MirrorStrategy]:
    - ErrorStrategy:    no "raise error" phrase → returns []
    - ToolCallStrategy: last non-system message is "tool" → returns "last tool call result is 4"
    - MirrorStrategy:   not reached

    Expected: a single assistant text choice whose content equals the original
    user message.  No tool_calls in the second-turn response.
    """
    full_composition_config: Config = {
        "models": [{"id": "gpt-4", "created": 1700000000, "owned_by": "openai"}],
        "api-key": TEST_API_KEY,
        "strategies": ["ErrorStrategy", "ToolCallStrategy", "MirrorStrategy"],
    }
    app = create_app(config=full_composition_config)
    app.dependency_overrides[get_config] = lambda: full_composition_config

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
    ) as client:
        user_message = "call tool 'calculate' with '{\"expression\": \"2+2\"}'"

        response = await client.post(
            "/chat/completions",
            json={
                "model": "gpt-4",
                "messages": [
                    # Turn 1 – user sent the original request with a trigger phrase
                    {"role": "user", "content": user_message},
                    # Turn 1 – llmock replied with a tool call (assistant message)
                    {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call_abc123",
                                "type": "function",
                                "function": {
                                    "name": "calculate",
                                    "arguments": '{"expression": "2+2"}',
                                },
                            }
                        ],
                    },
                    # Turn 2 – tool executor returned the result
                    {
                        "role": "tool",
                        "content": "4",
                        "tool_call_id": "call_abc123",
                    },
                ],
                "tools": [CALCULATOR_TOOL],
                "stream": False,
            },
        )

    assert response.status_code == 200
    data = response.json()

    # ToolCallStrategy handles the tool result and returns a text response
    assert len(data["choices"]) == 1
    choice = data["choices"][0]
    assert choice["finish_reason"] == "stop"
    assert choice["message"]["role"] == "assistant"
    assert choice["message"]["content"] == "last tool call result is 4"
    # No tool calls in the second-turn response
    assert choice["message"].get("tool_calls") is None
