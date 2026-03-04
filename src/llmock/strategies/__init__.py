"""Response generation strategies."""

from llmock.strategies.base import (
    ChatCompletionStrategy,
    ResponseStrategy,
    StrategyResponse,
    StrategyResponseType,
    error_response,
    text_response,
    tool_response,
)
from llmock.strategies.strategy_composition import (
    ChatCompositionStrategy,
    ResponseCompositionStrategy,
)
from llmock.strategies.strategy_content_mirror import (
    ChatMirrorStrategy,
    ResponseMirrorStrategy,
)
from llmock.strategies.strategy_error import (
    ChatErrorStrategy,
    ResponseErrorStrategy,
)
from llmock.strategies.factory import (
    create_chat_strategy,
    create_response_strategy,
)
from llmock.strategies.strategy_tool_call import (
    ChatToolCallStrategy,
    ResponseToolCallStrategy,
)

__all__ = [
    "ChatCompositionStrategy",
    "ChatCompletionStrategy",
    "ChatErrorStrategy",
    "ChatMirrorStrategy",
    "ChatToolCallStrategy",
    "ResponseCompositionStrategy",
    "ResponseErrorStrategy",
    "ResponseStrategy",
    "ResponseMirrorStrategy",
    "ResponseToolCallStrategy",
    "StrategyResponse",
    "StrategyResponseType",
    "create_chat_strategy",
    "create_response_strategy",
    "error_response",
    "text_response",
    "tool_response",
]
