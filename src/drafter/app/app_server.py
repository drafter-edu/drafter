import asyncio
import webbrowser
from pathlib import Path

from drafter.config.urls import determine_assets_url
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, Response
from starlette.routing import Route, WebSocketRoute, Mount
from starlette.staticfiles import StaticFiles
import uvicorn

from drafter.app.templating import render_index_html
from drafter.app.utils import pkg_assets_dir
from drafter.config.app_server import AppServerConfiguration, INTERNAL_ROUTES
from drafter.app.watcher import ReloadHub, ws_endpoint, _watch_and_reload


async def index(req) -> Response:
    app: Starlette = req.app  # type: ignore
    config: AppServerConfiguration = app.state.config
    user_code = app.state.user_path.read_text(encoding="utf-8")
    html = render_index_html(
        title=config.site_title,
        inline_py=config.inline_py,
        user_code=user_code if config.inline_py else None,
        python_url=str(app.state.user_path) if not config.inline_py else None,
        dev_ws_url=config.ws_url,
        assets_url=determine_assets_url(config.override_asset_url),
        engine=config.engine,
    )
    return HTMLResponse(html)


def make_app(config: AppServerConfiguration) -> Starlette:
    # Determine paths
    user_directory = (
        Path(config.user_directory).resolve()
        if isinstance(config.user_directory, str)
        else Path.cwd()
    )
    user_path = user_directory / (
        config.main_filename if isinstance(config.main_filename, str) else "main.py"
    )

    # Determine watches and routes
    watch_paths = [
        user_path,
    ]
    routes = [
        Route("/", index),
        WebSocketRoute(INTERNAL_ROUTES["WS"], ws_endpoint),
    ]
    # Handle default assets
    if not config.override_asset_url:
        assets_dir = (
            Path(config.asset_directory)
            if isinstance(config.asset_directory, str)
            else pkg_assets_dir()
        )
        if assets_dir.exists():
            watch_paths.append(assets_dir)
        routes.append(
            Mount(
                INTERNAL_ROUTES["ASSETS"],
                app=StaticFiles(directory=str(assets_dir)),
                name="assets",
            )
        )
    # Serve user files if enabled
    if config.serve_adjacent_files:
        watch_paths.append(user_directory)
        routes.append(
            Mount(
                "/",
                app=StaticFiles(directory=str(user_directory)),
                name="user_files",
            ),
        )
    # Create app and assign state
    app = Starlette(routes=routes)
    app.state.config = config
    app.state.user_directory = user_directory
    app.state.user_path = user_path
    app.state.hub = ReloadHub()
    app.state.watch_paths = watch_paths
    return app


def serve_app_once(
    config: AppServerConfiguration,
):
    app = make_app(config)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Background watcher task
    async def supervisor():
        watcher = asyncio.create_task(
            _watch_and_reload(app.state.hub, app.state.watch_paths, config)
        )
        try:
            uvicorn_config = uvicorn.Config(
                app, host=config.host, port=config.port, log_level="info", reload=False
            )
            server = uvicorn.Server(uvicorn_config)
            if config.open_browser:
                # Delay a touch to let server bind
                loop.call_later(
                    0.8, lambda: webbrowser.open(f"http://{config.host}:{config.port}/")
                )
            await server.serve()
        finally:
            watcher.cancel()

    try:
        asyncio.run(supervisor())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
