"""Content mirror strategies - return the input content as the response.

These strategies are useful for testing and debugging, as they echo back
what was sent.
"""

from llmock.schemas.chat import ChatCompletionRequest
from llmock.schemas.responses import (
    InputMessage,
    InputTextContent,
    ResponseCreateRequest,
    SimpleInputMessage,
)


class ChatMirrorStrategy:
    """Strategy that mirrors the last user message for Chat Completions API.

    Implements the ChatStrategy protocol.
    """

    def generate_response(self, request: ChatCompletionRequest) -> str:
        """Return the content of the last user message.

        Args:
            request: The chat completion request containing messages.

        Returns:
            The content of the last user message, or a default message if none found.
        """
        for message in reversed(request.messages):
            if message.role == "user" and message.content:
                return message.content
        return "No user message provided."


class ResponseMirrorStrategy:
    """Strategy that mirrors the last user input for Responses API.

    Implements the ResponseStrategy protocol.
    """

    def generate_response(self, request: ResponseCreateRequest) -> str:
        """Return the content of the last user input.

        Args:
            request: The response create request containing input.

        Returns:
            The content of the last user input, or a default message if none found.
        """
        # Handle simple string input
        if isinstance(request.input, str):
            return request.input

        # Handle list of input items - find the last user message
        for item in reversed(request.input):
            # Handle SimpleInputMessage (role + content as string)
            if isinstance(item, SimpleInputMessage):
                if item.role == "user":
                    return item.content

            # Handle InputMessage (role + content as string or list)
            elif isinstance(item, InputMessage):
                if item.role == "user":
                    if isinstance(item.content, str):
                        return item.content
                    # Handle content list (e.g., input_text items)
                    for content_item in item.content:
                        if isinstance(content_item, InputTextContent):
                            return content_item.text

        return "No user input provided."
