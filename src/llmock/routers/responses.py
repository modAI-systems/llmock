"""OpenAI Responses API endpoints."""

import asyncio
import time
import uuid
from collections.abc import AsyncGenerator
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from llmock.config import Config, get_config
from openai.types.responses import (
    Response,
    ResponseOutputMessage,
    ResponseOutputText,
    ResponseUsage,
)
from openai.types.responses.response_usage import (
    InputTokensDetails,
    OutputTokensDetails,
)

from llmock.schemas.responses import (
    InputMessage,
    InputTextContent,
    ResponseCreateRequest,
    SimpleInputMessage,
)
from llmock.strategies import ResponseMirrorStrategy, ResponseStrategy

router = APIRouter(prefix="/v1", tags=["responses"])

# Default strategy for generating responses
_default_strategy: ResponseStrategy = ResponseMirrorStrategy()


def get_strategy() -> ResponseStrategy:
    """Get the current response strategy."""
    return _default_strategy


def set_strategy(strategy: ResponseStrategy) -> None:
    """Set the response strategy to use."""
    global _default_strategy
    _default_strategy = strategy


def get_models_config(config: Config) -> list[dict[str, Any]]:
    """Extract models list from config."""
    return config.get("models", [])


def validate_model(model_id: str, config: Config) -> None:
    """Validate that the model exists in config."""
    models_config = get_models_config(config)
    model_ids = [m["id"] for m in models_config]

    if model_ids and model_id not in model_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "message": f"The model '{model_id}' does not exist",
                    "type": "invalid_request_error",
                    "param": "model",
                    "code": "model_not_found",
                }
            },
        )


def generate_response_id() -> str:
    """Generate a unique response ID."""
    return f"resp_{uuid.uuid4().hex}"


def generate_message_id() -> str:
    """Generate a unique message ID."""
    return f"msg_{uuid.uuid4().hex}"


