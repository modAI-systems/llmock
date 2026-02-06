"""Pydantic schemas for OpenAI API compatibility.

Request schemas are defined locally.
Response schemas (including Model) are imported from the openai library.
"""

from llmock.schemas.chat import ChatCompletionRequest, ChatMessageRequest
from llmock.schemas.models import Model, ModelList
from llmock.schemas.responses import (
    Response,
    ResponseCreateRequest,
    ResponseDeleted,
    ResponseUsage,
)

__all__ = [
    "ChatCompletionRequest",
    "ChatMessageRequest",
    "Model",
    "ModelList",
    "Response",
    "ResponseCreateRequest",
    "ResponseDeleted",
    "ResponseUsage",
]
