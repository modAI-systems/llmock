"""Tests for the strategy factory."""

import pytest

from llmock.strategies.factory import create_chat_strategy, create_response_strategy

STRATEGY_NAMES = ["MirrorStrategy", "ErrorStrategy", "ToolCallStrategy"]


@pytest.mark.parametrize("strategy_name", STRATEGY_NAMES)
def test_create_chat_strategy(strategy_name: str) -> None:
    """Factory creates the correct chat strategy for each config name."""
    strategy = create_chat_strategy({"response-strategy": strategy_name})
    assert type(strategy).__name__ == f"Chat{strategy_name}"


@pytest.mark.parametrize("strategy_name", STRATEGY_NAMES)
def test_create_response_strategy(strategy_name: str) -> None:
    """Factory creates the correct response strategy for each config name."""
    strategy = create_response_strategy({"response-strategy": strategy_name})
    assert type(strategy).__name__ == f"Response{strategy_name}"
