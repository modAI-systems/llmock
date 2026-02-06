"""Tests for the /v1/models endpoint using official OpenAI client."""

import threading
import time
from collections.abc import Generator

import pytest
import uvicorn
from fastapi import FastAPI
from openai import OpenAI

from llmock3.config import Config, get_config
from llmock3.routers import health, models


def create_test_app(config: Config) -> FastAPI:
    """Create a FastAPI app with custom config for testing."""
    app = FastAPI(title="LLMock3-Test")

    # Override the config dependency
    app.dependency_overrides[get_config] = lambda: config

    # Include routers
    app.include_router(health.router)
    app.include_router(models.router)

    return app


class ServerRunner:
    """Context manager to run the test server in a background thread."""

    def __init__(self, app: FastAPI, host: str = "127.0.0.1", port: int = 8765) -> None:
        self.app = app
        self.host = host
        self.port = port
        self.server: uvicorn.Server | None = None
        self.thread: threading.Thread | None = None

    def start(self) -> None:
        """Start the server in a background thread."""
        config = uvicorn.Config(
            self.app, host=self.host, port=self.port, log_level="error"
        )
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(target=self.server.run, daemon=True)
        self.thread.start()
        # Wait for server to be ready
        time.sleep(0.5)

    def stop(self) -> None:
        """Stop the server."""
        if self.server:
            self.server.should_exit = True
        if self.thread:
            self.thread.join(timeout=5)


@pytest.fixture
def test_config() -> Config:
    """Provide test config with custom models."""
    return {
        "models": [
            {"id": "test-model-1", "created": 1700000000, "owned_by": "test-org"},
            {"id": "test-model-2", "created": 1700000001, "owned_by": "test-org"},
        ],
    }


@pytest.fixture
def server(test_config: Config) -> Generator[ServerRunner, None, None]:
    """Start a test server with custom config and yield it."""
    app = create_test_app(test_config)
    test_server = ServerRunner(app)
    test_server.start()
    yield test_server
    test_server.stop()


@pytest.fixture
def openai_client(server: ServerRunner) -> OpenAI:
    """Provide an OpenAI client configured to use the test server."""
    return OpenAI(
        api_key="test-api-key",
        base_url=f"http://{server.host}:{server.port}/v1",
    )


def test_list_models_returns_model_list(openai_client: OpenAI) -> None:
    """Test that listing models returns the configured models."""
    result = openai_client.models.list()

    model_list = list(result)
    assert len(model_list) == 2


def test_list_models_returns_correct_model_data(openai_client: OpenAI) -> None:
    """Test that model data matches configuration."""
    result = list(openai_client.models.list())

    # Check first model
    model_1 = next((m for m in result if m.id == "test-model-1"), None)
    assert model_1 is not None
    assert model_1.object == "model"
    assert model_1.created == 1700000000
    assert model_1.owned_by == "test-org"

    # Check second model
    model_2 = next((m for m in result if m.id == "test-model-2"), None)
    assert model_2 is not None
    assert model_2.object == "model"
    assert model_2.created == 1700000001
    assert model_2.owned_by == "test-org"


def test_retrieve_existing_model(openai_client: OpenAI) -> None:
    """Test retrieving an existing model returns correct data."""
    model = openai_client.models.retrieve("test-model-1")

    assert model.id == "test-model-1"
    assert model.object == "model"
    assert model.created == 1700000000
    assert model.owned_by == "test-org"


def test_retrieve_nonexistent_model_raises_error(openai_client: OpenAI) -> None:
    """Test that retrieving a nonexistent model raises NotFoundError."""
    from openai import NotFoundError

    with pytest.raises(NotFoundError):
        openai_client.models.retrieve("nonexistent-model")
