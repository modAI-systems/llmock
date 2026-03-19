"""Entry point for running llmock as a module: python -m llmock."""

import uvicorn

from llmock.config import get_config


def main() -> None:
    """Start the uvicorn server using configuration from config.yaml / env vars."""
    config = get_config()
    port = int(config.get("port", 8000))
    uvicorn.run("llmock.app:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
