"""Base strategy interfaces for response generation."""

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from llmock.schemas.chat import ChatCompletionRequest
from llmock.schemas.responses import ResponseCreateRequest


class StrategyResponseType(Enum):
    """The kind of response produced by a strategy."""

    TEXT = "text"
    TOOL_CALL = "tool_call"
    ERROR = "error"


@dataclass
class StrategyResponse:
    """A single response item produced by a strategy.

    Attributes:
        type: The kind of response - TEXT for plain text content,
              TOOL_CALL for a tool/function call, ERROR for an error response.
        content: The response payload. For TEXT type this is the response text.
                 For TOOL_CALL type this is the arguments JSON string.
                 For ERROR type this is the error message.
        name: The function name. Only used for TOOL_CALL type responses.
        status_code: HTTP status code. Only used for ERROR type responses.
        error_type: OpenAI error type string. Only used for ERROR type.
        error_code: OpenAI error code string. Only used for ERROR type.
    """

    type: StrategyResponseType
    content: str
    name: str | None = None
    status_code: int | None = None
    error_type: str | None = None
    error_code: str | None = None


def text_response(content: str) -> StrategyResponse:
    """Create a TEXT strategy response."""
    return StrategyResponse(type=StrategyResponseType.TEXT, content=content)


def tool_response(content: str, name: str) -> StrategyResponse:
    """Create a TOOL_CALL strategy response."""
    return StrategyResponse(
        type=StrategyResponseType.TOOL_CALL, content=content, name=name
    )


def error_response(
    message: str,
    status_code: int,
    error_type: str,
    error_code: str,
) -> StrategyResponse:
    """Create an ERROR strategy response."""
    return StrategyResponse(
        type=StrategyResponseType.ERROR,
        content=message,
        status_code=status_code,
        error_type=error_type,
        error_code=error_code,
    )


class ChatCompletionStrategy(Protocol):
    """Protocol defining the interface for chat response strategies.

    Strategies are responsible for generating a list of response items
    based on the request. They are NOT concerned with streaming vs
    non-streaming - that is handled by the endpoint.
    """

    def generate_response(
        self, request: ChatCompletionRequest
    ) -> list[StrategyResponse]:
        """Generate response items for the given chat request.

        Args:
            request: The chat completion request containing messages and parameters.

        Returns:
            A list of StrategyResponse items. Each item has a type
            ("text" or "tool_call") and content.
        """
        ...


class ResponseStrategy(Protocol):
    """Protocol defining the interface for Responses API strategies.

    Strategies are responsible for generating a list of response items
    based on the request. They are NOT concerned with streaming vs
    non-streaming - that is handled by the endpoint.
    """

    def generate_response(
        self, request: ResponseCreateRequest
    ) -> list[StrategyResponse]:
        """Generate response items for the given Responses API request.

        Args:
            request: The response create request containing input and parameters.

        Returns:
            A list of StrategyResponse items. Each item has a type
            ("text" or "tool_call") and content.
        """
        ...
