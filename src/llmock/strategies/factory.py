"""Strategy factory - creates the correct strategy based on config.

Reads the ``response-strategy`` field from config.yaml and instantiates
the matching strategy class. Falls back to the mirror strategy when no
strategy is configured or the name is unrecognised.
"""

from typing import Any

from llmock.strategies.base import ChatCompletionStrategy, ResponseStrategy
from llmock.strategies.strategy_content_mirror import (
    ChatMirrorStrategy,
    ResponseMirrorStrategy,
)
from llmock.strategies.strategy_error import (
    ChatErrorStrategy,
    ResponseErrorStrategy,
)
from llmock.strategies.strategy_tool_call import (
    ChatToolCallStrategy,
    ResponseToolCallStrategy,
)

# Short strategy names used in config → (ChatClass, ResponseClass)
_STRATEGIES: dict[str, tuple[type, type]] = {
    "ErrorStrategy": (ChatErrorStrategy, ResponseErrorStrategy),
    "MirrorStrategy": (ChatMirrorStrategy, ResponseMirrorStrategy),
    "ToolCallStrategy": (ChatToolCallStrategy, ResponseToolCallStrategy),
}


def create_chat_strategy(config: dict[str, Any]) -> ChatCompletionStrategy:
    """Create a chat completion strategy from config.

    Reads ``response-strategy`` from *config*. If the value matches a known
    strategy name, that strategy is instantiated with the full config.
    Otherwise falls back to ``ChatMirrorStrategy``.

    Args:
        config: The application config dict.

    Returns:
        A strategy implementing ``ChatCompletionStrategy``.
    """
    name = config.get("response-strategy")
    if name in _STRATEGIES:
        return _STRATEGIES[name][0](config)
    return ChatMirrorStrategy(config)


def create_response_strategy(config: dict[str, Any]) -> ResponseStrategy:
    """Create a Responses API strategy from config.

    Reads ``response-strategy`` from *config*. If the value matches a known
    strategy name, that strategy is instantiated with the full config.
    Otherwise falls back to ``ResponseMirrorStrategy``.

    Args:
        config: The application config dict.

    Returns:
        A strategy implementing ``ResponseStrategy``.
    """
    name = config.get("response-strategy")
    if name in _STRATEGIES:
        return _STRATEGIES[name][1](config)
    return ResponseMirrorStrategy(config)
