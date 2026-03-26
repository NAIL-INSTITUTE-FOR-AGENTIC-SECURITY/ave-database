#!/usr/bin/env python3
"""
AVE Live Feed — Python Client Library

Provides both WebSocket and SSE clients for consuming the AVE Live Feed.

Usage:
    from live_client import AVELiveFeed

    feed = AVELiveFeed(api_key="your-key")

    @feed.on("ave.created")
    def on_new(event):
        print(f"New: {event['data']['ave_id']}")

    feed.connect(filters={"severity": ["critical"]})
"""

from __future__ import annotations

import asyncio
import json
import logging
import signal
import threading
from typing import Any, Callable

logger = logging.getLogger("ave-live-feed-client")


class AVELiveFeed:
    """
    Python client for the NAIL AVE Live Feed.

    Supports both WebSocket and SSE transports with automatic reconnection,
    event filtering, replay, and heartbeat monitoring.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.nailinstitute.org",
        transport: str = "websocket",  # "websocket" or "sse"
        auto_reconnect: bool = True,
        reconnect_delay: float = 5.0,
        max_reconnect_delay: float = 300.0,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.transport = transport
        self.auto_reconnect = auto_reconnect
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_delay = max_reconnect_delay

        self._handlers: dict[str, list[Callable]] = {}
        self._wildcard_handlers: list[Callable] = []
        self._filters: dict[str, Any] = {}
        self._last_sequence: int = 0
        self._connected = False
        self._loop: asyncio.AbstractEventLoop | None = None
        self._task: asyncio.Task | None = None

    def on(self, event_type: str | None = None) -> Callable:
        """
        Decorator to register an event handler.

        @feed.on("ave.created")
        def handle(event):
            ...

        @feed.on()  # wildcard — all events
        def handle_all(event):
            ...
        """
        def decorator(func: Callable) -> Callable:
            if event_type is None:
                self._wildcard_handlers.append(func)
            else:
                self._handlers.setdefault(event_type, []).append(func)
            return func
        return decorator

    def _dispatch(self, event: dict[str, Any]) -> None:
        """Dispatch an event to registered handlers."""
        etype = event.get("event_type", "")
        seq = event.get("sequence", 0)
        if seq > self._last_sequence:
            self._last_sequence = seq

        # Type-specific handlers
        for handler in self._handlers.get(etype, []):
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Handler error for {etype}: {e}")

        # Wildcard handlers
        for handler in self._wildcard_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Wildcard handler error: {e}")

    async def _connect_websocket(self) -> None:
        """Connect via WebSocket transport."""
        try:
            import websockets
        except ImportError:
            raise ImportError("Install websockets: pip install websockets")

        ws_url = self.base_url.replace("https://", "wss://").replace("http://", "ws://")
        ws_url = f"{ws_url}/ws/feed?token={self.api_key}"

        delay = self.reconnect_delay

        while True:
            try:
                async with websockets.connect(ws_url) as ws:
                    self._connected = True
                    delay = self.reconnect_delay
                    logger.info("Connected to AVE Live Feed (WebSocket)")

                    # Send subscription filters
                    if self._filters:
                        await ws.send(json.dumps({
                            "action": "subscribe",
                            "filters": self._filters,
                        }))

                    # Request replay if we have a last sequence
                    if self._last_sequence > 0:
                        await ws.send(json.dumps({
                            "action": "replay",
                            "from_sequence": self._last_sequence,
                        }))

                    async for message in ws:
                        event = json.loads(message)
                        if isinstance(event, dict) and "event_type" in event:
                            self._dispatch(event)

            except Exception as e:
                self._connected = False
                logger.warning(f"WebSocket disconnected: {e}")

                if not self.auto_reconnect:
                    break

                logger.info(f"Reconnecting in {delay}s...")
                await asyncio.sleep(delay)
                delay = min(delay * 2, self.max_reconnect_delay)

    async def _connect_sse(self) -> None:
        """Connect via SSE transport."""
        try:
            import httpx
        except ImportError:
            raise ImportError("Install httpx: pip install httpx")

        url = f"{self.base_url}/sse/feed"
        params = {}
        if self._filters.get("severity"):
            params["severity"] = ",".join(self._filters["severity"])
        if self._filters.get("categories"):
            params["category"] = ",".join(self._filters["categories"])
        if self._filters.get("event_types"):
            params["event_type"] = ",".join(self._filters["event_types"])

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "text/event-stream",
        }

        delay = self.reconnect_delay

        while True:
            try:
                async with httpx.AsyncClient(timeout=None) as client:
                    if self._last_sequence > 0:
                        headers["Last-Event-ID"] = str(self._last_sequence)

                    async with client.stream("GET", url, params=params, headers=headers) as resp:
                        self._connected = True
                        delay = self.reconnect_delay
                        logger.info("Connected to AVE Live Feed (SSE)")

                        buffer = ""
                        async for chunk in resp.aiter_text():
                            buffer += chunk
                            while "\n\n" in buffer:
                                raw_event, buffer = buffer.split("\n\n", 1)
                                data_line = ""
                                for line in raw_event.strip().split("\n"):
                                    if line.startswith("data: "):
                                        data_line = line[6:]
                                if data_line:
                                    try:
                                        event = json.loads(data_line)
                                        self._dispatch(event)
                                    except json.JSONDecodeError:
                                        pass

            except Exception as e:
                self._connected = False
                logger.warning(f"SSE disconnected: {e}")

                if not self.auto_reconnect:
                    break

                logger.info(f"Reconnecting in {delay}s...")
                await asyncio.sleep(delay)
                delay = min(delay * 2, self.max_reconnect_delay)

    def connect(
        self,
        filters: dict[str, Any] | None = None,
        blocking: bool = True,
    ) -> None:
        """
        Connect to the AVE Live Feed.

        Args:
            filters: Event filter configuration
            blocking: If True (default), blocks the calling thread
        """
        if filters:
            self._filters = filters

        coro = (
            self._connect_websocket()
            if self.transport == "websocket"
            else self._connect_sse()
        )

        if blocking:
            try:
                asyncio.run(coro)
            except KeyboardInterrupt:
                logger.info("Feed client stopped")
        else:
            self._loop = asyncio.new_event_loop()
            thread = threading.Thread(
                target=self._loop.run_until_complete,
                args=(coro,),
                daemon=True,
            )
            thread.start()

    def disconnect(self) -> None:
        """Disconnect from the feed."""
        self.auto_reconnect = False
        self._connected = False
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def last_sequence(self) -> int:
        return self._last_sequence


# ---------- CLI ----------

def main() -> None:
    """Simple CLI for testing the live feed."""
    import argparse

    parser = argparse.ArgumentParser(description="AVE Live Feed Client")
    parser.add_argument("--api-key", required=True, help="API key")
    parser.add_argument("--base-url", default="https://api.nailinstitute.org")
    parser.add_argument("--transport", choices=["websocket", "sse"], default="websocket")
    parser.add_argument("--severity", nargs="*", help="Severity filter")
    parser.add_argument("--category", nargs="*", help="Category filter")
    args = parser.parse_args()

    feed = AVELiveFeed(
        api_key=args.api_key,
        base_url=args.base_url,
        transport=args.transport,
    )

    @feed.on()
    def print_event(event: dict) -> None:
        etype = event.get("event_type", "?")
        data = event.get("data", {})
        seq = event.get("sequence", "?")
        ave_id = data.get("ave_id", "")
        name = data.get("name", "")
        sev = data.get("severity", "")
        print(f"[{seq}] {etype}: {ave_id} {name} [{sev}]" if ave_id else f"[{seq}] {etype}")

    filters = {}
    if args.severity:
        filters["severity"] = args.severity
    if args.category:
        filters["categories"] = args.category

    print(f"Connecting to AVE Live Feed ({args.transport})...")
    feed.connect(filters=filters or None)


if __name__ == "__main__":
    main()
