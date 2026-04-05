"""History endpoints — no authentication required."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from llmock import history_store

router = APIRouter(prefix="", tags=["history"])


class HistoryResponse(BaseModel):
    """Response model for the history endpoint."""

    requests: list[dict[str, Any]]


@router.get("/history", response_model=HistoryResponse)
async def get_history() -> HistoryResponse:
    """Return all received requests in the order they were received."""
    return HistoryResponse(requests=history_store.get_all())


@router.delete("/history", status_code=204)
async def reset_history() -> None:
    """Clear the recorded request history."""
    history_store.reset()
