"""Tests for the /history endpoints."""

import pytest
from httpx import AsyncClient

from llmock import history_store


@pytest.fixture(autouse=True)
def reset_history() -> None:
    """Ensure history is empty before and after every test."""
    history_store.reset()
    yield
    history_store.reset()


async def test_history_initially_empty(client: AsyncClient) -> None:
    """GET /history returns an empty list when no requests have been made."""
    response = await client.get("/history")
    assert response.status_code == 200
    assert response.json() == {"requests": []}


async def test_history_records_chat_request(client: AsyncClient) -> None:
    """A chat completion request appears in the history."""
    await client.post(
        "/chat/completions",
        json={"model": "gpt-4o", "messages": [{"role": "user", "content": "Hello"}]},
    )

    response = await client.get("/history")
    assert response.status_code == 200
    data = response.json()
    assert len(data["requests"]) == 1
    entry = data["requests"][0]
    assert entry["method"] == "POST"
    assert entry["path"] == "/chat/completions"
    assert entry["body"]["model"] == "gpt-4o"


async def test_history_preserves_order(client: AsyncClient) -> None:
    """Multiple requests are stored in the order they were received."""
    await client.post(
        "/chat/completions",
        json={"model": "gpt-4o", "messages": [{"role": "user", "content": "first"}]},
    )
    await client.post(
        "/chat/completions",
        json={"model": "gpt-4o", "messages": [{"role": "user", "content": "second"}]},
    )

    response = await client.get("/history")
    data = response.json()
    assert len(data["requests"]) == 2
    assert data["requests"][0]["body"]["messages"][0]["content"] == "first"
    assert data["requests"][1]["body"]["messages"][0]["content"] == "second"


async def test_history_does_not_record_history_get(client: AsyncClient) -> None:
    """GET /history itself is not recorded in the history."""
    await client.get("/history")
    await client.get("/history")

    response = await client.get("/history")
    assert response.json() == {"requests": []}


async def test_history_does_not_record_health(client: AsyncClient) -> None:
    """Health check calls are not recorded in the history."""
    await client.get("/health")

    response = await client.get("/history")
    assert response.json() == {"requests": []}


async def test_history_reset_clears_entries(client: AsyncClient) -> None:
    """DELETE /history removes all entries and returns 204."""
    await client.post(
        "/chat/completions",
        json={"model": "gpt-4o", "messages": [{"role": "user", "content": "Hi"}]},
    )

    reset_response = await client.delete("/history")
    assert reset_response.status_code == 204

    history_response = await client.get("/history")
    assert history_response.json() == {"requests": []}


async def test_history_reset_does_not_require_auth(client: AsyncClient) -> None:
    """DELETE /history works without an Authorization header."""
    # Use a raw client without the auth header
    from httpx import ASGITransport, AsyncClient as RawClient

    from llmock.app import create_app
    from llmock.config import get_config

    config = {"models": [], "api-key": "secret"}
    app = create_app(config=config)
    app.dependency_overrides[get_config] = lambda: config

    transport = ASGITransport(app=app)
    async with RawClient(transport=transport, base_url="http://test") as raw:
        response = await raw.delete("/history")
    assert response.status_code == 204


async def test_history_get_does_not_require_auth(client: AsyncClient) -> None:
    """GET /history works without an Authorization header."""
    from httpx import ASGITransport, AsyncClient as RawClient

    from llmock.app import create_app
    from llmock.config import get_config

    config = {"models": [], "api-key": "secret"}
    app = create_app(config=config)
    app.dependency_overrides[get_config] = lambda: config

    transport = ASGITransport(app=app)
    async with RawClient(transport=transport, base_url="http://test") as raw:
        response = await raw.get("/history")
    assert response.status_code == 200


async def test_history_entry_has_timestamp(client: AsyncClient) -> None:
    """Each history entry includes a timestamp."""
    await client.post(
        "/chat/completions",
        json={"model": "gpt-4o", "messages": [{"role": "user", "content": "ts test"}]},
    )

    response = await client.get("/history")
    entry = response.json()["requests"][0]
    assert "timestamp" in entry
    # Basic ISO 8601 check
    assert "T" in entry["timestamp"]
