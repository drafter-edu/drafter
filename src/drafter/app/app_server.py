"""Starlette-based development server for Drafter applications.

Provides local development server functionality including live reloading,
file watching, and pre-rendering of initial pages.
"""

import asyncio
import webbrowser
from pathlib import Path

from drafter.data.request import Request
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, Response
from starlette.routing import Route, WebSocketRoute, Mount
from starlette.staticfiles import StaticFiles
import uvicorn

from drafter import get_main_server
from drafter.config.system import SystemConfiguration
from drafter.configuration import get_system_config_modifications
from drafter.client_server.client_server import ClientServer
from drafter.config.urls import determine_assets_url
from drafter.scaffolding.templating import render_index_html
from drafter.scaffolding.utils import pkg_assets_dir
from drafter.config.urls import INTERNAL_ROUTES
from drafter.config.app_server import AppServerConfiguration
from drafter.app.watcher import ReloadHub, ws_endpoint, _watch_and_reload
from drafter.data.response import Response as DrafterResponse


async def index(req) -> Response:
    """Serve the index HTML page for the development server.

    Args:
        req: Starlette request object.

    Returns:
        HTMLResponse with rendered index page.
    """
    app: Starlette = req.app  # type: ignore
    system: SystemConfiguration = app.state.system
    user_code = app.state.user_path.read_text(encoding="utf-8")
    html = render_index_html(
        title=system.app_common.site_title,
        inline_py=system.app_server.inline_py,
        user_code=user_code if system.app_server.inline_py else None,
        python_url=str(app.state.user_path) if not system.app_server.inline_py else None,
        dev_ws_url=system.app_server.ws_url,
        assets_url="/"+determine_assets_url(system.app_common.override_asset_url),
        engine=system.app_common.engine,
        compiled_body=app.state.compiled_body,
        compiled_headers=app.state.compiled_headers,
        mount_drafter_locally=system.app_common.mount_drafter_locally,
        system=system.to_json(),
        modified_system=get_system_config_modifications(),
    )
    return HTMLResponse(html)


def make_app(
    system: SystemConfiguration,
    server: ClientServer, 
    initial_state
) -> Starlette:
    # Determine paths
    user_directory = (
        Path(system.app_common.user_directory).resolve()
        if isinstance(system.app_common.user_directory, str)
        else Path.cwd()
    )
    user_path = user_directory / (
        system.app_common.main_filename if isinstance(system.app_common.main_filename, str) else "main.py"
    )

    # Determine watches and routes
    watch_paths = [
        user_path,
    ]
    routes = [
        Route("/", index),
        WebSocketRoute("/"+INTERNAL_ROUTES["WS"], ws_endpoint),
    ]
    # Handle default assets
    if not system.app_common.override_asset_url:
        assets_dir = (
            Path(system.app_common.asset_directory)
            if isinstance(system.app_common.asset_directory, str)
            else pkg_assets_dir()
        )
        if assets_dir.exists():
            watch_paths.append(assets_dir)
        routes.append(
            Mount(
                "/"+INTERNAL_ROUTES["ASSETS"],
                app=StaticFiles(directory=str(assets_dir)),
                name="assets",
            )
        )
    # Serve user files if enabled
    if system.app_server.serve_adjacent_files:
        watch_paths.append(user_directory)
        routes.append(
            Mount(
                "/",
                app=StaticFiles(directory=str(user_directory)),
                name="user_files",
            ),
        )
    # Precompile if needed
    if system.app_common.prerender_initial_page:
        compiled_body, compiled_headers = server.precompile_server(initial_state)
    else:
        compiled_body, compiled_headers = "", ""
    # Create app and assign state
    app = Starlette(routes=routes)
    app.state.system = system
    app.state.user_directory = user_directory
    app.state.user_path = user_path
    app.state.hub = ReloadHub()
    app.state.watch_paths = watch_paths
    app.state.compiled_body = compiled_body
    app.state.compiled_headers = compiled_headers
    return app


def serve_app_once(
    system: SystemConfiguration,
    server: ClientServer,
    initial_state,
):
    # Configure the server if prerendering is needed
    if system.app_common.prerender_initial_page:
        possible_error = server.do_configuration()
        if possible_error:
            print("Error during prerendering configuration:", possible_error)
            return
    app = make_app(system, server, initial_state)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Background watcher task
    async def supervisor():
        watcher = asyncio.create_task(
            _watch_and_reload(app.state.hub, app.state.watch_paths, system)
        )
        try:
            uvicorn_config = uvicorn.Config(
                app, host=system.app_server.host, port=system.app_server.port, log_level="info", reload=False
            )
            server = uvicorn.Server(uvicorn_config)
            if system.app_server.open_browser:
                # Delay a touch to let server bind
                loop.call_later(
                    0.8, lambda: webbrowser.open(f"http://{system.app_server.host}:{system.app_server.port}/")
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
