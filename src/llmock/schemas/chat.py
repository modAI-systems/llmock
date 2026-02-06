"""OpenAI Chat Completions API request schemas.

Response schemas are imported from openai.types.chat.
"""

from typing import Literal

from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    """A message in a chat conversation request."""

    role: Literal["system", "user", "assistant", "tool"] = Field(
        description="The role of the message author."
    )
    content: str | None = Field(
        default=None,
        description="The contents of the message.",
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
