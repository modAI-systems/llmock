# LLM Mock

[![CI](https://github.com/modAI-systems/llmock/actions/workflows/ci.yml/badge.svg)](https://github.com/modAI-systems/llmock/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

OpenAI-compatible mock server for testing LLM integrations.

## Features

- OpenAI API compatibility with key endpoints (`/v1/models`, `/v1/chat/completions`, `/v1/responses`)
- Configurable mock responses via strategies
- Default mirror strategy (echoes input as output)
- **Tool calling support** — config-driven tool call responses when `tools` are present in the request
- **Error message simulation** — config-driven error responses triggered by specific message content
- Streaming support for both Chat Completions and Responses APIs (including `stream_options.include_usage`)

## Quick Start

### Option A: Docker

```bash
docker container run -p 8000:8000 ghcr.io/modai-systems/llmock:latest
```

Test with this sample request (yes, the default secret key is really `your-secret-api-key`):

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-secret-api-key" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

What the request does is simply mirror the input, so it returns `Hello!`.


### Option B: Local Build

**Prerequisites:**
- Python 3.14+
- [uv](https://docs.astral.sh/uv/) (package manager)

**Installation:**

```bash
git clone https://github.com/modAI-systems/llmock.git
cd llmock
uv sync --all-extras
```

**Run the Server:**

```bash
uv run uvicorn llmock.app:app --host 0.0.0.0 --port 8000
```

For development with auto-reload:

```bash
uv run uvicorn llmock.app:app --host 0.0.0.0 --port 8000 --reload
```

The server will be available at `http://localhost:8000`. Health check available at `/health`.

### Usage Example

Point your OpenAI client to the mock server:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="mock-key"  # Any key works
)

# Chat Completions API
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)

# Responses API
response = client.responses.create(
    model="gpt-4o",
    input="Hello!"
)
print(response.output[0].content[0].text)
```

### Tool Calling

When `ToolCallStrategy` is included in the `strategies` list in `config.yaml` and matching `tool-calls` entries exist, llmock responds with tool calls using the configured arguments. If no tools match the config, the next strategy in the chain is tried.

This works on both `/v1/chat/completions` and `/v1/responses` endpoints.

#### Configuration

Include `ToolCallStrategy` in the `strategies` list and add a `tool-calls` section to `config.yaml`:

```yaml
strategies:
  - ErrorStrategy
  - ToolCallStrategy
  - MirrorStrategy

tool-calls:
  calculate: '{"expression": "2+2"}'
  get_weather: '{"location": "San Francisco", "unit": "celsius"}'
```

When a request includes a tool named `calculate`, the mock responds with a tool call whose arguments are `{"expression": "2+2"}`.

#### Chat Completions API

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="mock-key")

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Calculate 6*7"}],
    tools=[{
        "type": "function",
        "function": {
            "name": "calculate",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"]
            }
        }
    }]
)
tool_call = response.choices[0].message.tool_calls[0]
# tool_call.function.name == "calculate"
# tool_call.function.arguments == '{"expression": "2+2"}'  (from config)
```

#### Responses API

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="mock-key")

response = client.responses.create(
    model="gpt-4o",
    input="Calculate 6*7",
    tools=[{
        "type": "function",
        "name": "calculate",
        "parameters": {
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"]
        }
    }]
)
function_call = response.output[0]
# function_call.name == "calculate"
# function_call.arguments == '{"expression": "2+2"}'  (from config)
```

### Error Message Simulation

Error responses are configured in `config.yaml` under the `error-messages` section. When a request's last user message matches a key in that section exactly, the server returns the configured error response instead of a normal completion.

Default configuration:

| Message Content   | HTTP Status | Error Type              | Message                |
|------------------|-------------|-------------------------|------------------------|
| `trigger-401`    | 401         | `authentication_error`  | Invalid API key        |
| `trigger-429`    | 429         | `rate_limit_error`      | Rate limit exceeded    |
| `trigger-500`    | 500         | `server_error`          | Internal server error  |

You can add custom error triggers by extending the `error-messages` section:

```yaml
error-messages:
  "Hi":
    status-code: 403
    message: "Forbidden"
    type: "forbidden_error"
    code: "forbidden"
```

```python
from openai import OpenAI, APIStatusError

client = OpenAI(base_url="http://localhost:8000/v1", api_key="mock-key")

try:
    client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "trigger-429"}]
    )
except APIStatusError as e:
    print(e.status_code)  # 429
    print(e.body)         # {"error": {"message": "Rate limit exceeded", ...}}
```

Only the last user message is checked. System/assistant/tool messages are ignored.
Works on both `/v1/chat/completions` and `/v1/responses` endpoints.

## Configuration

Edit `config.yaml` to configure available models, response strategies, error messages, and tool call responses:

```yaml
# Ordered list of strategies to try (first non-empty result wins)
# Available: ErrorStrategy, ToolCallStrategy, MirrorStrategy
strategies:
  - ErrorStrategy
  - ToolCallStrategy
  - MirrorStrategy

models:
  - id: "gpt-4o"
    created: 1715367049
    owned_by: "openai"
  - id: "gpt-4o-mini"
    created: 1721172741
    owned_by: "openai"

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

# Optional: configure tool call mock responses (used by ToolCallStrategy)
tool-calls:
  calculate: '{"expression": "2+2"}'
  get_weather: '{"location": "San Francisco", "unit": "celsius"}'

### Environment Variable Overrides

You can override values from `config.yaml` using environment variables with the `LLMOCK_` prefix.
Nested keys are joined with underscores, and dashes are converted to underscores.

Examples:

```bash
# Scalar override
export LLMOCK_API_KEY=your-secret-api-key

# Nested override: cors.allow-origins
export LLMOCK_CORS_ALLOW_ORIGINS="http://localhost:8000;http://localhost:5173"
```

Notes:
- Lists are parsed from semicolon-separated values.
- Only keys that exist in `config.yaml` are overridden.
```

## Development

### Run Tests

```bash
uv run pytest -v
```

### Lint & Format

```bash
uv run ruff format src tests    # Format code
uv run ruff check src tests     # Lint code
```

## Documentation

- **Architecture**: See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Decisions**: See [docs/DECISIONS.md](docs/DECISIONS.md)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests and linting (`uv run pytest && uv run ruff check src tests`)
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
