"""Tests for the custom answers strategy."""

from collections.abc import AsyncGenerator

import httpx
import pytest

from llmock.app import create_app
from llmock.config import Config, get_config
from llmock.schemas.chat import ChatCompletionRequest, ChatMessageRequest
from llmock.schemas.responses import ResponseCreateRequest
from llmock.strategies.strategy_custom_answers import (
    ChatCustomAnswersStrategy,
    ResponseCustomAnswersStrategy,
    _build_replies,
)

TEST_API_KEY = "test-api-key"

SAMPLE_ENTRIES = [
    {"question": "How are you today?", "answer": "I'm fine. how are you?"},
    {"question": "What is 1+1?", "answer": "2"},
]


# ============================================================================
# Unit tests - _build_replies
# ============================================================================


def test_build_replies_returns_mapping() -> None:
    result = _build_replies(SAMPLE_ENTRIES)
    assert result["How are you today?"] == "I'm fine. how are you?"
    assert result["What is 1+1?"] == "2"


def test_build_replies_empty_list() -> None:
    assert _build_replies([]) == {}


def test_build_replies_skips_incomplete_entries() -> None:
    result = _build_replies([{"question": "Only question"}, {"answer": "Only answer"}])
    assert result == {}


# ============================================================================
# Unit tests - ChatCustomAnswersStrategy
# ============================================================================


def test_chat_strategy_exact_match() -> None:
    strategy = ChatCustomAnswersStrategy({"customReplies": SAMPLE_ENTRIES})
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[ChatMessageRequest(role="user", content="How are you today?")],
    )
    result = strategy.generate_response(request)
    assert len(result) == 1
    assert result[0].content == "I'm fine. how are you?"


def test_chat_strategy_no_match_returns_empty() -> None:
    strategy = ChatCustomAnswersStrategy({"customReplies": SAMPLE_ENTRIES})
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[
            ChatMessageRequest(role="user", content="Something completely different")
        ],
    )
    result = strategy.generate_response(request)
    assert result == []


def test_chat_strategy_case_sensitive() -> None:
    strategy = ChatCustomAnswersStrategy({"customReplies": SAMPLE_ENTRIES})
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[ChatMessageRequest(role="user", content="how are you today?")],
    )
    result = strategy.generate_response(request)
    assert result == []


def test_chat_strategy_strips_whitespace() -> None:
    strategy = ChatCustomAnswersStrategy({"customReplies": SAMPLE_ENTRIES})
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[ChatMessageRequest(role="user", content="  How are you today?  ")],
    )
    result = strategy.generate_response(request)
    assert len(result) == 1
    assert result[0].content == "I'm fine. how are you?"


def test_chat_strategy_no_config_key_returns_empty() -> None:
    strategy = ChatCustomAnswersStrategy({})
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[ChatMessageRequest(role="user", content="How are you today?")],
    )
    result = strategy.generate_response(request)
    assert result == []


# ============================================================================
# Unit tests - ResponseCustomAnswersStrategy
# ============================================================================


def test_response_strategy_exact_match() -> None:
    strategy = ResponseCustomAnswersStrategy({"customReplies": SAMPLE_ENTRIES})
    request = ResponseCreateRequest(model="gpt-4", input="What is 1+1?")
    result = strategy.generate_response(request)
    assert len(result) == 1
    assert result[0].content == "2"


def test_response_strategy_no_match_returns_empty() -> None:
    strategy = ResponseCustomAnswersStrategy({"customReplies": SAMPLE_ENTRIES})
    request = ResponseCreateRequest(model="gpt-4", input="Unknown question")
    result = strategy.generate_response(request)
    assert result == []


# ============================================================================
# Integration tests - Chat Completions endpoint
# ============================================================================


@pytest.fixture
def chat_config() -> Config:
    return {
        "models": [{"id": "gpt-4", "created": 1700000000, "owned_by": "openai"}],
        "api-key": TEST_API_KEY,
        "strategies": ["CustomAnswersStrategy", "MirrorStrategy"],
        "customReplies": SAMPLE_ENTRIES,
    }


@pytest.fixture
async def chat_client(chat_config: Config) -> AsyncGenerator[httpx.AsyncClient, None]:
    app = create_app(config=chat_config)
    app.dependency_overrides[get_config] = lambda: chat_config
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
    ) as http_client:
        yield http_client


async def test_chat_endpoint_returns_custom_answer(
    chat_client: httpx.AsyncClient,
) -> None:
    response = await chat_client.post(
        "/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "What is 1+1?"}],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["choices"][0]["message"]["content"] == "2"


async def test_chat_endpoint_falls_through_to_mirror(
    chat_client: httpx.AsyncClient,
) -> None:
    response = await chat_client.post(
        "/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "No match here"}],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["choices"][0]["message"]["content"] == "No match here"


# ============================================================================
# Integration tests - Responses endpoint
# ============================================================================


@pytest.fixture
def responses_config() -> Config:
    return {
        "models": [{"id": "gpt-4", "created": 1700000000, "owned_by": "openai"}],
        "api-key": TEST_API_KEY,
        "strategies": ["CustomAnswersStrategy", "MirrorStrategy"],
        "customReplies": SAMPLE_ENTRIES,
    }


@pytest.fixture
async def responses_client(
    responses_config: Config,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    app = create_app(config=responses_config)
    app.dependency_overrides[get_config] = lambda: responses_config
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
    ) as http_client:
        yield http_client


async def test_responses_endpoint_returns_custom_answer(
    responses_client: httpx.AsyncClient,
) -> None:
    response = await responses_client.post(
        "/responses",
        json={"model": "gpt-4", "input": "How are you today?"},
    )
    assert response.status_code == 200
    data = response.json()
    output_text = data["output"][0]["content"][0]["text"]
    assert output_text == "I'm fine. how are you?"


async def test_responses_endpoint_falls_through_to_mirror(
    responses_client: httpx.AsyncClient,
) -> None:
    response = await responses_client.post(
        "/responses",
        json={"model": "gpt-4", "input": "No match here"},
    )
    assert response.status_code == 200
    data = response.json()
    output_text = data["output"][0]["content"][0]["text"]
    assert output_text == "No match here"
