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
uv run python -m llmock3
```

The server starts at `http://localhost:8000`. Health check available at `/health`.

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

Edit `config.yaml` or use environment variables (prefixed with `LLMOCK3_`):

```yaml
host: "0.0.0.0"
port: 8000
debug: false
app_name: "LLMock3"
```

## What It Does

Implements OpenAI's `/v1/models`, `/v1/chat/completions`, and `/v1/completions` endpoints.

Default behavior: Mirror input as output (MirrorStrategy).

## Documentation

- **Architecture**: See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Decisions**: See [docs/DECISIONS.md](docs/DECISIONS.md)

## For AI Agents

Read [AGENTS.md](./AGENTS.md) first for workflow protocols.
