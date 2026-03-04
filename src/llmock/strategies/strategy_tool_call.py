"""Tool call strategies - config-driven tool call response generation.

These strategies use a configuration dict that maps tool names to their
response arguments. When tools are present in the request, the strategy
looks up each tool by name and generates a tool call response for matches.
Tools not found in the config return a text message indicating no
tool call responses are registered.

Configuration format (in config.yaml):

    tool-calls:
      calculate: '{"expression": "2+2"}'
      search: '{"query": "default search"}'

Each key is a tool/function name, and the value is the JSON arguments
string that the mock server will return as the tool call arguments.
"""

from typing import Any

from llmock.schemas.chat import ChatCompletionRequest
from llmock.schemas.responses import (
    ResponseCreateRequest,
)
from llmock.strategies.base import StrategyResponse, tool_response


class ChatToolCallStrategy:
    """Config-driven tool call strategy for Chat Completions API.

    When tools are present in the request, iterates through each tool and
    looks up the function name in the configured ``tool_calls`` dict.
    If found, a ``tool_call`` response is generated with the configured
    arguments. If not found, that tool is skipped.

    Reads ``tool-calls`` from config.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self.tool_calls: dict[str, str] = config.get("tool-calls", {})

    def generate_response(
        self, request: ChatCompletionRequest
    ) -> list[StrategyResponse]:
        """Generate tool_call response items based on tools and config."""
        return self._generate_tool_calls(request)

    def _generate_tool_calls(
        self, request: ChatCompletionRequest
    ) -> list[StrategyResponse]:
        """Generate tool_call responses for tools found in config."""
        if not request.tools:
            return []

        responses = []
        for tool in request.tools:
            func_name = tool.get("function", {}).get("name")
            if func_name and func_name in self.tool_calls:
                responses.append(tool_response(self.tool_calls[func_name], func_name))

        if not responses:
            return []

        return responses


class ResponseToolCallStrategy:
    """Config-driven tool call strategy for the Responses API.

    Same behavior as ChatToolCallStrategy but operates on Responses API
    request types (``ResponseCreateRequest``).

    Reads ``tool-calls`` from config.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self.tool_calls: dict[str, str] = config.get("tool-calls", {})

    def generate_response(
        self, request: ResponseCreateRequest
    ) -> list[StrategyResponse]:
        """Generate tool_call response items based on tools and config."""
        return self._generate_tool_calls(request)

    def _generate_tool_calls(
        self, request: ResponseCreateRequest
    ) -> list[StrategyResponse]:
        """Generate tool_call responses for tools found in config."""
        if not request.tools:
            return []

        responses = []
        for tool in request.tools:
            func_name = tool.get("name")
            if func_name and func_name in self.tool_calls:
                responses.append(tool_response(self.tool_calls[func_name], func_name))

        if not responses:
            return []

        return responses
