"""Tool call strategies - trigger phrase–driven tool call response generation.

These strategies parse the last user message line-by-line for lines that
match the trigger pattern::

    call tool '<name>' with '<json>'

- ``<name>`` is used verbatim — no check against ``request.tools`` is made.
- ``<json>`` must be a valid JSON string (may be empty, treated as ``{}``).

Each matching line produces one :class:`~llmock.strategies.base.StrategyResponse`
of type ``TOOL_CALL``.  If no lines match the pattern, an empty list is
returned and the next strategy in the composition chain runs.

No configuration keys are required.  Adding ``ToolCallStrategy`` to the
``strategies`` list in ``config.yaml`` is sufficient:

    strategies:
      - ErrorStrategy
      - ToolCallStrategy
      - MirrorStrategy
"""

import re
from typing import Any

from llmock.schemas.chat import ChatCompletionRequest
from llmock.schemas.responses import ResponseCreateRequest
from llmock.strategies.base import StrategyResponse, tool_response
from llmock.utils.chat import (
    extract_last_user_text_chat,
    extract_last_user_text_response,
)

# Matches:  call tool '<name>' with '<args>'
_TRIGGER_RE = re.compile(r"call tool '([^']+)' with '([^']*)'")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _parse_triggers(text: str) -> list[StrategyResponse]:
    """Scan *text* line-by-line and return tool responses for every match.

    Each line is tested against ``_TRIGGER_RE``.  A match produces a
    ``TOOL_CALL`` response using the extracted name and arguments verbatim;
    no check against ``request.tools`` is performed.

    Lines that do not match or contain invalid JSON args are silently skipped.
    """
    responses: list[StrategyResponse] = []
    for line in text.splitlines():
        m = _TRIGGER_RE.search(line)
        if not m:
            continue
        name, args_str = m.group(1), m.group(2)
        effective_args = args_str if args_str else "{}"
        responses.append(tool_response(effective_args, name))
    return responses


# ---------------------------------------------------------------------------
# Public strategy classes
# ---------------------------------------------------------------------------


class ChatToolCallStrategy:
    """Trigger phrase–driven tool call strategy for Chat Completions API.

    Parses the last user message for ``call tool '<name>' with '<json>'``
    lines.  Each matching line generates a ``TOOL_CALL`` strategy response;
    no validation against ``request.tools`` is performed.

    No configuration is consumed.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        pass  # no config required

    def generate_response(
        self, request: ChatCompletionRequest
    ) -> list[StrategyResponse]:
        """Return tool call responses extracted from the last user message.

        Returns an empty list when the most recent non-system message is not
        from the user — this prevents the strategy from re-triggering every
        cycle of an agentic loop where the original trigger still sits earlier
        in the conversation history.
        """
        # Only process the trigger when the last non-system turn is the user's.
        last_role = next(
            (msg.role for msg in reversed(request.messages) if msg.role != "system"),
            None,
        )
        if last_role != "user":
            return []
        text = extract_last_user_text_chat(request)
        if text is None:
            return []
        return _parse_triggers(text)


class ResponseToolCallStrategy:
    """Trigger phrase–driven tool call strategy for the Responses API.

    Same behaviour as :class:`ChatToolCallStrategy` but operates on
    :class:`~llmock.schemas.responses.ResponseCreateRequest` objects.  No
    validation against ``request.tools`` is performed.

    No configuration is consumed.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        pass  # no config required

    def generate_response(
        self, request: ResponseCreateRequest
    ) -> list[StrategyResponse]:
        """Return tool call responses extracted from the last user input.

        Returns an empty list when the most recent item in the input list is
        not a user message — this prevents the strategy from re-triggering
        every cycle of an agentic loop.

        When ``request.input`` is a plain string it is always treated as a
        fresh user turn.
        """
        # A plain string is always a fresh user turn — proceed normally.
        if not isinstance(request.input, str):
            # For a list input, the last item must be a user-role message.
            last_item = request.input[-1] if request.input else None
            if last_item is None:
                return []
            last_role = getattr(last_item, "role", None)
            if last_role != "user":
                # Covers FunctionCallOutputItem (no role) and assistant items.
                return []
        text = extract_last_user_text_response(request)
        if text is None:
            return []
        return _parse_triggers(text)
