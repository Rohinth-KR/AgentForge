"""
Phase 3 — WebSocket streaming endpoint.

Clients connect to  ``WS /api/run/{run_id}/stream``  and receive
real-time ``AgentEvent`` JSON messages as the pipeline executes.
"""
from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.event_bus import event_bus

router = APIRouter(tags=["streaming"])


@router.websocket("/api/run/{run_id}/stream")
async def stream_run(websocket: WebSocket, run_id: str) -> None:
    """
    Stream agent events for a specific pipeline run over WebSocket.

    Protocol
    --------
    1. Client opens the WebSocket connection.
    2. Server pushes JSON-encoded ``AgentEvent`` messages as they happen.
    3. When the run finishes (or errors), a final event with
       ``type = "run_complete"`` or ``type = "run_error"`` is sent,
       followed by a clean close.
    """
    await websocket.accept()
    queue = event_bus.subscribe(run_id)

    try:
        while True:
            # Wait for the next event (or sentinel None = stream over)
            event = await queue.get()
            if event is None:
                # Sentinel — pipeline finished, close gracefully
                break

            await websocket.send_text(event.to_json())

            # If this was a terminal event, stop after sending it
            if event.type in ("run_complete", "run_error"):
                break
    except WebSocketDisconnect:
        # Client disconnected early — nothing to do
        pass
    except Exception:
        # Unexpected error — close with an internal-error code
        try:
            await websocket.close(code=1011)
        except Exception:
            pass
    else:
        try:
            await websocket.close(code=1000)
        except Exception:
            pass
