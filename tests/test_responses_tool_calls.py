"""Tests for tool calling support in /responses."""

import json
from collections.abc import AsyncGenerator

import httpx
import pytest

from llmock.app import create_app
from llmock.config import Config, get_config

# Test API key used across all tests
TEST_API_KEY = "test-api-key"

# Responses API style tool definition
CALCULATOR_TOOL = {
    "type": "function",
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
}

SEARCH_TOOL = {
    "type": "function",
    "name": "search",
    "parameters": {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    },
}

# Config mapping for tool responses
TOOL_CALLS_CONFIG = {
    "calculate": '{"expression": "2+2"}',
    "search": '{"query": "test search"}',
}


@pytest.fixture
def test_config() -> Config:
    """Provide test config with a model and tool-calls."""
    return {
        "models": [
            {"id": "gpt-4o", "created": 1700000000, "owned_by": "openai"},
        ],
        "api-key": TEST_API_KEY,
        "strategies": ["ToolCallStrategy"],
        "tool-calls": TOOL_CALLS_CONFIG,
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
# Tool Call - Initial Request (no tool result yet)
# ============================================================================


async def test_responses_tool_call_non_streaming(client: httpx.AsyncClient) -> None:
    """Test non-streaming tool call response via Responses API."""
    response = await client.post(
        "/responses",
        json={
            "model": "gpt-4o",
            "input": [{"role": "user", "content": "Calculate 6*7"}],
            "tools": [CALCULATOR_TOOL],
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["object"] == "response"
    assert data["status"] == "completed"
    assert data["model"] == "gpt-4o"

    # Output should be a function_call item, not a message
    assert len(data["output"]) == 1
    output = data["output"][0]
    assert output["type"] == "function_call"
    assert output["name"] == "calculate"
    assert output["call_id"].startswith("call_")
    assert output["status"] == "completed"

    # Arguments come from config
    args = json.loads(output["arguments"])
    assert args["expression"] == "2+2"

    # Usage should be present
    assert data["usage"]["total_tokens"] > 0


async def test_responses_tool_call_streaming(client: httpx.AsyncClient) -> None:
    """Test streaming tool call response via Responses API."""
    async with client.stream(
        "POST",
        "/responses",
        json={
            "model": "gpt-4o",
            "input": [{"role": "user", "content": "Calculate 6*7"}],
            "tools": [CALCULATOR_TOOL],
            "stream": True,
        },
    ) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        events: list[tuple[str, dict]] = []
        current_event = None
        async for line in response.aiter_lines():
            line = line.strip()
            if line.startswith("event:"):
                current_event = line.removeprefix("event:").strip()
            elif line.startswith("data:") and current_event:
                data = json.loads(line.removeprefix("data:").strip())
                events.append((current_event, data))

    event_types = [e[0] for e in events]

    # Verify key events are present
    assert "response.created" in event_types
    assert "response.in_progress" in event_types
    assert "response.output_item.added" in event_types
    assert "response.function_call_arguments.delta" in event_types
    assert "response.function_call_arguments.done" in event_types
    assert "response.output_item.done" in event_types
    assert "response.completed" in event_types

    # Check output_item.added is a function_call
    added_event = next(e[1] for e in events if e[0] == "response.output_item.added")
    assert added_event["item"]["type"] == "function_call"
    assert added_event["item"]["name"] == "calculate"
    assert added_event["item"]["call_id"].startswith("call_")

    # Check arguments delta - from config
    delta_event = next(
        e[1] for e in events if e[0] == "response.function_call_arguments.delta"
    )
    args = json.loads(delta_event["delta"])
    assert args["expression"] == "2+2"

    # Check arguments done
    done_event = next(
        e[1] for e in events if e[0] == "response.function_call_arguments.done"
    )
    args = json.loads(done_event["arguments"])
    assert args["expression"] == "2+2"

    # Check completed event has usage
    completed_event = next(e[1] for e in events if e[0] == "response.completed")
    assert completed_event["response"]["usage"]["total_tokens"] > 0
    assert completed_event["response"]["output"][0]["type"] == "function_call"


async def test_responses_tool_call_unique_ids(client: httpx.AsyncClient) -> None:
    """Test that each tool call gets a unique call_id."""
    call_ids = []
    for _ in range(3):
        response = await client.post(
            "/responses",
            json={
                "model": "gpt-4o",
                "input": "test",
                "tools": [CALCULATOR_TOOL],
            },
        )
        data = response.json()
        call_ids.append(data["output"][0]["call_id"])

    assert len(set(call_ids)) == 3, "Tool call IDs should be unique"


# ============================================================================
# Normal responses still work (no tools)
# ============================================================================


async def test_responses_normal_without_tools() -> None:
    """Test that normal responses still work when no tools present."""
    mirror_config: Config = {
        "models": [{"id": "gpt-4o", "created": 1700000000, "owned_by": "openai"}],
        "api-key": TEST_API_KEY,
    }
    app = create_app(config=mirror_config)
    app.dependency_overrides[get_config] = lambda: mirror_config

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
    ) as mirror_client:
        response = await mirror_client.post(
            "/responses",
            json={
                "model": "gpt-4o",
                "input": "Hello world!",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["output"][0]["type"] == "message"
    assert data["output"][0]["content"][0]["text"] == "Hello world!"


# ============================================================================
# Tool with string input
# ============================================================================


async def test_responses_tool_call_with_string_input(
    client: httpx.AsyncClient,
) -> None:
    """Test tool call when input is a simple string."""
    response = await client.post(
        "/responses",
        json={
            "model": "gpt-4o",
            "input": "Calculate 6*7",
            "tools": [CALCULATOR_TOOL],
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["output"][0]["type"] == "function_call"
    args = json.loads(data["output"][0]["arguments"])
    assert args["expression"] == "2+2"


# ============================================================================
# Unconfigured tool returns warning message
# ============================================================================


async def test_responses_unconfigured_tool_returns_warning(
    client: httpx.AsyncClient,
) -> None:
    """Test that unconfigured tools return a warning text message."""
    unknown_tool = {
        "type": "function",
        "name": "unknown_func",
        "parameters": {
            "type": "object",
            "properties": {"x": {"type": "string"}},
        },
    }
    response = await client.post(
        "/responses",
        json={
            "model": "gpt-4o",
            "input": "Hello world!",
            "tools": [unknown_tool],
        },
    )

    assert response.status_code == 200
    data = response.json()
    # No configured tools matched — output contains an empty message
    assert data["output"][0]["type"] == "message"
    assert data["output"][0]["content"][0]["text"] == ""


# ============================================================================
# Tool picks only configured tools
# ============================================================================


async def test_responses_tool_call_picks_configured_tool(
    client: httpx.AsyncClient,
) -> None:
    """Test that only tools in config are called."""
    response = await client.post(
        "/responses",
        json={
            "model": "gpt-4o",
            "input": "find something",
            "tools": [CALCULATOR_TOOL, SEARCH_TOOL],
        },
    )

    assert response.status_code == 200
    data = response.json()
    # First configured tool (calculate) is the first in the output
    assert data["output"][0]["name"] == "calculate"
