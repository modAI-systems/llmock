"""Tests for response generation strategies."""

from llmock.schemas.chat import ChatCompletionRequest, ChatMessageRequest
from llmock.schemas.responses import ResponseCreateRequest, SimpleInputMessage
from llmock.strategies import (
    ChatMirrorStrategy,
    ChatCompletionStrategy,
    ResponseMirrorStrategy,
    ResponseStrategy,
)


# ============================================================================
# ChatMirrorStrategy Tests
# ============================================================================


def test_chat_mirror_strategy_returns_last_user_message() -> None:
    """Test that ChatMirrorStrategy returns the last user message."""
    strategy = ChatMirrorStrategy()
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

    assert result == "Second message"


def test_chat_mirror_strategy_no_user_message() -> None:
    """Test ChatMirrorStrategy with no user message returns default."""
    strategy = ChatMirrorStrategy()
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[
            ChatMessageRequest(role="system", content="You are helpful."),
        ],
    )

    result = strategy.generate_response(request)

    assert result == "No user message provided."


def test_chat_mirror_strategy_empty_content() -> None:
    """Test ChatMirrorStrategy skips messages with empty content."""
    strategy = ChatMirrorStrategy()
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[
            ChatMessageRequest(role="user", content="Real message"),
            ChatMessageRequest(role="user", content=None),
        ],
    )

    result = strategy.generate_response(request)

    assert result == "Real message"


def test_chat_mirror_strategy_implements_protocol() -> None:
    """Test that ChatMirrorStrategy implements ChatStrategy protocol."""
    strategy: ChatCompletionStrategy = ChatMirrorStrategy()
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[
            ChatMessageRequest(role="user", content="Hello"),
        ],
    )

    result = strategy.generate_response(request)
    assert result == "Hello"


# ============================================================================
# ResponseMirrorStrategy Tests
# ============================================================================


def test_response_mirror_strategy_string_input() -> None:
    """Test ResponseMirrorStrategy with simple string input."""
    strategy = ResponseMirrorStrategy()
    request = ResponseCreateRequest(
        model="gpt-4o",
        input="Hello, world!",
    )

    result = strategy.generate_response(request)

    assert result == "Hello, world!"


def test_response_mirror_strategy_message_list() -> None:
    """Test ResponseMirrorStrategy with message list input."""
    strategy = ResponseMirrorStrategy()
    request = ResponseCreateRequest(
        model="gpt-4o",
        input=[
            SimpleInputMessage(role="user", content="First message"),
            SimpleInputMessage(role="assistant", content="Response"),
            SimpleInputMessage(role="user", content="Second message"),
        ],
    )

    result = strategy.generate_response(request)

    assert result == "Second message"


def test_response_mirror_strategy_no_user_message() -> None:
    """Test ResponseMirrorStrategy with no user message returns default."""
    strategy = ResponseMirrorStrategy()
    request = ResponseCreateRequest(
        model="gpt-4o",
        input=[
            SimpleInputMessage(role="assistant", content="I'm an assistant"),
        ],
    )

    result = strategy.generate_response(request)

    assert result == "No user input provided."


def test_response_mirror_strategy_implements_protocol() -> None:
    """Test that ResponseMirrorStrategy implements ResponseStrategy protocol."""
    strategy: ResponseStrategy = ResponseMirrorStrategy()
    request = ResponseCreateRequest(
        model="gpt-4o",
        input="Test input",
    )

    result = strategy.generate_response(request)
    assert result == "Test input"
