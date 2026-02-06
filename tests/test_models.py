"""Tests for the /v1/models endpoint using official OpenAI client."""

from collections.abc import AsyncGenerator

import httpx
import pytest
from openai import AsyncOpenAI, NotFoundError

from llmock3.app import create_app
from llmock3.config import Config, get_config


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
async def openai_client(test_config: Config) -> AsyncGenerator[AsyncOpenAI, None]:
    """Provide an AsyncOpenAI client using ASGI transport (no real server needed)."""
    app = create_app()
    app.dependency_overrides[get_config] = lambda: test_config

    # Use httpx with ASGITransport to test without spinning up a real server
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as http_client:
        client = AsyncOpenAI(
            api_key="test-api-key",
            http_client=http_client,
            base_url="http://testserver/v1",
        )
        yield client


async def test_list_models_returns_model_list(openai_client: AsyncOpenAI) -> None:
    """Test that listing models returns the configured models."""
    result = await openai_client.models.list()

    assert len(result.data) == 2


async def test_list_models_returns_correct_model_data(
    openai_client: AsyncOpenAI,
) -> None:
    """Test that model data matches configuration."""
    result = (await openai_client.models.list()).data

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


async def test_retrieve_existing_model(openai_client: AsyncOpenAI) -> None:
    """Test retrieving an existing model returns correct data."""
    model = await openai_client.models.retrieve("test-model-1")

    assert model.id == "test-model-1"
    assert model.object == "model"
    assert model.created == 1700000000
    assert model.owned_by == "test-org"


async def test_retrieve_nonexistent_model_raises_error(
    openai_client: AsyncOpenAI,
) -> None:
    """Test that retrieving a nonexistent model raises NotFoundError."""
    with pytest.raises(NotFoundError):
        await openai_client.models.retrieve("nonexistent-model")
