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


def test_chat_tool_call_strategy_generates_tool_call() -> None:
    """Test that the trigger phrase produces a tool_call response."""
    strategy = ChatToolCallStrategy(config={})
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[
            ChatMessageRequest(
                role="user",
                content="call tool 'calculate' with '{\"expression\": \"2+2\"}'",
            )
        ],
        tools=[CALCULATOR_TOOL],
    )

    result = strategy.generate_response(request)

    assert len(result) == 1
    assert result[0].type == StrategyResponseType.TOOL_CALL
    assert result[0].name == "calculate"
    assert result[0].content == '{"expression": "2+2"}'


def test_chat_tool_call_strategy_no_trigger_phrase_returns_empty() -> None:
    """Test that a message without the trigger phrase returns empty list."""
    strategy = ChatToolCallStrategy(config={})
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[ChatMessageRequest(role="user", content="Calculate 6*7")],
        tools=[CALCULATOR_TOOL],
    )

    result = strategy.generate_response(request)

    assert result == []


def test_chat_tool_call_strategy_tool_not_in_request_returns_empty() -> None:
    """Test that trigger for a tool absent from request.tools is skipped."""
    strategy = ChatToolCallStrategy(config={})
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[
            ChatMessageRequest(role="user", content="call tool 'calculate' with '{}'")
        ],
        tools=[SEARCH_TOOL],  # only search, not calculate
    )

    result = strategy.generate_response(request)

    assert result == []


def test_chat_tool_call_strategy_multiple_trigger_lines() -> None:
    """Test that multiple trigger lines each produce a tool response."""
    strategy = ChatToolCallStrategy(config={})
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[
            ChatMessageRequest(
                role="user",
                content=(
                    "call tool 'calculate' with '{\"expression\": \"2+2\"}'\n"
                    "call tool 'search' with '{\"query\": \"test search\"}'"
                ),
            )
        ],
        tools=[CALCULATOR_TOOL, SEARCH_TOOL],
    )

    result = strategy.generate_response(request)

    assert len(result) == 2
    assert result[0].type == StrategyResponseType.TOOL_CALL
    assert result[0].name == "calculate"
    assert result[1].type == StrategyResponseType.TOOL_CALL
    assert result[1].name == "search"


def test_chat_tool_call_strategy_only_matching_tool_fires() -> None:
    """Test that only the tool named in the trigger phrase fires."""
    strategy = ChatToolCallStrategy(config={})
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[
            ChatMessageRequest(
                role="user",
                content="call tool 'search' with '{\"query\": \"hi\"}'",
            )
        ],
        tools=[CALCULATOR_TOOL, SEARCH_TOOL],
    )

    result = strategy.generate_response(request)

    assert len(result) == 1
    assert result[0].name == "search"


def test_chat_tool_call_strategy_no_tools_in_request() -> None:
    """Test with no tools in request returns empty list even with trigger phrase."""
    strategy = ChatToolCallStrategy(config={})
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[
            ChatMessageRequest(role="user", content="call tool 'calculate' with '{}'")
        ],
    )

    result = strategy.generate_response(request)

    assert result == []


def test_chat_tool_call_strategy_empty_args_normalised() -> None:
    """Test that an empty args string is normalised to '{}'."""
    strategy = ChatToolCallStrategy(config={})
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[
            ChatMessageRequest(role="user", content="call tool 'calculate' with ''")
        ],
        tools=[CALCULATOR_TOOL],
    )

    result = strategy.generate_response(request)

    assert len(result) == 1
    assert result[0].content == "{}"


def test_chat_tool_call_strategy_last_message_is_tool_role() -> None:
    """Strategy must NOT fire when the last non-system message has role 'tool'.

    In an agentic loop the conversation history looks like:
        user(trigger) → assistant(tool_call) → tool(result)
    The trigger phrase still lives in the user message, but the last turn
    belongs to the tool.  Firing again would create an infinite loop.
    """
    strategy = ChatToolCallStrategy(config={})
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[
            ChatMessageRequest(
                role="user",
                content="call tool 'calculate' with '{}'",
            ),
            ChatMessageRequest(role="assistant", content=None),
            ChatMessageRequest(role="tool", content="4"),
        ],
        tools=[CALCULATOR_TOOL],
    )

    result = strategy.generate_response(request)

    # The last non-system message is 'tool' → strategy must fall through.
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
    """Test tool_call response when trigger phrase is present."""
    strategy = ResponseToolCallStrategy(config={})
    request = ResponseCreateRequest(
        model="gpt-4o",
        input=[
            SimpleInputMessage(
                role="user",
                content="call tool 'calculate' with '{\"expression\": \"2+2\"}'",
            )
        ],
        tools=[RESPONSES_CALCULATOR_TOOL],
    )

    result = strategy.generate_response(request)

    assert len(result) == 1
    assert result[0].type == StrategyResponseType.TOOL_CALL
    assert result[0].name == "calculate"
    assert result[0].content == '{"expression": "2+2"}'


def test_response_tool_call_strategy_tool_not_in_request_returns_empty() -> None:
    """Test that trigger for a tool absent from request.tools is skipped."""
    strategy = ResponseToolCallStrategy(config={})
    request = ResponseCreateRequest(
        model="gpt-4o",
        input="call tool 'calculate' with '{}'",
        tools=[RESPONSES_SEARCH_TOOL],  # only search in request, not calculate
    )

    result = strategy.generate_response(request)

    assert result == []


def test_response_tool_call_strategy_string_input() -> None:
    """Test tool_call with string input and trigger phrase works."""
    strategy = ResponseToolCallStrategy(config={})
    request = ResponseCreateRequest(
        model="gpt-4o",
        input="call tool 'calculate' with '{}'",
        tools=[RESPONSES_CALCULATOR_TOOL],
    )

    result = strategy.generate_response(request)

    assert len(result) == 1
    assert result[0].type == StrategyResponseType.TOOL_CALL


def test_response_tool_call_strategy_multiple_trigger_lines() -> None:
    """Test that multiple trigger lines each produce a tool response."""
    strategy = ResponseToolCallStrategy(config={})
    request = ResponseCreateRequest(
        model="gpt-4o",
        input=(
            "call tool 'calculate' with '{}'\n"
            "call tool 'search' with '{\"query\": \"hi\"}'"
        ),
        tools=[RESPONSES_CALCULATOR_TOOL, RESPONSES_SEARCH_TOOL],
    )

    result = strategy.generate_response(request)

    assert len(result) == 2
    assert result[0].name == "calculate"
    assert result[1].name == "search"


def test_response_tool_call_strategy_no_trigger_phrase_returns_empty() -> None:
    """Test that a message without the trigger phrase returns empty list."""
    strategy = ResponseToolCallStrategy(config={})
    request = ResponseCreateRequest(
        model="gpt-4o",
        input="Calculate 6*7",
        tools=[RESPONSES_CALCULATOR_TOOL],
    )

    result = strategy.generate_response(request)

    assert result == []


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
