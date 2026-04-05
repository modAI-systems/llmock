"""In-memory store for recording incoming API requests."""

from datetime import UTC, datetime
from typing import Any

_history: list[dict[str, Any]] = []


def add_entry(method: str, path: str, body: Any) -> None:
    """Append a request entry to the history."""
    _history.append(
        {
            "method": method,
            "path": path,
            "body": body,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )


def get_all() -> list[dict[str, Any]]:
    """Return all recorded request entries in order."""
    return list(_history)


def reset() -> None:
    """Clear all recorded request entries."""
    _history.clear()
