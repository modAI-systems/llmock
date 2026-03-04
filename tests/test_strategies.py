"""Tests for response generation strategies."""

from llmock.schemas.chat import ChatCompletionRequest, ChatMessageRequest
from llmock.schemas.responses import (
    ResponseCreateRequest,
    SimpleInputMessage,
)
from llmock.strategies import (
    ChatCompletionStrategy,
    ChatMirrorStrategy,
    ChatToolCallStrategy,
    ResponseMirrorStrategy,
    ResponseStrategy,
    ResponseToolCallStrategy,
    StrategyResponseType,
    text_response,
    tool_response,
)


# ============================================================================
# ChatMirrorStrategy Tests
# ============================================================================


def test_chat_mirror_strategy_returns_last_user_message() -> None:
    """Test that ChatMirrorStrategy returns the last user message."""
    strategy = ChatMirrorStrategy({})
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[
            ChatMessageRequest(role="system", content="You are helpful."),
            ChatMessageRequest(role="user", content="First message"),
            ChatMessageRequest(role="assistant", content="Response"),
            ChatMessageRequest(role="user", content="Second message"),
        ],
    )

    result = strategy.generate_response(request)

    assert len(result) == 1
    assert result[0].type == StrategyResponseType.TEXT
    assert result[0].content == "Second message"


def test_chat_mirror_strategy_no_user_message() -> None:
    """Test ChatMirrorStrategy with no user message returns default."""
    strategy = ChatMirrorStrategy({})
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[
            ChatMessageRequest(role="system", content="You are helpful."),
        ],
    )

    result = strategy.generate_response(request)

    assert len(result) == 1
    assert result[0].type == StrategyResponseType.TEXT
    assert result[0].content == "No user message provided."


def test_chat_mirror_strategy_empty_content() -> None:
    """Test ChatMirrorStrategy skips messages with empty content."""
    strategy = ChatMirrorStrategy({})
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[
            ChatMessageRequest(role="user", content="Real message"),
            ChatMessageRequest(role="user", content=None),
        ],
    )

    result = strategy.generate_response(request)

    assert len(result) == 1
    assert result[0].content == "Real message"


def test_chat_mirror_strategy_implements_protocol() -> None:
    """Test that ChatMirrorStrategy implements ChatCompletionStrategy protocol."""
    strategy: ChatCompletionStrategy = ChatMirrorStrategy({})
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[
            ChatMessageRequest(role="user", content="Hello"),
        ],
    )

    result = strategy.generate_response(request)
    assert isinstance(result, list)
    assert result[0].content == "Hello"


# ============================================================================
# ResponseMirrorStrategy Tests
# ============================================================================


def test_response_mirror_strategy_string_input() -> None:
    """Test ResponseMirrorStrategy with simple string input."""
    strategy = ResponseMirrorStrategy({})
    request = ResponseCreateRequest(
        model="gpt-4o",
        input="Hello, world!",
    )

    result = strategy.generate_response(request)

    assert len(result) == 1
    assert result[0].type == StrategyResponseType.TEXT
    assert result[0].content == "Hello, world!"


def test_response_mirror_strategy_message_list() -> None:
    """Test ResponseMirrorStrategy with message list input."""
    strategy = ResponseMirrorStrategy({})
    request = ResponseCreateRequest(
        model="gpt-4o",
        input=[
            SimpleInputMessage(role="user", content="First message"),
            SimpleInputMessage(role="assistant", content="Response"),
            SimpleInputMessage(role="user", content="Second message"),
        ],
    )

    result = strategy.generate_response(request)

    assert len(result) == 1
    assert result[0].content == "Second message"


def test_response_mirror_strategy_no_user_message() -> None:
    """Test ResponseMirrorStrategy with no user message returns default."""
    strategy = ResponseMirrorStrategy({})
    request = ResponseCreateRequest(
        model="gpt-4o",
        input=[
            SimpleInputMessage(role="assistant", content="I'm an assistant"),
        ],
    )

    result = strategy.generate_response(request)

    assert len(result) == 1
    assert result[0].content == "No user input provided."


def test_response_mirror_strategy_implements_protocol() -> None:
    """Test that ResponseMirrorStrategy implements ResponseStrategy protocol."""
    strategy: ResponseStrategy = ResponseMirrorStrategy({})
    request = ResponseCreateRequest(
        model="gpt-4o",
        input="Test input",
    )

    result = strategy.generate_response(request)
    assert isinstance(result, list)
    assert result[0].content == "Test input"


# ============================================================================
# ChatToolCallStrategy Tests
# ============================================================================

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

TOOL_CALLS_CONFIG = {
    "calculate": '{"expression": "2+2"}',
    "search": '{"query": "test search"}',
}


def test_chat_tool_call_strategy_generates_tool_call() -> None:
    """Test that the strategy generates a tool_call response for configured tools."""
    strategy = ChatToolCallStrategy(config={"tool-calls": TOOL_CALLS_CONFIG})
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[ChatMessageRequest(role="user", content="Calculate 6*7")],
        tools=[CALCULATOR_TOOL],
    )

    result = strategy.generate_response(request)

    assert len(result) == 1
    assert result[0].type == StrategyResponseType.TOOL_CALL
    assert result[0].name == "calculate"
    assert result[0].content == '{"expression": "2+2"}'


