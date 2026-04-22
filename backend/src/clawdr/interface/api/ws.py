"""WebSocket endpoint for real-time event streaming."""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

if TYPE_CHECKING:
    from clawdr.application.event_bus import EventBus

router = APIRouter()

_event_bus: EventBus | None = None


def init_ws_router(event_bus: EventBus) -> None:
    """Wire dependencies. Called once at app startup."""
    global _event_bus
    _event_bus = event_bus


def _bus() -> EventBus:
    assert _event_bus is not None, "WS router not initialized"
    return _event_bus


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    """Stream domain events to the client over WebSocket."""
    await ws.accept()
    bus = _bus()
    queue = await bus.subscribe()
    try:
        while True:
            event = await queue.get()
            payload = bus.to_dict(event)
            await ws.send_text(json.dumps(payload))
    except WebSocketDisconnect:
        pass
    except asyncio.CancelledError:
        pass
    finally:
        await bus.unsubscribe(queue)
