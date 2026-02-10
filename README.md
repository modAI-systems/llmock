# LLM Mock

[![CI](https://github.com/modAI-systems/llmock/actions/workflows/ci.yml/badge.svg)](https://github.com/modAI-systems/llmock/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

OpenAI-compatible mock server for testing LLM integrations.

## Features

- OpenAI API compatibility with key endpoints (`/v1/models`, `/v1/chat/completions`, `/v1/responses`)
- Configurable mock responses via strategies
- Default mirror strategy (echoes input as output)
- Streaming support for both Chat Completions and Responses APIs

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

## Configuration

Edit `config.yaml` to configure available models:

```yaml
models:
  - id: "gpt-4o"
    created: 1715367049
    owned_by: "openai"
  - id: "gpt-4o-mini"
    created: 1721172741
    owned_by: "openai"

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