def test_chat_tool_call_strategy_ignores_unconfigured_tools() -> None:
    """Test that tools not in config return empty list."""
    strategy = ChatToolCallStrategy(
        config={"tool-calls": {"search": '{"query": "test"}'}}
    )
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[ChatMessageRequest(role="user", content="Calculate 6*7")],
        tools=[CALCULATOR_TOOL],
    )

    result = strategy.generate_response(request)

    assert result == []


def test_chat_tool_call_strategy_multiple_tools() -> None:
    """Test that strategy generates responses for all configured tools."""
    strategy = ChatToolCallStrategy(config={"tool-calls": TOOL_CALLS_CONFIG})
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[ChatMessageRequest(role="user", content="test")],
        tools=[CALCULATOR_TOOL, SEARCH_TOOL],
    )

    result = strategy.generate_response(request)

    assert len(result) == 2
    assert result[0].type == StrategyResponseType.TOOL_CALL
    assert result[0].name == "calculate"
    assert result[1].type == StrategyResponseType.TOOL_CALL
    assert result[1].name == "search"


def test_chat_tool_call_strategy_partial_match() -> None:
    """Test only tools in config are matched, others skipped."""
    strategy = ChatToolCallStrategy(
        config={"tool-calls": {"search": '{"query": "hi"}'}}
    )
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[ChatMessageRequest(role="user", content="test")],
        tools=[CALCULATOR_TOOL, SEARCH_TOOL],
    )

    result = strategy.generate_response(request)

    assert len(result) == 1
    assert result[0].name == "search"


def test_chat_tool_call_strategy_empty_config() -> None:
    """Test with empty tool_calls config returns empty list."""
    strategy = ChatToolCallStrategy(config={"tool-calls": {}})
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[ChatMessageRequest(role="user", content="test")],
        tools=[CALCULATOR_TOOL],
    )

    result = strategy.generate_response(request)

    assert result == []


def test_chat_tool_call_strategy_no_tools_in_request() -> None:
    """Test with no tools in request returns empty list."""
    strategy = ChatToolCallStrategy(config={"tool-calls": TOOL_CALLS_CONFIG})
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[ChatMessageRequest(role="user", content="Hello")],
    )

    result = strategy.generate_response(request)

    assert result == []


# ============================================================================
# ResponseToolCallStrategy Tests
# ============================================================================

RESPONSES_CALCULATOR_TOOL = {
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

RESPONSES_SEARCH_TOOL = {
    "type": "function",
    "name": "search",
    "parameters": {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    },
}


def test_response_tool_call_strategy_generates_tool_call() -> None:
    """Test tool_call response for configured tools."""
    strategy = ResponseToolCallStrategy(config={"tool-calls": TOOL_CALLS_CONFIG})
    request = ResponseCreateRequest(
        model="gpt-4o",
        input=[SimpleInputMessage(role="user", content="Calculate 6*7")],
        tools=[RESPONSES_CALCULATOR_TOOL],
    )

    result = strategy.generate_response(request)

    assert len(result) == 1
    assert result[0].type == StrategyResponseType.TOOL_CALL
    assert result[0].name == "calculate"
    assert result[0].content == '{"expression": "2+2"}'


def test_response_tool_call_strategy_ignores_unconfigured_tools() -> None:
    """Test that tools not in config return empty list."""
    strategy = ResponseToolCallStrategy(
        config={"tool-calls": {"search": '{"query": "x"}'}}
    )
    request = ResponseCreateRequest(
        model="gpt-4o",
        input="Calculate 6*7",
        tools=[RESPONSES_CALCULATOR_TOOL],
    )

    result = strategy.generate_response(request)

    assert result == []


def test_response_tool_call_strategy_string_input() -> None:
    """Test tool_call with string input works."""
    strategy = ResponseToolCallStrategy(config={"tool-calls": TOOL_CALLS_CONFIG})
    request = ResponseCreateRequest(
        model="gpt-4o",
        input="Calculate 6*7",
        tools=[RESPONSES_CALCULATOR_TOOL],
    )

    result = strategy.generate_response(request)

    assert len(result) == 1
    assert result[0].type == StrategyResponseType.TOOL_CALL


def test_response_tool_call_strategy_multiple_tools() -> None:
    """Test that strategy handles multiple matching tools."""
    strategy = ResponseToolCallStrategy(config={"tool-calls": TOOL_CALLS_CONFIG})
    request = ResponseCreateRequest(
        model="gpt-4o",
        input="test",
        tools=[RESPONSES_CALCULATOR_TOOL, RESPONSES_SEARCH_TOOL],
    )

    result = strategy.generate_response(request)

    assert len(result) == 2
    assert result[0].name == "calculate"
    assert result[1].name == "search"


def test_strategy_response_dataclass() -> None:
    """Test StrategyResponse dataclass creation."""
    text_resp = text_response("Hello")
    assert text_resp.type == StrategyResponseType.TEXT
    assert text_resp.content == "Hello"
    assert text_resp.name is None

    tool_resp = tool_response('{"x": 1}', "my_func")
    assert tool_resp.type == StrategyResponseType.TOOL_CALL
    assert tool_resp.content == '{"x": 1}'
    assert tool_resp.name == "my_func"
