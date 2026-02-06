"""Base strategy interface for chat response generation."""

from typing import Protocol

from llmock.schemas.chat import ChatCompletionRequest


class ChatStrategy(Protocol):
    """Protocol defining the interface for chat response strategies.

    Strategies are responsible for generating response text based on the request.
    They are NOT concerned with streaming vs non-streaming - that is handled
    by the endpoint.
    """

    def generate_response(self, request: ChatCompletionRequest) -> str:
        """Generate a response text for the given chat request.

        Args:
            request: The chat completion request containing messages and parameters.

        Returns:
            The response text to be returned to the client.
        """
        ...
