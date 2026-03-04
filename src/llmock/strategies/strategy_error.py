"""Error strategies - config-driven error response generation.

These strategies check the user's message content against a configured
mapping of error-triggering messages. When the message matches, an error
response is returned with the configured status code, message, type, and
code.

Configuration format (in config.yaml):

    error-messages:
      "Hi":
        status-code: 403
        message: "Forbidden"
        type: "forbidden_error"
        code: "forbidden"
      "rate limit test":
        status-code: 429
        message: "Rate limit exceeded"
        type: "rate_limit_error"
        code: "rate_limit_exceeded"

Each key is a message string. When a request's last user message matches
that key exactly, the strategy returns an ERROR StrategyResponse instead
of delegating to the normal response strategy.
"""

from typing import Any

from llmock.schemas.chat import ChatCompletionRequest
from llmock.utils.chat import extract_text_content
from llmock.schemas.responses import (
    InputMessage,
    InputTextContent,
    ResponseCreateRequest,
    SimpleInputMessage,
)
from llmock.strategies.base import StrategyResponse, error_response


class ChatErrorStrategy:
    """Config-driven error strategy for Chat Completions API.

    Checks the last user message content against ``error-messages`` in
    config. If found, returns an ERROR response. Otherwise returns an
    empty list (indicating no error, so the caller should proceed
    normally).
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self.error_messages: dict[str, dict[str, Any]] = config.get(
            "error-messages", {}
        )

    def generate_response(
        self, request: ChatCompletionRequest
    ) -> list[StrategyResponse]:
        """Check if the last user message triggers an error response."""
        content = _extract_last_chat_message(request)
        return _check_error_message(content, self.error_messages)


class ResponseErrorStrategy:
    """Config-driven error strategy for the Responses API.

    Same behavior as ChatErrorStrategy but operates on Responses API
    request types.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self.error_messages: dict[str, dict[str, Any]] = config.get(
            "error-messages", {}
        )

    def generate_response(
        self, request: ResponseCreateRequest
    ) -> list[StrategyResponse]:
        """Check if the input message triggers an error response."""
        content = _extract_last_response_message(request)
        return _check_error_message(content, self.error_messages)


def _extract_last_chat_message(request: ChatCompletionRequest) -> str | None:
    """Extract the content of the last user message from a chat request."""
    for message in reversed(request.messages):
        if message.role == "user" and message.content:
            return extract_text_content(message.content)
    return None


def _extract_last_response_message(request: ResponseCreateRequest) -> str | None:
    """Extract the last user input text from a responses request."""
    if isinstance(request.input, str):
        return request.input

    for item in reversed(request.input):
        if isinstance(item, SimpleInputMessage) and item.role == "user":
            return extract_text_content(item.content)
        if isinstance(item, InputMessage) and item.role == "user":
            if isinstance(item.content, str):
                return item.content
            # Handle content list (InputTextContent or ContentPart)
            for content_item in item.content:
                if isinstance(content_item, InputTextContent):
                    return content_item.text
                if (
                    hasattr(content_item, "type")
                    and content_item.type == "text"
                    and getattr(content_item, "text", None)
                ):
                    return content_item.text
    return None


def _check_error_message(
    content: str | None, error_messages: dict[str, dict[str, Any]]
) -> list[StrategyResponse]:
    """Check if the message content matches an error message in config.

    Returns a list with a single ERROR response if matched,
    or an empty list if no match.
    """
    if content is not None and content in error_messages:
        cfg = error_messages[content]
        return [
            error_response(
                message=cfg["message"],
                status_code=cfg["status-code"],
                error_type=cfg["type"],
                error_code=cfg["code"],
            )
        ]
    return []
