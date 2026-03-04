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

**Tool Call Strategies** (config-driven):
- `ChatToolCallStrategy` (Chat Completions): Reads `tool-calls` from config. Goes through each tool in the request, looks up by name in config. Configured tools → `StrategyResponse(type="tool_call")`, unconfigured tools → ignored with warning message.
- `ResponseToolCallStrategy` (Responses API): Same config-driven logic.
- If no tools match config → returns a text warning message.
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

**Error Strategies** (config-driven):
- `ChatErrorStrategy` / `ResponseErrorStrategy`: Read `error-messages` from config. If the last user message content matches a key in `error-messages`, return `StrategyResponse(type="error", ...)` with the configured status code, message, type, and code. Otherwise return empty list (no error).
- Error check happens after model validation but before the main response strategy runs.
- Only the last user message is checked (system/assistant/tool messages are ignored).
- Separate from the main strategy factory — created via `create_chat_error_strategy(config)` / `create_response_error_strategy(config)`.
- Typically placed first in the `strategies` list so errors take priority.

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

# Config-driven error responses (triggered by message content)
error-messages:
  "trigger-401":
    status-code: 401
    message: "Invalid API key"
    type: "authentication_error"
    code: "invalid_api_key"
  "trigger-429":
    status-code: 429
    message: "Rate limit exceeded"
    type: "rate_limit_error"
    code: "rate_limit_exceeded"
  "trigger-500":
    status-code: 500
    message: "Internal server error"
    type: "server_error"
    code: "internal_error"

# Config-driven tool call responses (used by ToolCallStrategy)
tool-calls:
  calculate: '{"expression": "2+2"}'
  get_weather: '{"location": "San Francisco", "unit": "celsius"}'
```

The `strategies` field is an ordered list of strategy names to try. The composition strategy runs them in order; the first one that returns a non-empty result wins. If omitted, `["MirrorStrategy"]` is the default.

The `error-messages` section maps message content strings to error responses. When a request's last user message matches a key in `error-messages` exactly, the server returns the configured HTTP error instead of a normal response. Each entry requires `status-code`, `message`, `type`, and `code`.

## Endpoints

All endpoints follow OpenAI spec exactly (same schemas, status codes, error formats).

### GET /models
Returns configured model list. [OpenAI Spec](https://platform.openai.com/docs/api-reference/models)

### POST /chat/completions
Chat-style completions with streaming support. [OpenAI Spec](https://platform.openai.com/docs/api-reference/chat/create)
- Supports `tools` for tool calling
- Supports `stream_options.include_usage` for usage stats in streaming
- Message content matching `error-messages` config returns HTTP errors (see Error Messages below)

### POST /responses
OpenAI's newer Responses API with streaming support. [OpenAI Spec](https://platform.openai.com/docs/api-reference/responses)
- Supports `tools` for tool calling (Responses API format: flat `{"type": "function", "name": ...}` tools)
- Message content matching `error-messages` config returns HTTP errors (see Error Messages below)

## Error Messages

Error responses are fully config-driven via the `error-messages` section in `config.yaml`. When a request's last user message content matches a key in `error-messages` exactly, the server returns the configured HTTP error instead of a normal response.

Default configuration:

| Message Content   | HTTP Status | Error Type              | Message                  |
|------------------|-------------|-------------------------|--------------------------|
| `trigger-401`    | 401         | `authentication_error`  | Invalid API key          |
| `trigger-429`    | 429         | `rate_limit_error`      | Rate limit exceeded      |
| `trigger-500`    | 500         | `server_error`          | Internal server error    |

Custom error triggers can be added by adding entries to the `error-messages` section with any message string and custom status code, message, type, and code.

Only the last user message is checked. System/assistant/tool messages are ignored.
Model validation happens first, so the model must be valid.
Works on both `/chat/completions` and `/responses`.

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
