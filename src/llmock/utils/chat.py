"""Chat-related utility helpers."""

from llmock.schemas.chat import ChatCompletionRequest, ContentPart
from llmock.schemas.responses import (
    InputMessage,
    ResponseCreateRequest,
    SimpleInputMessage,
)


def extract_text_content(content: "str | list[ContentPart] | None") -> str | None:
    """Extract plain text from a content field that may be a string or list of parts.

    For list content, all parts with ``type == "text"`` are concatenated with a
    newline separator.  Returns *None* when content is *None* or when the list
    contains no text parts.
    """
    if content is None:
        return None
    if isinstance(content, str):
        return content
    texts = [
        part.text for part in content if part.type == "text" and part.text is not None
    ]
    return "\n".join(texts) if texts else None


def extract_last_user_text_chat(request: ChatCompletionRequest) -> str | None:
    """Extract the text of the last user message from a Chat Completions request.

    Returns *None* when no user message is found or the message has no text.
    """
    for message in reversed(request.messages):
        if message.role == "user" and message.content:
            return extract_text_content(message.content)
    return None


def extract_last_user_text_response(request: ResponseCreateRequest) -> str | None:
    """Extract the text of the last user input from a Responses API request.

    Handles all three input shapes:

    - Plain string: returned as-is.
    - ``SimpleInputMessage``: delegates to :func:`extract_text_content`.
    - ``InputMessage`` with a content list: all text parts are concatenated
      with a newline separator (consistent with :func:`extract_text_content`).

    Returns *None* when no user message is found or the message has no text.
    """
    if isinstance(request.input, str):
        return request.input

    for item in reversed(request.input):
        if isinstance(item, SimpleInputMessage) and item.role == "user":
            return extract_text_content(item.content)
        if isinstance(item, InputMessage) and item.role == "user":
            if isinstance(item.content, str):
                return item.content
            texts = [
                part.text
                for part in item.content
                if hasattr(part, "text") and part.text
            ]
            return "\n".join(texts) if texts else None
    return None
