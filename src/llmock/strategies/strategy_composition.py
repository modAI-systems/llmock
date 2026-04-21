"""Composition strategy - chains multiple strategies in priority order.

Reads the ``strategies`` list from config and creates each sub-strategy via
the factory registry.  When ``generate_response`` is called, the strategies
are tried in order; the first one that returns a **non-empty** list wins and
its result is returned immediately.  Remaining strategies are not called.

If ``strategies`` is missing from config, defaults to
``["ErrorStrategy", "ToolCallStrategy", "MirrorStrategy"]``.

This strategy is **not** registered in the factory — it wraps the factory
internally and is the top-level strategy instantiated by the routers.
"""

import logging
from typing import Any

from llmock.schemas.chat import ChatCompletionRequest
from llmock.schemas.responses import ResponseCreateRequest
from llmock.strategies.base import StrategyResponse
from llmock.strategies.factory import _STRATEGIES

logger = logging.getLogger(__name__)

_DEFAULT_STRATEGIES = [
    "ErrorStrategy",
    "CustomAnswersStrategy",
    "ToolCallStrategy",
    "MirrorStrategy",
]


class ChatCompositionStrategy:
    """Composition strategy for the Chat Completions API.

    Creates sub-strategies from the ``strategies`` config list and runs
    them in order.  The first strategy that returns a non-empty list of
    :class:`StrategyResponse` items wins.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        strategy_names: list[str] = config.get("strategies", _DEFAULT_STRATEGIES)
        self.strategies = []
        for name in strategy_names:
            pair = _STRATEGIES.get(name)
            if pair is None:
                logger.warning("Unknown strategy '%s' — skipped", name)
                continue
            self.strategies.append(pair[0](config))

    def generate_response(
        self, request: ChatCompletionRequest
    ) -> list[StrategyResponse]:
        """Run strategies in order, returning the first non-empty result."""
        for strategy in self.strategies:
            result = strategy.generate_response(request)
            if result:
                return result
        return []


class ResponseCompositionStrategy:
    """Composition strategy for the Responses API.

    Creates sub-strategies from the ``strategies`` config list and runs
    them in order.  The first strategy that returns a non-empty list of
    :class:`StrategyResponse` items wins.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        strategy_names: list[str] = config.get("strategies", _DEFAULT_STRATEGIES)
        self.strategies = []
        for name in strategy_names:
            pair = _STRATEGIES.get(name)
            if pair is None:
                logger.warning("Unknown strategy '%s' — skipped", name)
                continue
            self.strategies.append(pair[1](config))

    def generate_response(
        self, request: ResponseCreateRequest
    ) -> list[StrategyResponse]:
        """Run strategies in order, returning the first non-empty result."""
        for strategy in self.strategies:
            result = strategy.generate_response(request)
            if result:
                return result
        return []
