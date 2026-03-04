"""Error strategies - trigger phrase–driven error response generation.

These strategies scan the last user message line-by-line for the pattern::

    raise error {"code": 429, "message": "Rate limit exceeded"}

The JSON payload must contain ``code`` (integer HTTP status code) and
``message`` (string).  Optional fields: ``type`` (OpenAI error type string)
and ``error_code`` (OpenAI error code string).  The first matching line
wins; subsequent lines are ignored.

No configuration keys are required.  Adding ``ErrorStrategy`` to the
``strategies`` list in ``config.yaml`` is sufficient:

    strategies:
      - ErrorStrategy
      - ToolCallStrategy
      - MirrorStrategy
"""

import json
import logging
import re
from typing import Any

from llmock.schemas.chat import ChatCompletionRequest
from llmock.schemas.responses import ResponseCreateRequest
from llmock.strategies.base import StrategyResponse, error_response
from llmock.utils.chat import (
    extract_last_user_text_chat,
    extract_last_user_text_response,
)

logger = logging.getLogger(__name__)

# Matches:  raise error <json>   (captures everything after "raise error ")
_ERROR_TRIGGER_RE = re.compile(r"raise error\s+(\{.+\})")


class ChatErrorStrategy:
    """Trigger-phrase error strategy for Chat Completions API.

    Scans the last user message for ``raise error <json>`` lines.  Returns
    an ERROR response when a valid trigger is found, or an empty list
    otherwise (so the next strategy in the composition chain runs).
    """

    def __init__(self, config: dict[str, Any]) -> None:  # noqa: ARG002
        pass

    def generate_response(
        self, request: ChatCompletionRequest
    ) -> list[StrategyResponse]:
        """Check if the last user message contains a raise error trigger."""
        content = extract_last_user_text_chat(request)
        if content is None:
            return []
        return _parse_error_trigger(content)


class ResponseErrorStrategy:
    """Trigger-phrase error strategy for the Responses API.

    Same behavior as ChatErrorStrategy but operates on Responses API
    request types.
    """

    def __init__(self, config: dict[str, Any]) -> None:  # noqa: ARG002
        pass

    def generate_response(
        self, request: ResponseCreateRequest
    ) -> list[StrategyResponse]:
        """Check if the input message contains a raise error trigger."""
        content = extract_last_user_text_response(request)
        if content is None:
            return []
        return _parse_error_trigger(content)


def _parse_error_trigger(text: str) -> list[StrategyResponse]:
    """Scan *text* line-by-line for ``raise error <json>`` trigger phrases.

    The first matching line with valid JSON containing at least ``code``
    (integer) and ``message`` (string) produces a single ERROR response.
    Remaining lines are not checked.

    Returns a list containing the single ERROR response, or an empty list
    if no valid trigger is found.
    """
    for line in text.splitlines():
        m = _ERROR_TRIGGER_RE.search(line)
        if not m:
            continue
        raw = m.group(1)
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in 'raise error' trigger — skipped: %r", raw)
            continue
        if not isinstance(payload.get("code"), int) or not isinstance(
            payload.get("message"), str
        ):
            logger.warning(
                "'raise error' trigger JSON missing required 'code' (int) or "
                "'message' (str) — skipped: %r",
                raw,
            )
            continue
        return [
            error_response(
                message=payload["message"],
                status_code=payload["code"],
                error_type=payload.get("type"),
                error_code=payload.get("error_code"),
            )
        ]
    return []
