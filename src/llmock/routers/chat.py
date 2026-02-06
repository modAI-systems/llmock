"""OpenAI Chat Completions API endpoints."""

import asyncio
import time
import uuid
from collections.abc import AsyncGenerator
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from openai.types import CompletionUsage
from openai.types.chat import ChatCompletion, ChatCompletionChunk, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice
from openai.types.chat.chat_completion_chunk import ChoiceDelta

from llmock.config import Config, get_config
from llmock.schemas.chat import ChatCompletionRequest
from llmock.strategies import ChatMirrorStrategy, ChatCompletionStrategy

router = APIRouter(prefix="/v1", tags=["chat"])

# Default strategy for generating responses
_default_strategy: ChatCompletionStrategy = ChatMirrorStrategy()


def get_strategy() -> ChatCompletionStrategy:
    """Get the current chat strategy."""
    return _default_strategy


def set_strategy(strategy: ChatCompletionStrategy) -> None:
    """Set the chat strategy to use."""
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


def generate_completion_id() -> str:
    """Generate a unique completion ID."""
    return f"chatcmpl-{uuid.uuid4().hex[:24]}"


def estimate_tokens(text: str) -> int:
    """Estimate token count (rough approximation: ~4 chars per token)."""
    return max(1, len(text) // 4)


def create_non_streaming_response(
    request: ChatCompletionRequest,
    response_content: str,
) -> ChatCompletion:
    """Create a non-streaming chat completion response."""
    completion_id = generate_completion_id()
    created = int(time.time())

    # Calculate token usage
    prompt_text = " ".join(msg.content or "" for msg in request.messages if msg.content)
    prompt_tokens = estimate_tokens(prompt_text)
    completion_tokens = estimate_tokens(response_content)

    return ChatCompletion(
        id=completion_id,
        created=created,
        model=request.model,
        object="chat.completion",
        choices=[
            Choice(
                index=0,
                message=ChatCompletionMessage(
                    role="assistant",
                    content=response_content,
                ),
                finish_reason="stop",
            )
        ],
        usage=CompletionUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        ),
    )


async def generate_streaming_response(
    request: ChatCompletionRequest,
    response_content: str,
) -> AsyncGenerator[str, None]:
    """Generate SSE streaming chunks for chat completion."""
    completion_id = generate_completion_id()
    created = int(time.time())

    # First chunk: send role
    first_chunk = ChatCompletionChunk(
        id=completion_id,
        created=created,
        model=request.model,
        object="chat.completion.chunk",
        choices=[
            ChunkChoice(
                index=0,
                delta=ChoiceDelta(role="assistant", content=""),
                finish_reason=None,
            )
        ],
    )
    yield f"data: {first_chunk.model_dump_json()}\n\n"

    # Stream content word by word
    words = response_content.split(" ")
    for i, word in enumerate(words):
        # Add space before word (except first)
        content = word if i == 0 else f" {word}"

        chunk = ChatCompletionChunk(
            id=completion_id,
            created=created,
            model=request.model,
            object="chat.completion.chunk",
            choices=[
                ChunkChoice(
                    index=0,
                    delta=ChoiceDelta(content=content),
                    finish_reason=None,
                )
            ],
        )
        yield f"data: {chunk.model_dump_json()}\n\n"

        # Small delay to simulate streaming
        await asyncio.sleep(0.01)

    # Final chunk: send finish_reason
    final_chunk = ChatCompletionChunk(
        id=completion_id,
        created=created,
        model=request.model,
        object="chat.completion.chunk",
        choices=[
            ChunkChoice(
                index=0,
                delta=ChoiceDelta(),
                finish_reason="stop",
            )
        ],
    )
    yield f"data: {final_chunk.model_dump_json()}\n\n"

    # Send [DONE] marker
    yield "data: [DONE]\n\n"


@router.post("/chat/completions", response_model=None)
async def create_chat_completion(
    request: ChatCompletionRequest,
    config: Annotated[Config, Depends(get_config)],
    strategy: Annotated[ChatCompletionStrategy, Depends(get_strategy)],
) -> ChatCompletion | StreamingResponse:
    """Create a chat completion.

    Creates a model response for the given chat conversation.
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

    return create_non_streaming_response(request, response_content)
