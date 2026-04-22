"""In-memory async event bus for domain events."""

from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events."""

    event_type: str


@dataclass(frozen=True)
class SessionStateChanged(DomainEvent):
    """Fired when a session transitions state."""

    event_type: str = field(default="session.state", init=False)
    project_id: str = ""
    state: str = ""
    started_at: str | None = None
    url: str | None = None


@dataclass(frozen=True)
class ProjectListChanged(DomainEvent):
    """Fired when projects are added or removed."""

    event_type: str = field(default="project.list_changed", init=False)


class EventBus:
    """Fan-out async event bus. Subscribers get an asyncio.Queue."""

    def __init__(self) -> None:
        self._subscribers: list[asyncio.Queue[DomainEvent]] = []
        self._lock = asyncio.Lock()

    async def publish(self, event: DomainEvent) -> None:
        """Push an event to all subscriber queues."""
        async with self._lock:
            for queue in self._subscribers:
                with contextlib.suppress(asyncio.QueueFull):
                    queue.put_nowait(event)

    async def subscribe(self) -> asyncio.Queue[DomainEvent]:
        """Create and return a new subscription queue."""
        queue: asyncio.Queue[DomainEvent] = asyncio.Queue(maxsize=256)
        async with self._lock:
            self._subscribers.append(queue)
        return queue

    async def unsubscribe(self, queue: asyncio.Queue[DomainEvent]) -> None:
        """Remove a subscription queue."""
        async with self._lock:
            with contextlib.suppress(ValueError):
                self._subscribers.remove(queue)

    def to_dict(self, event: DomainEvent) -> dict[str, Any]:
        """Serialize a domain event to a dict for JSON transport."""
        if isinstance(event, SessionStateChanged):
            result: dict[str, Any] = {
                "type": event.event_type,
                "project_id": event.project_id,
                "state": event.state,
            }
            if event.started_at is not None:
                result["started_at"] = event.started_at
            if event.url is not None:
                result["url"] = event.url
            return result
        if isinstance(event, ProjectListChanged):
            return {"type": event.event_type}
        return {"type": event.event_type}
