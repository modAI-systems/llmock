# llmock Architecture

**Simple OpenAI-compatible mock server for testing**

## Overview

Mock server implementing OpenAI's `/models`, `/chat/completions`, and `/responses` endpoints. Default behavior: echo input as output (MirrorStrategy). Pluggable strategy system for custom behaviors.

**Spec Reference**: Follow [OpenAI API Reference](https://platform.openai.com/docs/api-reference) exactly.
**OpenAPI Spec**: https://app.stainless.com/api/spec/documented/openai/openapi.documented.yml

## Core Design

```
Client Request
    ↓
HTTP Server (parse, route, format)
    ↓
Auth Middleware (validate API key)
    ↓
Endpoint Handler (models | chat | completions)
    ↓
Strategy (generate response content)
    ↓
Streaming Adapter (format SSE if stream=true)
    ↓
Response
```

### Separation of Concerns

| Component | Responsibility | Doesn't Know About |
|-----------|----------------|-------------------|
| **HTTP Server** | Protocol, routing, SSE | Authentication, strategies |
| **Auth Middleware** | API key validation | Endpoints, strategies |
| **Endpoint Handler** | Parse request, call strategy | How strategy works |
| **Strategy** | Generate content | HTTP, SSE, authentication |
| **Streaming Adapter** | SSE formatting | Strategy logic |

### Strategy Pattern

**Response Type**:
```python
@dataclass
class StrategyResponse:
    type: str              # "text", "tool_call", or "error"
    content: str           # Text content, tool call arguments, or error message
    name: str | None       # Function name (for tool_call type)
    status_code: int | None    # HTTP status code (for error type)
    error_type: str | None     # Error type string (for error type)
    error_code: str | None     # Error code string (for error type)
```

**Interfaces**:
```
ChatStrategy {
  generateResponse(request) → list[StrategyResponse]
}

ResponseStrategy {
  generateResponse(request) → list[StrategyResponse]
}
```

**Default Strategies (MirrorStrategy)**:
- `ChatMirrorStrategy`: Extract last user message → return `[StrategyResponse(type="text", content=...)]`
- `ResponseMirrorStrategy`: Extract last user input → return `[StrategyResponse(type="text", content=...)]`

**Tool Call Strategies** (trigger phrase–driven):
- `ChatToolCallStrategy` (Chat Completions): Parses the **last user message** line-by-line for the pattern `call tool '<name>' with '<json>'`. Each matching line whose `<name>` appears in `request.tools` produces a `StrategyResponse(type="tool_call")` with the extracted JSON arguments. Multiple matching lines produce multiple responses. If no line matches, returns an empty list (falls through to the next strategy). No config keys required.
- `ResponseToolCallStrategy` (Responses API): Same trigger-phrase logic but operates on `ResponseCreateRequest` inputs (string or structured message list).
- Both support streaming and non-streaming modes.

**Strategy Factory**:
- `create_chat_strategy(config)` / `create_response_strategy(config)` — reads `response-strategy` from config, looks up the class pair in a registry, and instantiates with the full config.
- All strategies accept `config: dict` in their constructor and read their own section.
- Short names used in config: `MirrorStrategy`, `ToolCallStrategy`.
- Falls back to `MirrorStrategy` when `response-strategy` is unset or unrecognised.

**Composition Strategy** (used by routers):
- `ChatCompositionStrategy` / `ResponseCompositionStrategy` — reads the `strategies` list from config, creates each sub-strategy via the factory registry, and runs them in order.
- The first strategy that returns a **non-empty** `list[StrategyResponse]` wins; remaining strategies are not called.
- Default when `strategies` is missing: `["MirrorStrategy"]`.
- Unknown strategy names are skipped with a warning.
- Not registered in the factory — it **wraps** the factory internally.
- Both routers (`/chat/completions` and `/responses`) instantiate the composition strategy directly.

**Error Strategies** (trigger phrase–driven):
- `ChatErrorStrategy` / `ResponseErrorStrategy`: Scan the last user message line-by-line for `raise error <json>`. JSON must contain `code` (int) and `message` (str); optional `type` and `error_code`. First matching line wins. No config required.
- Only the last user message is checked (system/assistant/tool messages are ignored).
- Registered in the factory under `"ErrorStrategy"` — place first in the `strategies` list so errors take priority.

**Future Strategies**: FixedResponse, Template, Random, AIProxy

## Configuration

**config.yaml**:
```yaml
api-key: "your-secret-api-key"

# Ordered list of strategies (first non-empty result wins)
strategies:
  - ErrorStrategy
  - ToolCallStrategy
  - MirrorStrategy

models:
  - id: gpt-4o
    created: 1715367049
    owned_by: openai
  - id: gpt-4o-mini
    created: 1721172741
    owned_by: openai

```

The `strategies` field is an ordered list of strategy names to try. The composition strategy runs them in order; the first one that returns a non-empty result wins. If omitted, `["MirrorStrategy"]` is the default.

`ToolCallStrategy` fires when the last user message contains a line matching `call tool '<name>' with '<json>'` and `<name>` is present in `request.tools`.

`ErrorStrategy` fires when the last user message contains a line matching `raise error <json>`, where `<json>` has at least `code` (int) and `message` (str).

## Endpoints

All endpoints follow OpenAI spec exactly (same schemas, status codes, error formats).

### GET /models
Returns configured model list. [OpenAI Spec](https://platform.openai.com/docs/api-reference/models)

### POST /chat/completions
Chat-style completions with streaming support. [OpenAI Spec](https://platform.openai.com/docs/api-reference/chat/create)
- Supports `tools` for tool calling
- Supports `stream_options.include_usage` for usage stats in streaming
- `raise error <json>` trigger phrase in last user message returns the configured HTTP error

### POST /responses
OpenAI's newer Responses API with streaming support. [OpenAI Spec](https://platform.openai.com/docs/api-reference/responses)
- Supports `tools` for tool calling (Responses API format: flat `{"type": "function", "name": ...}` tools)
- `raise error <json>` trigger phrase in last user message returns the configured HTTP error

## Streaming (SSE)

When `stream: true`, return Server-Sent Events:

```
data: {"id":"chatcmpl-xyz",...,"delta":{"role":"assistant","content":""},...}

data: {"id":"chatcmpl-xyz",...,"delta":{"content":"Hello"},...}

data: {"id":"chatcmpl-xyz",...,"delta":{"content":" world"},...}

data: {"id":"chatcmpl-xyz",...,"delta":{},"finish_reason":"stop"}

data: [DONE]
```

**Chunking**: Word-level (split on whitespace) for MVP.
**Format**: Exactly matches [OpenAI Streaming Spec](https://platform.openai.com/docs/api-reference/chat/streaming)

## Authentication

**Format**: `Authorization: Bearer <api-key>`
**Validation**: Against `config/auth.yaml`
**Errors**: Return 401 with OpenAI error format if invalid

## Error Handling

All errors follow OpenAI format:
```json
{
  "error": {
    "message": "Error description",
    "type": "invalid_request_error",
    "param": "field_name",
    "code": "error_code"
  }
}
```

**Status Codes**: 400 (bad request), 401 (auth), 404 (not found), 500 (server error)

## Key Decisions

**Why Strategy Pattern?**
Add new response behaviors (fixed, template, proxy) without touching core code.

**Why YAML config?**
Change API keys and models without rebuilding.

**Why separate Streaming Adapter?**
Strategies generate content, adapter handles SSE protocol. Clean separation.

**No persistence?**
Keem mock easy and stateless.

## Testing Strategy

**Client Compatibility**:
```python
# If OpenAI's client works, we're compatible
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8080",
    api_key="sk-mock-key"
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "test"}]
)
```

## Extension Examples

**Add FixedResponseStrategy**:
```python
class FixedResponseStrategy:
    def __init__(self, response_text):
        self.response_text = response_text

    def generateChatResponse(self, req):
        return {
            'content': self.response_text,
            'finish_reason': 'stop'
        }
```

**Add per-model strategies** (future):
```yaml
model_strategies:
  gpt-4o: mirror
  gpt-3.5-turbo: fixed
```

## References

- **OpenAI API Docs**: https://platform.openai.com/docs/api-reference
- **OpenAPI Spec**: https://app.stainless.com/api/spec/documented/openai/openapi.documented.yml
- **SSE Spec**: https://html.spec.whatwg.org/multipage/server-sent-events.html
- **Strategy Pattern**: https://refactoring.guru/design-patterns/strategy
