"""File watching and live reload functionality.

Monitors file changes and broadcasts reload events to connected WebSocket clients,
enabling live reload during development.
"""

import asyncio
import json
from pathlib import Path
from typing import Any, List, Set

from drafter.config.system import SystemConfiguration
from starlette.websockets import WebSocket
from watchfiles import awatch


class ReloadHub:
    """Manages WebSocket connections and broadcasts reload events.

    Tracks connected WebSocket clients and sends reload messages when
    watched files change.

    Attributes:
        _clients: Set of active WebSocket connections.
        _lock: Asyncio lock for thread-safe client management.
    """

    def __init__(self) -> None:
        """Initialize empty client set and lock."""
        self._clients: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def register(self, ws: WebSocket) -> None:
        """Register a new WebSocket connection.

        Args:
            ws: WebSocket connection to register.
        """
        await ws.accept()
        async with self._lock:
            self._clients.add(ws)

    async def unregister(self, ws: WebSocket) -> None:
        """Unregister a WebSocket connection.

        Args:
            ws: WebSocket connection to remove.
        """
        async with self._lock:
            self._clients.discard(ws)

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Send a message to all connected clients.

        Removes dead connections from the client set.
        """
        payload = json.dumps(message)
        async with self._lock:
            dead: List[WebSocket] = []
            for ws in self._clients:
                try:
                    await ws.send_text(payload)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self._clients.discard(ws)

    async def broadcast_reload(self) -> None:
        """Send a full page reload message to all connected clients."""
        await self.broadcast({"type": "reload"})

    async def broadcast_student_restart(self, code: str) -> None:
        """Send a student-code restart message to all connected clients."""
        await self.broadcast({"type": "restart_student_code", "code": code})


async def ws_endpoint(websocket: WebSocket):
    """WebSocket endpoint for live reload connections.

    Accepts a connection, registers it, and keeps it open until closed.

    Args:
        websocket: Starlette WebSocket object.
    """
    hub: ReloadHub = websocket.app.state.hub  # type: ignore
    await hub.register(websocket)
    try:
        while True:
            # Keep the connection alive; client doesn't need to send messages
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        await hub.unregister(websocket)


async def _watch_and_reload(
    hub: ReloadHub,
    watch_paths: list[Path],
    system: SystemConfiguration,
    student_path: Path,
):
    """Monitor file changes and broadcast reload events.

    Watches the specified paths for any changes and triggers a reload
    broadcast when changes are detected.

    Args:
        hub: ReloadHub instance to broadcast through.
        watch_paths: List of file paths to monitor.
        system: System configuration (for future use).
    """
    # watchfiles supports multiple roots
    watched_student_path = student_path.resolve()
    async for changes in awatch(*watch_paths, stop_event=None):
        changed_paths = {Path(path).resolve() for _, path in changes}
        if changed_paths and changed_paths.issubset({watched_student_path}):
            try:
                await hub.broadcast_student_restart(
                    watched_student_path.read_text(encoding="utf-8")
                )
            except Exception:
                await hub.broadcast_reload()
        else:
            # Debounce simple bursts by scheduling a single broadcast per tick
            await hub.broadcast_reload()
