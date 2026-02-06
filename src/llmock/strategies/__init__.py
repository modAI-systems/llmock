"""Chat response strategies."""

from llmock.strategies.base import ChatStrategy
from llmock.strategies.content_mirror import ContentMirrorStrategy

__all__ = ["ChatStrategy", "ContentMirrorStrategy"]
