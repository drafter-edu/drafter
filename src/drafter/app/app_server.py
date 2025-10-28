import asyncio
import json
import os
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Set

from starlette.applications import Starlette
from starlette.responses import HTMLResponse, Response
from starlette.routing import Route, WebSocketRoute, Mount
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket
import uvicorn
from watchfiles import awatch, Change

from drafter.app.templating import render_index_html
from drafter.app.utils import pkg_assets_dir, pkg_scaffold_dir


@dataclass
class DevConfig:
    title: str
    user_path: Path
    inline_py: bool
    host: str
    port: int

    @property
    def ws_url(self) -> str:
        return f"ws://{self.host}:{self.port}/ws"


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


async def index(req) -> Response:
    app: Starlette = req.app  # type: ignore
    cfg: DevConfig = app.state.cfg
    user_code = cfg.user_path.read_text(encoding="utf-8")
    html = render_index_html(
        title=cfg.title,
        inline_py=cfg.inline_py,
        user_code=user_code if cfg.inline_py else None,
        python_url=str(cfg.user_path) if not cfg.inline_py else None,
        dev_ws_url=cfg.ws_url,
        assets_url_override="assets",  # we mount package assets under /assets
    )
    return HTMLResponse(html)


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


def _watch_paths(cfg: DevConfig) -> Iterable[Path]:
    yield cfg.user_path
    # Optionally watch template & assets for live dev on your lib:
    yield pkg_scaffold_dir() / "index.template.html"
    assets = pkg_assets_dir()
    if assets.exists():
        yield assets


async def _watch_and_reload(hub: ReloadHub, cfg: DevConfig):
    # watchfiles supports multiple roots
    roots = list(_watch_paths(cfg))
    async for changes in awatch(*roots, stop_event=None):
        # Debounce simple bursts by scheduling a single broadcast per tick
        await hub.broadcast_reload()


def make_app(cfg: DevConfig) -> Starlette:
    assets_dir = pkg_assets_dir()
    routes = [
        Route("/", index),
        WebSocketRoute("/ws", ws_endpoint),
        Mount("/assets", app=StaticFiles(directory=str(assets_dir)), name="assets"),
    ]
    app = Starlette(routes=routes)
    app.state.cfg = cfg
    app.state.hub = ReloadHub()
    return app


def serve_app_once(
    user_file: str,
    title: str,
    host: str = "localhost",
    port: int = 8080,
    inline_py: bool = True,
    open_browser: bool = True,
):
    cfg = DevConfig(
        title=title,
        user_path=Path(user_file).resolve(),
        inline_py=inline_py,
        host=host,
        port=port,
    )
    app = make_app(cfg)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Background watcher task
    async def supervisor():
        watcher = asyncio.create_task(_watch_and_reload(app.state.hub, cfg))
        try:
            config = uvicorn.Config(
                app, host=host, port=port, log_level="info", reload=False
            )
            server = uvicorn.Server(config)
            if open_browser:
                # Delay a touch to let server bind
                loop.call_later(0.8, lambda: webbrowser.open(f"http://{host}:{port}/"))
            await server.serve()
        finally:
            watcher.cancel()

    try:
        asyncio.run(supervisor())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
