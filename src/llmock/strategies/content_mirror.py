"""Content mirror strategy - returns the input content as the response."""

from llmock.schemas.chat import ChatCompletionRequest


class ContentMirrorStrategy:
    """Strategy that mirrors the last user message content as the response.

    This is useful for testing and debugging, as it echoes back what was sent.
    """

    def generate_response(self, request: ChatCompletionRequest) -> str:
        """Return the content of the last user message.

        Args:
            request: The chat completion request containing messages.

        Returns:
            The content of the last user message, or a default message if none found.
        """
        # Find the last user message
        for message in reversed(request.messages):
            if message.role == "user" and message.content:
                return message.content

        return "No user message provided."
