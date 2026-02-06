# llmock Architecture

**Simple OpenAI-compatible mock server for testing**

## Overview

Mock server implementing OpenAI's `/v1/models`, `/v1/chat/completions`, and `/v1/completions` endpoints. Default behavior: echo input as output (MirrorStrategy). Pluggable strategy system for custom behaviors.

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

**Interface**:
```
ResponseStrategy {
  generateChatResponse(request) → { content, finish_reason }
  generateCompletionResponse(request) → { text, finish_reason }
}
```

**Default Strategy (MirrorStrategy)**:
- Chat: Extract last user message → return as assistant message
- Completion: Extract prompt → return as completion text

**Future Strategies**: FixedResponse, Template, Random, AIProxy

## Configuration

**config/server.yaml**
```yaml
server:
  host: 0.0.0.0
  port: 8080
strategies:
  default: mirror
```

**config/auth.yaml**
```yaml
valid_api_keys:
  - sk-mock-key-default
```

**config/models.yaml**
```yaml
models:
  - id: gpt-4o
    object: model
    created: 1678000000
    owned_by: openai
```

## Endpoints

All endpoints follow OpenAI spec exactly (same schemas, status codes, error formats).

### GET /v1/models
Returns configured model list. [OpenAI Spec](https://platform.openai.com/docs/api-reference/models)

### POST /v1/chat/completions
Chat-style completions with streaming support. [OpenAI Spec](https://platform.openai.com/docs/api-reference/chat/create)

### POST /v1/completions
Legacy text completions with streaming support. [OpenAI Spec](https://platform.openai.com/docs/api-reference/completions)

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
    base_url="http://localhost:8080/v1",
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
