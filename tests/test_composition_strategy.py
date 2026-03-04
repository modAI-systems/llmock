"""Tests for the CompositionStrategy (priority-chain of strategies)."""

from llmock.app import create_app
from llmock.config import get_config
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
    """ErrorStrategy fires before MirrorStrategy when the message triggers it."""
    config = {
        "strategies": ["ErrorStrategy", "MirrorStrategy"],
        "error-messages": {
            "boom": {
                "status-code": 500,
                "message": "Server error",
                "type": "server_error",
                "code": "server_error",
            },
        },
    }
    strategy = ChatCompositionStrategy(config)
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[ChatMessageRequest(role="user", content="boom")],
    )
    result = strategy.generate_response(request)
    assert len(result) == 1
    assert result[0].type == StrategyResponseType.ERROR
    assert result[0].content == "Server error"


def test_chat_composition_falls_through_to_mirror() -> None:
    """ErrorStrategy returns empty for normal messages, MirrorStrategy answers."""
    config = {
        "strategies": ["ErrorStrategy", "MirrorStrategy"],
        "error-messages": {
            "boom": {
                "status-code": 500,
                "message": "Server error",
                "type": "server_error",
                "code": "server_error",
            },
        },
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