def estimate_tokens(text: str) -> int:
    """Estimate token count (rough approximation: ~4 chars per token)."""
    return max(1, len(text) // 4)


def extract_input_text(request: ResponseCreateRequest) -> str:
    """Extract text from input for token counting."""
    if isinstance(request.input, str):
        return request.input

    texts: list[str] = []
    for item in request.input:
        if isinstance(item, SimpleInputMessage):
            texts.append(item.content)
        elif isinstance(item, InputMessage):
            if isinstance(item.content, str):
                texts.append(item.content)
            else:
                for content_item in item.content:
                    if isinstance(content_item, InputTextContent):
                        texts.append(content_item.text)
    return " ".join(texts)


def create_response(
    request: ResponseCreateRequest,
    response_content: str,
) -> Response:
    """Create a response object."""
    response_id = generate_response_id()
    message_id = generate_message_id()
    created_at = int(time.time())

    # Calculate token usage
    input_text = extract_input_text(request)
    if request.instructions:
        input_text = f"{request.instructions} {input_text}"
    input_tokens = estimate_tokens(input_text)
    output_tokens = estimate_tokens(response_content)

    return Response(
        id=response_id,
        object="response",
        created_at=created_at,
        status="completed",
        completed_at=created_at,
        instructions=request.instructions,
        max_output_tokens=request.max_output_tokens,
        model=request.model,
        output=[
            ResponseOutputMessage(
                type="message",
                id=message_id,
                status="completed",
                role="assistant",
                content=[
                    ResponseOutputText(
                        type="output_text",
                        text=response_content,
                        annotations=[],
                    )
                ],
            )
        ],
        parallel_tool_calls=request.parallel_tool_calls,
        previous_response_id=request.previous_response_id,
        temperature=request.temperature,
        tool_choice="auto",
        tools=[],
        top_p=request.top_p,
        truncation=request.truncation,
        usage=ResponseUsage(
            input_tokens=input_tokens,
            input_tokens_details=InputTokensDetails(cached_tokens=0),
            output_tokens=output_tokens,
            output_tokens_details=OutputTokensDetails(reasoning_tokens=0),
            total_tokens=input_tokens + output_tokens,
        ),
        metadata=request.metadata or {},
    )


async def generate_streaming_response(
    request: ResponseCreateRequest,
    response_content: str,
) -> AsyncGenerator[str, None]:
    """Generate SSE streaming events for response creation."""
    response_id = generate_response_id()
    message_id = generate_message_id()
    created_at = int(time.time())

    # Calculate token usage
    input_text = extract_input_text(request)
    if request.instructions:
        input_text = f"{request.instructions} {input_text}"
    input_tokens = estimate_tokens(input_text)
    output_tokens = estimate_tokens(response_content)

    # Event: response.created
    created_event = {
        "type": "response.created",
        "response": {
            "id": response_id,
            "object": "response",
            "created_at": created_at,
            "status": "in_progress",
            "model": request.model,
            "output": [],
        },
    }
    yield f"event: response.created\ndata: {_json_dumps(created_event)}\n\n"

    # Event: response.in_progress
    in_progress_event = {
        "type": "response.in_progress",
        "response": {
            "id": response_id,
            "object": "response",
            "created_at": created_at,
            "status": "in_progress",
            "model": request.model,
            "output": [],
        },
    }
    yield f"event: response.in_progress\ndata: {_json_dumps(in_progress_event)}\n\n"

    # Event: response.output_item.added
    item_added_event = {
        "type": "response.output_item.added",
        "output_index": 0,
        "item": {
            "type": "message",
            "id": message_id,
            "status": "in_progress",
            "role": "assistant",
            "content": [],
        },
    }
    yield f"event: response.output_item.added\ndata: {_json_dumps(item_added_event)}\n\n"

    # Event: response.content_part.added
    content_part_added_event = {
        "type": "response.content_part.added",
        "item_id": message_id,
        "output_index": 0,
        "content_index": 0,
        "part": {"type": "output_text", "text": "", "annotations": []},
    }
    yield f"event: response.content_part.added\ndata: {_json_dumps(content_part_added_event)}\n\n"

    # Stream content word by word
    words = response_content.split(" ")
    for i, word in enumerate(words):
        # Add space before word (except first)
        delta = word if i == 0 else f" {word}"

        delta_event = {
            "type": "response.output_text.delta",
            "item_id": message_id,
            "output_index": 0,
            "content_index": 0,
            "delta": delta,
        }
        yield f"event: response.output_text.delta\ndata: {_json_dumps(delta_event)}\n\n"

        # Small delay to simulate streaming
        await asyncio.sleep(0.01)

    # Event: response.output_text.done
    text_done_event = {
        "type": "response.output_text.done",
        "item_id": message_id,
        "output_index": 0,
        "content_index": 0,
        "text": response_content,
    }
    yield f"event: response.output_text.done\ndata: {_json_dumps(text_done_event)}\n\n"

    # Event: response.content_part.done
    content_part_done_event = {
        "type": "response.content_part.done",
        "item_id": message_id,
        "output_index": 0,
        "content_index": 0,
        "part": {"type": "output_text", "text": response_content, "annotations": []},
    }
    yield f"event: response.content_part.done\ndata: {_json_dumps(content_part_done_event)}\n\n"

    # Event: response.output_item.done
    item_done_event = {
        "type": "response.output_item.done",
        "output_index": 0,
        "item": {
            "type": "message",
            "id": message_id,
            "status": "completed",
            "role": "assistant",
            "content": [
                {"type": "output_text", "text": response_content, "annotations": []}
            ],
        },
    }
    yield f"event: response.output_item.done\ndata: {_json_dumps(item_done_event)}\n\n"

    # Event: response.completed
    completed_event = {
        "type": "response.completed",
        "response": {
            "id": response_id,
            "object": "response",
            "created_at": created_at,
            "status": "completed",
            "completed_at": int(time.time()),
            "model": request.model,
            "output": [
                {
                    "type": "message",
                    "id": message_id,
                    "status": "completed",
                    "role": "assistant",
                    "content": [
                        {
                            "type": "output_text",
                            "text": response_content,
                            "annotations": [],
                        }
                    ],
                }
            ],
            "usage": {
                "input_tokens": input_tokens,
                "input_tokens_details": {"cached_tokens": 0},
                "output_tokens": output_tokens,
                "output_tokens_details": {"reasoning_tokens": 0},
                "total_tokens": input_tokens + output_tokens,
            },
        },
    }
    yield f"event: response.completed\ndata: {_json_dumps(completed_event)}\n\n"


def _json_dumps(obj: dict[str, Any]) -> str:
    """Convert dict to JSON string."""
    import json

    return json.dumps(obj)


@router.post("/responses", response_model=None)
async def create_response_endpoint(
    request: ResponseCreateRequest,
    config: Annotated[Config, Depends(get_config)],
    strategy: Annotated[ResponseStrategy, Depends(get_strategy)],
) -> Response | StreamingResponse:
    """Create a model response.

    Creates a model response for the given input.
    Supports both streaming and non-streaming responses.

    The actual response content is generated by the strategy.
    The endpoint handles streaming vs non-streaming output formatting.
    """
    # Validate model exists
    validate_model(request.model, config)

    # Get response content from strategy
    response_content = strategy.generate_response(request)

    if request.stream:
        return StreamingResponse(
            generate_streaming_response(request, response_content),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    return create_response(request, response_content)
