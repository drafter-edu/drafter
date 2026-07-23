"""File watching and live reload functionality.

Monitors file changes and broadcasts reload events to connected WebSocket clients,
enabling live reload during development.
"""

import asyncio
import json
from pathlib import Path
from typing import Any, List, Set
from dataclasses import dataclass

from drafter.config.system import SystemConfiguration
from starlette.websockets import WebSocket
from watchfiles import awatch


@dataclass
class WatchedPath:
    """Represents a file system path to be watched for changes.

    Attributes:
        directory: The file system path to watch.
        full_reload: Whether to trigger a full page reload when changes are detected in this path, or just restart the code.
    """

    directory: Path
    full_reload: bool = True


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
    watch_paths: list[WatchedPath],
    system: SystemConfiguration,
    student_path: Path,
):
    """Monitor file changes and broadcast reload or restart events.

    Watches all the given paths. When a change falls under a path marked
    `full_reload=False`, it first attempts a student-restart broadcast
    carrying the current contents of `student_path`, falling back to a
    full page reload broadcast if reading or broadcasting fails. Changes
    anywhere else trigger a full page reload broadcast.

    Args:
        hub: ReloadHub instance to broadcast through.
        watch_paths: List of paths to monitor; each entry's `full_reload`
            flag decides between a page reload and a student-code restart.
        system: System configuration (for future use).
        student_path: Path to the student's main code file, whose
            contents are sent with student-restart broadcasts.
    """
    # watchfiles supports multiple roots
    watched_student_path = student_path.resolve()
    restart_paths = {wp.directory.resolve() for wp in watch_paths if not wp.full_reload}
    async for changes in awatch(*[wp.directory for wp in watch_paths], stop_event=None):
        changed_paths = {Path(path).resolve() for _, path in changes}
        print("Checking for", restart_paths, "in", changed_paths)
        if changed_paths and any(
            changed_path.is_relative_to(restart_path)
            for changed_path in changed_paths
            for restart_path in restart_paths
        ):
            try:
                print(
                    "Trying to restart student code due to changes in:", changed_paths
                )
                await hub.broadcast_student_restart(
                    watched_student_path.read_text(encoding="utf-8")
                )
            except Exception:
                print("Failed. Reloading instead.")
                await hub.broadcast_reload()
        else:
            print(
                "Changes detected in watched paths, broadcasting reload:", changed_paths
            )
            # Debounce simple bursts by scheduling a single broadcast per tick
            await hub.broadcast_reload()
