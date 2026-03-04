"""OpenAI Chat Completions API request schemas.

Response schemas are imported from openai.types.chat.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field


class ContentPart(BaseModel):
    """A single content part in a message (e.g. text, image_url)."""

    type: str = Field(
        description="The type of content part, e.g. 'text' or 'image_url'."
    )
    text: str | None = Field(
        default=None,
        description="The text content (for type='text').",
    )


class ChatMessageRequest(BaseModel):
    """A message in a chat conversation request."""

    role: Literal["system", "user", "assistant", "tool"] = Field(
        description="The role of the message author."
    )
    content: str | list[ContentPart] | None = Field(
        default=None,
        description="The contents of the message.",
    )


class StreamOptions(BaseModel):
    """Options for streaming responses."""

    include_usage: bool = Field(
        default=False,
        description="If set, an additional chunk with usage stats is sent.",
    )


class ChatCompletionRequest(BaseModel):
    """Request body for chat completions."""

    model: str = Field(description="ID of the model to use.")
    messages: list[ChatMessageRequest] = Field(
        description="A list of messages comprising the conversation so far."
    )
    stream: bool = Field(
        default=False,
        description="If set, partial message deltas will be sent as SSE events.",
    )
    stream_options: StreamOptions | None = Field(
        default=None,
        description="Options for streaming responses.",
    )
    temperature: float | None = Field(
        default=1.0,
        ge=0.0,
        le=2.0,
        description="Sampling temperature between 0 and 2.",
    )
    max_tokens: int | None = Field(
        default=None,
        ge=1,
        description="The maximum number of tokens to generate.",
    )
    tools: list[dict[str, Any]] | None = Field(
        default=None,
        description="A list of tools the model may call.",
    )
