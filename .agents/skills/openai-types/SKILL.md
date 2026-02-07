---
name: openai-types
description: OpenAI Python SDK types documentation - when to use SDK types vs custom Pydantic models for FastAPI
---

# OpenAI Python SDK Types

This skill documents the types available in the `openai` Python package and best practices for using them.

## Overview

The OpenAI Python SDK provides comprehensive type definitions for all API interactions. These types are Pydantic models (for responses) and TypedDicts (for request parameters).

## Package Structure

```
openai.types
├── Model, ModelDeleted
├── Completion, CompletionChoice, CompletionUsage
├── Embedding, CreateEmbeddingResponse
├── FileObject, FileDeleted
├── Batch, BatchError, BatchRequestCounts
├── Image, ImagesResponse
├── Moderation, ModerationCreateResponse
├── VectorStore, VectorStoreDeleted
└── chat/
    ├── ChatCompletion
    ├── ChatCompletionChunk
    ├── ChatCompletionMessage
    ├── ChatCompletionMessageParam (union of all message types)
    ├── ChatCompletionSystemMessageParam
    ├── ChatCompletionUserMessageParam
    ├── ChatCompletionAssistantMessageParam
    ├── ChatCompletionToolMessageParam
    └── ... (tool calls, function calls, etc.)
```

## Key Distinctions

### Response Types (Pydantic Models)
- Used for deserializing API responses
- Full Pydantic BaseModel instances
- Examples: `ChatCompletion`, `Model`, `Embedding`

### Request Parameter Types (TypedDict)
- Used for type-checking request parameters
- NOT Pydantic models - they are TypedDicts
- Examples: `ChatCompletionCreateParams`, `ChatCompletionMessageParam`

## Usage Patterns

### For Response Schemas
Import and use directly - they are Pydantic models compatible with FastAPI:

```python
from openai.types import Model, CompletionUsage
from openai.types.chat import ChatCompletion, ChatCompletionMessage

@router.get("/models/{model_id}", response_model=Model)
async def retrieve_model(model_id: str) -> Model:
    return Model(id=model_id, created=1234567890, owned_by="organization")
```

### For Request Schemas
The OpenAI SDK uses TypedDicts for parameters, NOT Pydantic models:

```python
# OpenAI's type (TypedDict - NOT usable directly with FastAPI):
from openai.types.chat import ChatCompletionMessageParam

# For FastAPI request validation, define custom Pydantic models:
class ChatMessageRequest(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str | None
```

## Types Used in This Project

### Currently Imported from openai.types

| Type | Location | Purpose |
|------|----------|---------|
| `Model` | `openai.types` | Model metadata response |
| `CompletionUsage` | `openai.types` | Token usage statistics |
| `ChatCompletion` | `openai.types.chat` | Non-streaming response |
| `ChatCompletionChunk` | `openai.types.chat` | Streaming response chunks |
| `ChatCompletionMessage` | `openai.types.chat` | Message in response |
| `Choice` | `openai.types.chat.chat_completion` | Choice in non-streaming |
| `ChoiceDelta` | `openai.types.chat.chat_completion_chunk` | Delta in streaming |

### Custom Types (with rationale)

| Type | Rationale |
|------|-----------|
| `ModelList` | OpenAI uses pagination wrappers; we need a simple list |
| `ChatMessageRequest` | OpenAI's `ChatCompletionMessageParam` is TypedDict, not Pydantic |
| `ChatCompletionRequest` | Same - TypedDict not compatible with FastAPI validation |

## When to Use OpenAI Types vs Custom

### Use OpenAI Types When:
1. The type is a response schema (Pydantic model)
2. The fields match exactly what you need
3. You want to maintain 1:1 API compatibility

### Use Custom Types When:
1. The OpenAI type is a TypedDict (request params)
2. You need a subset of fields for a mock/simplified API
3. You need custom validation logic
4. The OpenAI structure doesn't fit your use case (e.g., pagination)

## Resources

- **Official SDK GitHub**: https://github.com/openai/openai-python
- **Types Source**: https://github.com/openai/openai-python/tree/main/src/openai/types
- **API Reference**: https://platform.openai.com/docs/api-reference

## Discovering Available Types

To explore available types programmatically:

```python
import openai.types as types
import openai.types.chat as chat_types

# List all types in openai.types
for name in dir(types):
    if not name.startswith('_'):
        print(name)

# List all chat types
for name in dir(chat_types):
    if not name.startswith('_'):
        print(name)
```

## Common Gotchas

1. **TypedDict vs Pydantic**: Request param types (ending in `Param` or `Params`) are TypedDicts, not Pydantic models.

2. **Union Types**: `ChatCompletionMessageParam` is a Union of all message types - can't be instantiated directly.

3. **Nested Imports**: Some types require deep imports:
   ```python
   from openai.types.chat.chat_completion import Choice
   from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice
   ```

4. **Model vs ModelDeleted**: Different types for GET vs DELETE responses.
