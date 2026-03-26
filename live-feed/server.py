#!/usr/bin/env python3
"""
AVE Live Feed Server — WebSocket & SSE streaming endpoint.

Publishes real-time AVE card events to connected clients with filtering,
authentication, replay, and heartbeat support.

Usage:
    uvicorn server:app --host 0.0.0.0 --port 8001 --workers 1

Environment variables:
    REDIS_URL          — Redis connection URL (default: redis://localhost:6379)
    API_KEY_HEADER     — Auth header name (default: Authorization)
    HEARTBEAT_INTERVAL — Seconds between heartbeats (default: 30)
    MAX_REPLAY_EVENTS  — Maximum events to replay (default: 10000)
    CORS_ORIGINS       — Comma-separated allowed origins (default: *)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from collections import deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, AsyncGenerator

from fastapi import (
    FastAPI,
    Query,
    WebSocket,
    WebSocketDisconnect,
    Request,
    HTTPException,
    Depends,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# ---------- Configuration ----------

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", "30"))
MAX_REPLAY_EVENTS = int(os.getenv("MAX_REPLAY_EVENTS", "10000"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ave-live-feed")


# ---------- Event Types ----------

class EventType(str, Enum):
    AVE_CREATED = "ave.created"
    AVE_UPDATED = "ave.updated"
    AVE_DEPRECATED = "ave.deprecated"
    AVE_STATUS_CHANGED = "ave.status_changed"
    AVE_SEVERITY_CHANGED = "ave.severity_changed"
    AVSS_RECALCULATED = "avss.recalculated"
    FEED_HEARTBEAT = "feed.heartbeat"


class FeedEvent(BaseModel):
    event_id: str
    event_type: str
    timestamp: str
    sequence: int
    data: dict[str, Any]
    metadata: dict[str, Any] = {}


# ---------- Event Store (in-memory ring buffer) ----------

@dataclass
class EventStore:
    """Thread-safe ring buffer for event replay."""
    max_size: int = MAX_REPLAY_EVENTS
    _events: deque[FeedEvent] = field(default_factory=deque)
    _sequence: int = 0

    def append(self, event: FeedEvent) -> None:
        if len(self._events) >= self.max_size:
            self._events.popleft()
        self._events.append(event)

    def get_since(self, sequence: int, limit: int = 1000) -> list[FeedEvent]:
        return [e for e in self._events if e.sequence > sequence][:limit]

    def next_sequence(self) -> int:
        self._sequence += 1
        return self._sequence

    @property
    def last_sequence(self) -> int:
        return self._sequence


event_store = EventStore()


# ---------- Client Registry ----------

@dataclass
class ClientFilter:
    event_types: list[str] | None = None
    severity: list[str] | None = None
    categories: list[str] | None = None
    frameworks: list[str] | None = None

    def matches(self, event: FeedEvent) -> bool:
        if self.event_types and event.event_type not in self.event_types:
            return False
        data = event.data
        if self.severity and data.get("severity") not in self.severity:
            # Heartbeats and non-card events pass through
            if event.event_type != EventType.FEED_HEARTBEAT and "severity" in data:
                return False
        if self.categories and data.get("category") not in self.categories:
            if event.event_type != EventType.FEED_HEARTBEAT and "category" in data:
                return False
        if self.frameworks:
            card_frameworks = set(data.get("environment", {}).get("agent_frameworks", []))
            if card_frameworks and not card_frameworks & set(self.frameworks):
                return False
        return True


@dataclass
class ConnectedClient:
    client_id: str
    client_type: str  # "ws" or "sse"
    filters: ClientFilter
    connected_at: float
    queue: asyncio.Queue[FeedEvent] = field(default_factory=lambda: asyncio.Queue(maxsize=1000))


class ClientRegistry:
    def __init__(self) -> None:
        self._clients: dict[str, ConnectedClient] = {}

    def register(self, client: ConnectedClient) -> None:
        self._clients[client.client_id] = client
        logger.info(
            f"Client connected: {client.client_id} ({client.client_type}) "
            f"[total: {len(self._clients)}]"
        )

    def unregister(self, client_id: str) -> None:
        self._clients.pop(client_id, None)
        logger.info(f"Client disconnected: {client_id} [total: {len(self._clients)}]")

    async def broadcast(self, event: FeedEvent) -> None:
        for client in list(self._clients.values()):
            if client.filters.matches(event):
                try:
                    client.queue.put_nowait(event)
                except asyncio.QueueFull:
                    logger.warning(f"Queue full for client {client.client_id}, dropping event")

    @property
    def ws_count(self) -> int:
        return sum(1 for c in self._clients.values() if c.client_type == "ws")

    @property
    def sse_count(self) -> int:
        return sum(1 for c in self._clients.values() if c.client_type == "sse")

    @property
    def total(self) -> int:
        return len(self._clients)


registry = ClientRegistry()


# ---------- Event Publishing ----------

_events_published_total = 0


async def publish_event(
    event_type: str,
    data: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> FeedEvent:
    """Create and broadcast an event to all connected clients."""
    global _events_published_total

    seq = event_store.next_sequence()
    event = FeedEvent(
        event_id=f"evt_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{seq:06d}",
        event_type=event_type,
        timestamp=datetime.now(timezone.utc).isoformat(),
        sequence=seq,
        data=data,
        metadata=metadata or {"schema_version": "2.0.0", "source": "nail-ave-database"},
    )

    event_store.append(event)
    await registry.broadcast(event)
    _events_published_total += 1
    return event


# ---------- Heartbeat Task ----------

async def heartbeat_task() -> None:
    """Send periodic heartbeat events."""
    while True:
        await asyncio.sleep(HEARTBEAT_INTERVAL)
        await publish_event(
            EventType.FEED_HEARTBEAT,
            {"timestamp": datetime.now(timezone.utc).isoformat()},
        )


# ---------- Authentication ----------

async def verify_api_key(request: Request) -> str:
    """Verify API key from Authorization header."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        # In production: validate against key store
        if token:
            return token
    raise HTTPException(status_code=401, detail="Invalid or missing API key")


