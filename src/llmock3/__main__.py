"""Main entry point for running the application."""

import uvicorn

from llmock3.config import get_settings


def main() -> None:
    """Run the application using uvicorn."""
    settings = get_settings()
    uvicorn.run(
        "llmock3.app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
