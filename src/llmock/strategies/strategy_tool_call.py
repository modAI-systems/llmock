"""Tool call strategies - trigger phrase–driven tool call response generation.

These strategies parse the last user message line-by-line for lines that
match the trigger pattern::

    call tool '<name>' with '<json>'

- ``<name>`` must match one of the tools declared in ``request.tools``.
- ``<json>`` must be a valid JSON string (may be empty, treated as ``{}``).

Each matching line produces one :class:`~llmock.strategies.base.StrategyResponse`
of type ``TOOL_CALL``.  If no lines match the pattern (or the named tool is
not in the request), an empty list is returned and the next strategy in the
composition chain runs.

No configuration keys are required.  Adding ``ToolCallStrategy`` to the
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
from llmock.strategies.base import StrategyResponse, tool_response
from llmock.utils.chat import (
    extract_last_user_text_chat,
    extract_last_user_text_response,
)

logger = logging.getLogger(__name__)

# Matches:  call tool '<name>' with '<args>'
_TRIGGER_RE = re.compile(r"call tool '([^']+)' with '([^']*)'")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _tool_names_from_chat(request: ChatCompletionRequest) -> set[str]:
    """Return the set of tool function names declared in a Chat request."""
    if not request.tools:
        return set()
    names: set[str] = set()
    for tool in request.tools:
        name = tool.get("function", {}).get("name")
        if name:
            names.add(name)
    return names


def _tool_names_from_response(request: ResponseCreateRequest) -> set[str]:
    """Return the set of tool names declared in a Responses request."""
    if not request.tools:
        return set()
    names: set[str] = set()
    for tool in request.tools:
        name = tool.get("name")
        if name:
            names.add(name)
    return names


def _parse_triggers(text: str, available_tools: set[str]) -> list[StrategyResponse]:
    """Scan *text* line-by-line and return tool responses for every match.

    Each line is tested against ``_TRIGGER_RE``.  A match is accepted when:

    1. The extracted tool ``<name>`` appears in ``available_tools``.
    2. The extracted ``<json>`` (or ``{}`` when empty) is valid JSON.

    Lines that do not match or fail either check are silently skipped.
    """
    responses: list[StrategyResponse] = []
    for line in text.splitlines():
        m = _TRIGGER_RE.search(line)
        if not m:
            continue
        name, args_str = m.group(1), m.group(2)
        if name not in available_tools:
            logger.debug("Trigger tool '%s' not in request.tools — skipped", name)
            continue
        effective_args = args_str if args_str else "{}"
        try:
            json.loads(effective_args)
        except json.JSONDecodeError:
            logger.warning(
                "Invalid JSON in trigger for tool '%s' — skipped: %r", name, args_str
            )
            continue
        responses.append(tool_response(effective_args, name))
    return responses


# ---------------------------------------------------------------------------
# Public strategy classes
# ---------------------------------------------------------------------------


class ChatToolCallStrategy:
    """Trigger phrase–driven tool call strategy for Chat Completions API.

    Parses the last user message for ``call tool '<name>' with '<json>'``
    lines.  Each matching line whose tool name appears in ``request.tools``
    generates a ``TOOL_CALL`` strategy response.

    No configuration is consumed.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        pass  # no config required

    def generate_response(
        self, request: ChatCompletionRequest
    ) -> list[StrategyResponse]:
        """Return tool call responses extracted from the last user message."""
        available = _tool_names_from_chat(request)
        if not available:
            return []
        text = extract_last_user_text_chat(request)
        if text is None:
            return []
        return _parse_triggers(text, available)


class ResponseToolCallStrategy:
    """Trigger phrase–driven tool call strategy for the Responses API.

    Same behaviour as :class:`ChatToolCallStrategy` but operates on
    :class:`~llmock.schemas.responses.ResponseCreateRequest` objects.

    No configuration is consumed.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        pass  # no config required

    def generate_response(
        self, request: ResponseCreateRequest
    ) -> list[StrategyResponse]:
        """Return tool call responses extracted from the last user input."""
        available = _tool_names_from_response(request)
        if not available:
            return []
        text = extract_last_user_text_response(request)
        if text is None:
            return []
        return _parse_triggers(text, available)
