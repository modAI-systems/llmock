"""Custom answers strategy - return preconfigured answers for exact-match questions.

Reads the ``customReplies`` list directly from config.  The list must have
the following structure in ``config.yaml``::

    customReplies:
      - question: How are you today?
        answer: I'm fine. how are you?
      - question: What is 1+1?
        answer: 2

When the last user message exactly matches a ``question`` (case-sensitive,
stripped of leading/trailing whitespace), the corresponding ``answer`` is
returned as a text response.  If no match is found, an empty list is
returned so the next strategy in the composition chain runs.

If ``customReplies`` is not present in config the strategy passes through
silently (empty list).
"""

import logging
from typing import Any

from llmock.schemas.chat import ChatCompletionRequest
from llmock.schemas.responses import ResponseCreateRequest
from llmock.strategies.base import StrategyResponse, text_response
from llmock.utils.chat import (
    extract_last_user_text_chat,
    extract_last_user_text_response,
)

logger = logging.getLogger(__name__)

CONFIG_KEY = "customReplies"


def _build_replies(entries: list[Any]) -> dict[str, str]:
    """Build a question→answer mapping from a list of config entries."""
    return {
        str(entry["question"]).strip(): str(entry["answer"])
        for entry in entries
        if isinstance(entry, dict) and "question" in entry and "answer" in entry
    }


def _match(content: str | None, replies: dict[str, str]) -> list[StrategyResponse]:
    """Return a response if *content* exactly matches a question, else []."""
    if content is None:
        return []
    answer = replies.get(content.strip())
    if answer is None:
        return []
    return [text_response(answer)]


class ChatCustomAnswersStrategy:
    """Exact-match custom answers strategy for the Chat Completions API."""

    def __init__(self, config: dict[str, Any]) -> None:
        entries = config.get(CONFIG_KEY, [])
        self._replies: dict[str, str] = _build_replies(entries)

    def generate_response(
        self, request: ChatCompletionRequest
    ) -> list[StrategyResponse]:
        content = extract_last_user_text_chat(request)
        return _match(content, self._replies)


class ResponseCustomAnswersStrategy:
    """Exact-match custom answers strategy for the Responses API."""

    def __init__(self, config: dict[str, Any]) -> None:
        entries = config.get(CONFIG_KEY, [])
        self._replies: dict[str, str] = _build_replies(entries)

    def generate_response(
        self, request: ResponseCreateRequest
    ) -> list[StrategyResponse]:
        content = extract_last_user_text_response(request)
        return _match(content, self._replies)
