# LLM Mock

[![CI](https://github.com/modAI-systems/llmock/actions/workflows/ci.yml/badge.svg)](https://github.com/modAI-systems/llmock/actions/workflows/ci.yml)
[![Unit Tests](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/guenhter/e105735f20b2a01389046b1b6dd9a5e5/raw/llmock-junit-tests.json)](https://github.com/modAI-systems/llmock/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

OpenAI-compatible mock server for testing LLM integrations.

## Features

- OpenAI API compatibility with key endpoints (`/models`, `/chat/completions`, `/responses`)
- Default mirror strategy (echoes input as output)
- **Tool calling support** — trigger phrase–driven tool call responses when `tools` are present in the request using `call tool '<name>' with '<json>'`
- **Error simulation** — trigger phrase–driven error responses using `raise error <json>` in the last user message
- Streaming support for both Chat Completions and Responses APIs (including `stream_options.include_usage`)

## Quick Start

### Option A: Docker

```bash
docker container run -p 8000:8000 ghcr.io/modai-systems/llmock:latest
```

Test with this sample request:

```bash
curl http://localhost:8000/chat/completions \
  -H "Content-Type: application/json" \
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
uv sync --all-extras
```

**Run the Server:**

```bash
uv run python -m llmock
```

For development with auto-reload:

```bash
uv run uvicorn llmock.app:app --host 0.0.0.0 --port 8000 --reload
```

The server will be available at `http://localhost:8000`. Health check available at `/health`.


## Configuration

Edit `config.yaml` to configure available models and response strategies:

```yaml
# Port for the HTTP server (default: 8000)
port: 8000

# API key for authentication (optional - if not set, no auth required)
api-key:

# CORS configuration
cors:
  allow-origins:
    - "http://localhost:8000"

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
```

### Environment Variable Overrides

You can override values from `config.yaml` using environment variables with the `LLMOCK_` prefix.
Nested keys are joined with underscores, and dashes are converted to underscores.

Examples:

```bash
# Port
export LLMOCK_PORT=9000

# API key (enables authentication)
export LLMOCK_API_KEY=your-secret-api-key

# Lists — always use a JSON array
export LLMOCK_CORS_ALLOW_ORIGINS='["http://localhost:8000","http://localhost:5173"]'

# Models — JSON array of model objects
export LLMOCK_MODELS='[{"id":"my-model","created":1715367049,"owned_by":"custom"},{"id":"other-model","created":1715367049,"owned_by":"custom"}]'
```

Docker example using a custom port and API key:

```bash
docker container run -p 9000:9000 \
  -e LLMOCK_PORT=9000 \
  -e LLMOCK_API_KEY=secret \
  ghcr.io/modai-systems/llmock:latest
```

Notes:
- Lists must be passed as JSON arrays (`[...]`).
- Only keys that exist in `config.yaml` are overridden.


## Operation

### Tool Calling

When `ToolCallStrategy` is included in the `strategies` list, llmock watches the last user message for lines matching the pattern:

```
call tool '<name>' with '<json>'
```

- `<name>` is used verbatim — no check against the `tools` list in the request is performed.
- `<json>` is the arguments string passed to the tool (use `'{}'` for no arguments).
- Multiple matching lines produce multiple tool calls.
- If no line matches, the strategy falls through to the next one (e.g. `MirrorStrategy`).

No extra config keys are needed — adding `ToolCallStrategy` to the `strategies` list is sufficient.

```python
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "call tool 'calculate' with '{\"expression\": \"6*7\"}'"}],
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
# tool_call.function.arguments == '{"expression": "6*7"}'  (from trigger phrase)
```


This works on both `/chat/completions` and `/responses` endpoints.

### Error Simulation

When `ErrorStrategy` is included in the `strategies` list, llmock watches the last user message for lines matching the pattern:

```
raise error <json>
```

The JSON payload must contain:
- `code` (integer) — HTTP status code to return
- `message` (string) — error message
- `type` (string, optional) — OpenAI error type (e.g. `"rate_limit_error"`)
- `error_code` (string, optional) — OpenAI error code (e.g. `"rate_limit_exceeded"`)

The first matching line wins. If no line matches, the strategy falls through to the next one.

No extra config keys are needed — adding `ErrorStrategy` to the `strategies` list is sufficient.

```python
client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": 'raise error {"code": 429, "message": "Rate limit exceeded", "type": "rate_limit_error", "error_code": "rate_limit_exceeded"}'}]
)
```

Only the last user message is checked. System/assistant/tool messages are ignored.
Works on both `/chat/completions` and `/responses` endpoints.

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
