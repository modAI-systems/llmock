"""Content mirror strategies - return the input content as the response.

These strategies are useful for testing and debugging, as they echo back
what was sent.
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
from llmock.strategies.base import StrategyResponse, text_response


class ChatMirrorStrategy:
    """Strategy that mirrors the last user message for Chat Completions API.

    Implements the ChatCompletionStrategy protocol.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        pass

    def generate_response(
        self, request: ChatCompletionRequest
    ) -> list[StrategyResponse]:
        """Return a response echoing the last user message.

        Args:
            request: The chat completion request containing messages.

        Returns:
            A single-item list with a text StrategyResponse, or a default
            message when no user message is found.
        """
        last = next(
            (
                msg
                for msg in reversed(request.messages)
                if msg.role == "user" and extract_text_content(msg.content)
            ),
            None,
        )
        if last is None:
            return [text_response("No user message provided.")]
        content = extract_text_content(last.content) or ""
        return (
            [text_response(content)]
            if content
            else [text_response("No user message provided.")]
        )


class ResponseMirrorStrategy:
    """Strategy that mirrors the last user input for Responses API.

    Implements the ResponseStrategy protocol.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        pass

    def generate_response(
        self, request: ResponseCreateRequest
    ) -> list[StrategyResponse]:
        """Return the content of the last user input.

        Args:
            request: The response create request containing input.

        Returns:
            A single-item list with a text StrategyResponse containing
            the last user input, or a default message if none found.
        """
        # Handle simple string input
        if isinstance(request.input, str):
            return [text_response(request.input)]

        # Handle list of input items - find the last user message
        for item in reversed(request.input):
            # Handle SimpleInputMessage (role + content as string or list)
            if isinstance(item, SimpleInputMessage):
                if item.role == "user":
                    text = extract_text_content(item.content)
                    if text:
                        return [text_response(text)]

            # Handle InputMessage (role + content as string or list)
            elif isinstance(item, InputMessage):
                if item.role == "user":
                    if isinstance(item.content, str):
                        return [text_response(item.content)]
                    # Handle content list (e.g., input_text items or ContentPart)
                    texts = []
                    for content_item in item.content:
                        if isinstance(content_item, InputTextContent):
                            texts.append(content_item.text)
                        elif (
                            hasattr(content_item, "type")
                            and content_item.type == "text"
                            and getattr(content_item, "text", None)
                        ):
                            texts.append(content_item.text)
                    if texts:
                        return [text_response("\n".join(texts))]

        return [text_response("No user input provided.")]
