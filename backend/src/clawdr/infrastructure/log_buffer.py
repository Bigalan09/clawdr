"""Ring-buffer log sink for the frontend dev console."""

from __future__ import annotations

import logging
from collections import deque
from datetime import UTC, datetime

_MAX_ENTRIES = 300
_buffer: deque[dict[str, str]] = deque(maxlen=_MAX_ENTRIES)


def log(level: str, msg: str) -> None:
    """Write to both the Python logger and the ring buffer."""
    getattr(logging.getLogger("clawdr"), level, logging.getLogger("clawdr").info)(msg)
    _buffer.append({"ts": datetime.now(UTC).isoformat(), "level": level, "msg": msg})


def entries(since: str = "") -> list[dict[str, str]]:
    """Return log entries, optionally filtered by timestamp."""
    items = list(_buffer)
    if since:
        items = [e for e in items if e["ts"] > since]
    return items
