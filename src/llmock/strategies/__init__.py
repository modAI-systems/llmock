"""Response generation strategies."""

from llmock.strategies.base import ChatCompletionStrategy, ResponseStrategy
from llmock.strategies.content_mirror import ChatMirrorStrategy, ResponseMirrorStrategy

__all__ = [
    "ChatCompletionStrategy",
    "ChatMirrorStrategy",
    "ResponseStrategy",
    "ResponseMirrorStrategy",
]
