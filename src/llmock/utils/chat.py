"""Chat-related utility helpers."""

from llmock.schemas.chat import ContentPart


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
