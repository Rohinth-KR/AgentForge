"""
Phase 3 — In-memory event bus for real-time WebSocket streaming.

Each pipeline run gets its own asyncio.Queue.  The orchestrator pushes
structured events into the queue from a background thread, and the
WebSocket endpoint consumes them asynchronously.
"""
from __future__ import annotations

import asyncio
import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class AgentEvent:
    """A single event emitted by the orchestrator during a pipeline run."""

    run_id: str
    type: str                       # agent_start | agent_output | agent_complete | run_complete | run_error
    agent: str | None = None
    content: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str)


class EventBus:
    """
    Global event bus that manages per-run async queues.

    * ``subscribe(run_id)``  — returns an ``asyncio.Queue`` for that run.
    * ``publish(event)``     — pushes an event to every subscriber on that run.
    * ``close(run_id)``      — sends a sentinel ``None`` so consumers know the
                               stream is done, then cleans up.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue[AgentEvent | None]]] = {}
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Capture the running event loop so background threads can schedule work."""
        self._loop = loop

    def subscribe(self, run_id: str) -> asyncio.Queue[AgentEvent | None]:
        """Create and return a new subscription queue for *run_id*."""
        queue: asyncio.Queue[AgentEvent | None] = asyncio.Queue()
        self._subscribers.setdefault(run_id, []).append(queue)
        return queue

    def publish(self, event: AgentEvent) -> None:
        """
        Push *event* to every subscriber queue for the given run.

        Safe to call from **any thread** — if the caller is not on the
        event-loop thread the put is scheduled via ``call_soon_threadsafe``.
        """
        queues = self._subscribers.get(event.run_id, [])
        for q in queues:
            if self._loop is not None and self._loop.is_running():
                self._loop.call_soon_threadsafe(q.put_nowait, event)
            else:
                # Fallback — same-thread (e.g. tests)
                q.put_nowait(event)

    def close(self, run_id: str) -> None:
        """Send a ``None`` sentinel to all subscribers, then remove the run."""
        for q in self._subscribers.pop(run_id, []):
            if self._loop is not None and self._loop.is_running():
                self._loop.call_soon_threadsafe(q.put_nowait, None)
            else:
                q.put_nowait(None)


# ---------------------------------------------------------------------------
# Module-level singleton — imported everywhere
# ---------------------------------------------------------------------------
event_bus = EventBus()
