# LLMock3

OpenAI-compatible mock server for testing LLM integrations.

## Quick Start

### Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) (package manager)

### Installation

```bash
uv sync --all-extras
```

### Run the Application

```bash
uv run uvicorn llmock3.app:app --host 0.0.0.0 --port 8000
```

For development with auto-reload:

```bash
uv run uvicorn llmock3.app:app --host 0.0.0.0 --port 8000 --reload
```

Health check available at `/health`.

### Run Tests

```bash
uv run pytest -v
```

### Lint & Format

```bash
uv run ruff format src tests    # Format code
uv run ruff check src tests     # Lint code
```

## Configuration

Edit `config.yaml` to configure router-specific settings:

```yaml
models:
  - id: "gpt-4o"
    created: 1715367049
    owned_by: "openai"
  - id: "gpt-4o-mini"
    created: 1721172741
    owned_by: "openai"
```

Server host/port are configured via uvicorn CLI arguments (see above).

## What It Does

Implements OpenAI's `/v1/models`, `/v1/chat/completions`, and `/v1/completions` endpoints.

Default behavior: Mirror input as output (MirrorStrategy).

## Documentation

- **Architecture**: See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Decisions**: See [docs/DECISIONS.md](docs/DECISIONS.md)

## For AI Agents

Read [AGENTS.md](./AGENTS.md) first for workflow protocols.
