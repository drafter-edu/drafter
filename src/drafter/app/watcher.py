import asyncio
import json
from pathlib import Path
from typing import List, Set

from starlette.websockets import WebSocket
from watchfiles import awatch

from drafter.config.app_server import AppServerConfiguration


class ReloadHub:
    """Tracks live WS connections; broadcasts reload on file changes."""

    def __init__(self) -> None:
        self._clients: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def register(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._clients.add(ws)

    async def unregister(self, ws: WebSocket) -> None:
        async with self._lock:
            self._clients.discard(ws)

    async def broadcast_reload(self) -> None:
        payload = json.dumps({"type": "reload"})
        async with self._lock:
            dead: List[WebSocket] = []
            for ws in self._clients:
                try:
                    await ws.send_text(payload)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self._clients.discard(ws)


async def ws_endpoint(websocket: WebSocket):
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
    hub: ReloadHub, watch_paths: list[Path], config: AppServerConfiguration
):
    # watchfiles supports multiple roots
    async for changes in awatch(*watch_paths, stop_event=None):
        # Debounce simple bursts by scheduling a single broadcast per tick
        await hub.broadcast_reload()
