"""OpenAI Responses API request schemas.

Response schemas are imported from openai.types.responses.
Request schemas need to be Pydantic models for FastAPI validation.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

# Re-export response types from openai library
from openai.types.responses import (
    EasyInputMessage,
    Response,
    ResponseInputText,
    ResponseInputTextContent,
    ResponseOutputMessage,
    ResponseOutputText,
    ResponseUsage,
)

# Type aliases for cleaner imports
InputTextContent = ResponseInputTextContent
InputText = ResponseInputText
OutputMessage = ResponseOutputMessage
OutputTextContent = ResponseOutputText


# ============================================================================
# Input Item Types (for request validation)
# ============================================================================


class InputImageContent(BaseModel):
    """Image content in an input message (URL-based)."""

    type: Literal["input_image"] = "input_image"
    image_url: str | None = None
    detail: Literal["auto", "low", "high"] | None = "auto"


class InputMessage(BaseModel):
    """An input message item with structured content."""

    type: Literal["message"] = "message"
    role: Literal["user", "assistant", "system", "developer"]
    content: str | list[InputTextContent | InputImageContent]


class SimpleInputMessage(BaseModel):
    """Simplified input message format (just role and content as string)."""

    role: Literal["user", "assistant", "system", "developer"]
    content: str


class FunctionCallOutputItem(BaseModel):
    """A function call output item in the input list (tool result)."""

    type: Literal["function_call_output"] = "function_call_output"
    call_id: str = Field(description="The ID of the function call being responded to.")
    output: str = Field(description="The output of the function call.")


# Input can be a simple string, or a list of message items
InputItem = InputMessage | SimpleInputMessage | FunctionCallOutputItem


# ============================================================================
# Request Schema
# ============================================================================


class ResponseCreateRequest(BaseModel):
    """Request body for creating a response.

    This follows the OpenAI Responses API specification.
    """

    model: str = Field(description="Model ID used to generate the response.")
    input: str | list[InputItem] = Field(
        description="Text or message inputs to the model."
    )
    instructions: str | None = Field(
        default=None,
        description="A system (or developer) message inserted into the model's context.",
    )
    max_output_tokens: int | None = Field(
        default=None,
        description="Maximum number of tokens to generate.",
    )
    metadata: dict[str, str] | None = Field(
        default=None,
        description="Key-value pairs for storing additional information.",
    )
    parallel_tool_calls: bool = Field(
        default=True,
        description="Whether to allow parallel tool calls.",
    )
    previous_response_id: str | None = Field(
        default=None,
        description="ID of previous response for multi-turn conversations.",
    )
    store: bool = Field(
        default=True,
        description="Whether to store the response for later retrieval.",
    )
    stream: bool = Field(
        default=False,
        description="Whether to stream the response.",
    )
    temperature: float | None = Field(
        default=1.0,
        ge=0.0,
        le=2.0,
        description="Sampling temperature between 0 and 2.",
    )
    top_p: float | None = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling parameter.",
    )
    truncation: Literal["auto", "disabled"] = Field(
        default="disabled",
        description="Truncation strategy for the context window.",
    )
    tools: list[dict[str, Any]] | None = Field(
        default=None,
        description="A list of tools the model may call.",
    )


# ============================================================================
# Delete Response Schema
# ============================================================================


class ResponseDeleted(BaseModel):
    """Response for a deleted response."""

    id: str
    object: Literal["response"] = "response"
    deleted: bool = True


__all__ = [
    # Request types
    "ResponseCreateRequest",
    "ResponseDeleted",
    "InputItem",
    "InputMessage",
    "SimpleInputMessage",
    "FunctionCallOutputItem",
    "InputTextContent",
    "InputImageContent",
    # Re-exported from openai
    "Response",
    "ResponseUsage",
    "ResponseOutputMessage",
    "ResponseOutputText",
    "EasyInputMessage",
]