# ---------- FastAPI App ----------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start background tasks on startup."""
    task = asyncio.create_task(heartbeat_task())
    logger.info("AVE Live Feed server started")
    yield
    task.cancel()
    logger.info("AVE Live Feed server stopped")


app = FastAPI(
    title="AVE Live Feed",
    description="Real-time streaming API for NAIL AVE vulnerability intelligence",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- SSE Endpoint ----------

@app.get("/sse/feed")
async def sse_feed(
    request: Request,
    api_key: str = Depends(verify_api_key),
    severity: str | None = Query(None, description="Comma-separated severity filter"),
    category: str | None = Query(None, description="Comma-separated category filter"),
    event_type: str | None = Query(None, description="Comma-separated event type filter"),
    framework: str | None = Query(None, description="Comma-separated framework filter"),
    last_event_id: str | None = Query(None, alias="Last-Event-ID"),
) -> StreamingResponse:
    """Server-Sent Events endpoint for real-time AVE feed."""

    filters = ClientFilter(
        event_types=event_type.split(",") if event_type else None,
        severity=severity.split(",") if severity else None,
        categories=category.split(",") if category else None,
        frameworks=framework.split(",") if framework else None,
    )

    client = ConnectedClient(
        client_id=f"sse_{uuid.uuid4().hex[:12]}",
        client_type="sse",
        filters=filters,
        connected_at=time.time(),
    )
    registry.register(client)

    # Replay missed events if Last-Event-ID provided
    if last_event_id:
        try:
            replay_seq = int(last_event_id)
            missed = event_store.get_since(replay_seq)
            for evt in missed:
                if filters.matches(evt):
                    await client.queue.put(evt)
        except (ValueError, TypeError):
            pass

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(client.queue.get(), timeout=1.0)
                    yield (
                        f"id: {event.sequence}\n"
                        f"event: {event.event_type}\n"
                        f"data: {event.model_dump_json()}\n\n"
                    )
                except asyncio.TimeoutError:
                    continue
        finally:
            registry.unregister(client.client_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ---------- WebSocket Endpoint ----------

@app.websocket("/ws/feed")
async def ws_feed(
    websocket: WebSocket,
    token: str | None = Query(None),
) -> None:
    """WebSocket endpoint for real-time AVE feed."""

    # Auth
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    await websocket.accept()

    client = ConnectedClient(
        client_id=f"ws_{uuid.uuid4().hex[:12]}",
        client_type="ws",
        filters=ClientFilter(),
        connected_at=time.time(),
    )
    registry.register(client)

    async def sender() -> None:
        """Send events from queue to WebSocket."""
        try:
            while True:
                event = await client.queue.get()
                await websocket.send_text(event.model_dump_json())
        except Exception:
            pass

    async def receiver() -> None:
        """Receive filter updates from WebSocket."""
        try:
            while True:
                raw = await websocket.receive_text()
                msg = json.loads(raw)
                action = msg.get("action")

                if action == "subscribe":
                    f = msg.get("filters", {})
                    client.filters = ClientFilter(
                        event_types=f.get("event_types"),
                        severity=f.get("severity"),
                        categories=f.get("categories"),
                        frameworks=f.get("frameworks"),
                    )
                    await websocket.send_text(json.dumps({
                        "action": "subscribed",
                        "filters": f,
                    }))

                elif action == "replay":
                    from_seq = msg.get("from_sequence", 0)
                    missed = event_store.get_since(from_seq)
                    for evt in missed:
                        if client.filters.matches(evt):
                            await websocket.send_text(evt.model_dump_json())
                    await websocket.send_text(json.dumps({
                        "action": "replay_complete",
                        "events_replayed": len(missed),
                    }))

                elif action == "ping":
                    await websocket.send_text(json.dumps({"action": "pong"}))

        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger.error(f"WebSocket receiver error: {e}")

    try:
        await asyncio.gather(sender(), receiver())
    finally:
        registry.unregister(client.client_id)


# ---------- REST Endpoints ----------

@app.get("/api/v2/events")
async def get_events(
    api_key: str = Depends(verify_api_key),
    since: str | None = Query(None, description="ISO8601 timestamp"),
    since_sequence: int | None = Query(None, description="Sequence number"),
    limit: int = Query(100, ge=1, le=1000),
) -> dict:
    """REST polling fallback — get events since a timestamp or sequence."""
    if since_sequence is not None:
        events = event_store.get_since(since_sequence, limit=limit)
    else:
        events = event_store.get_since(0, limit=limit)

    return {
        "events": [e.model_dump() for e in events],
        "count": len(events),
        "last_sequence": event_store.last_sequence,
    }


@app.get("/api/v2/feed/health")
async def feed_health() -> dict:
    """Health check for the live feed service."""
    return {
        "status": "healthy",
        "connections": {
            "websocket": registry.ws_count,
            "sse": registry.sse_count,
            "total": registry.total,
        },
        "events_total": _events_published_total,
        "last_event_sequence": event_store.last_sequence,
        "uptime_seconds": int(time.time() - _start_time),
    }


@app.post("/api/v2/events/publish")
async def publish_event_endpoint(
    event_type: str = Query(...),
    api_key: str = Depends(verify_api_key),
    request: Request = None,
) -> dict:
    """Internal endpoint to publish events (used by AVE database on card changes)."""
    body = await request.json()
    event = await publish_event(event_type, data=body)
    return {"event_id": event.event_id, "sequence": event.sequence}


_start_time = time.time()


# ---------- Prometheus Metrics ----------

@app.get("/metrics")
async def prometheus_metrics() -> str:
    """Prometheus-compatible metrics endpoint."""
    lines = [
        f'ave_feed_connections_active{{type="websocket"}} {registry.ws_count}',
        f'ave_feed_connections_active{{type="sse"}} {registry.sse_count}',
        f"ave_feed_events_published_total {_events_published_total}",
        f"ave_feed_last_sequence {event_store.last_sequence}",
        f"ave_feed_uptime_seconds {int(time.time() - _start_time)}",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
