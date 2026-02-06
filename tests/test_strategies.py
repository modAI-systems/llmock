"""Tests for chat response strategies."""

from llmock.schemas.chat import ChatCompletionRequest, ChatMessageRequest
from llmock.strategies import ChatStrategy, ContentMirrorStrategy


def test_content_mirror_strategy_returns_last_user_message() -> None:
    """Test that ContentMirrorStrategy returns the last user message."""
    strategy = ContentMirrorStrategy()
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


def test_content_mirror_strategy_no_user_message() -> None:
    """Test ContentMirrorStrategy with no user message returns default."""
    strategy = ContentMirrorStrategy()
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[
            ChatMessageRequest(role="system", content="You are helpful."),
        ],
    )

    result = strategy.generate_response(request)

    assert result == "No user message provided."


def test_content_mirror_strategy_empty_content() -> None:
    """Test ContentMirrorStrategy skips messages with empty content."""
    strategy = ContentMirrorStrategy()
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[
            ChatMessageRequest(role="user", content="Real message"),
            ChatMessageRequest(role="user", content=None),
        ],
    )

    result = strategy.generate_response(request)

    assert result == "Real message"


def test_content_mirror_strategy_implements_protocol() -> None:
    """Test that ContentMirrorStrategy implements ChatStrategy protocol."""
    strategy: ChatStrategy = ContentMirrorStrategy()
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[
            ChatMessageRequest(role="user", content="Hello"),
        ],
    )

    # This should work without type errors since it implements the protocol
    result = strategy.generate_response(request)
    assert result == "Hello"
