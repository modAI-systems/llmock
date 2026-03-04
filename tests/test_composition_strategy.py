"""Tests for the CompositionStrategy (priority-chain of strategies)."""

from llmock.schemas.chat import ChatCompletionRequest, ChatMessageRequest
from llmock.strategies import StrategyResponseType
from llmock.strategies.strategy_composition import (
    ChatCompositionStrategy,
)

TEST_API_KEY = "test-api-key"


# ============================================================================
# Unit tests – ChatCompositionStrategy
# ============================================================================


def test_chat_composition_error_takes_priority() -> None:
    """ErrorStrategy fires before MirrorStrategy when the message contains a trigger phrase."""
    config = {
        "strategies": ["ErrorStrategy", "MirrorStrategy"],
    }
    strategy = ChatCompositionStrategy(config)
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[
            ChatMessageRequest(
                role="user",
                content='raise error {"code": 500, "message": "Server error"}',
            )
        ],
    )
    result = strategy.generate_response(request)
    assert len(result) == 1
    assert result[0].type == StrategyResponseType.ERROR
    assert result[0].content == "Server error"


def test_chat_composition_falls_through_to_mirror() -> None:
    """ErrorStrategy returns empty for normal messages, MirrorStrategy answers."""
    config = {
        "strategies": ["ErrorStrategy", "MirrorStrategy"],
    }
    strategy = ChatCompositionStrategy(config)
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[ChatMessageRequest(role="user", content="Hello")],
    )
    result = strategy.generate_response(request)
    assert len(result) == 1
    assert result[0].type == StrategyResponseType.TEXT
    assert result[0].content == "Hello"
