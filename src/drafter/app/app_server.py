"""Starlette-based development server for Drafter applications.

Provides local development server functionality including live reloading,
file watching, and pre-rendering of initial pages.
"""

import asyncio
import webbrowser
from pathlib import Path

from drafter.data.request import Request
from pathlib import Path
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse, Response
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
        system=system,
        modified_system=get_system_config_modifications(),
        inline_py=system.app_server.inline_py,
        user_code=user_code if system.app_server.inline_py else None,
        python_url=str(app.state.user_path) if not system.app_server.inline_py else None,
        dev_ws_url=system.app_server.ws_url,
        assets_url="/"+determine_assets_url(system.app_common.override_asset_url),
        compiled_body=app.state.compiled_body,
        compiled_headers=app.state.compiled_headers,
        pyodide_drafter_path=app.state.pyodide_drafter_path,
    )
    return HTMLResponse(html)

async def list_user_files(req) -> Response:
    """Serve a JSON response listing user files in the user directory.
    
    If a path is given, it will be resolved as a subpath of the user directory, and only files within that subpath will be listed.
    
    Clearly indicates whether an entry is a file or a folder.
    
    Does not allow access to files outside the user directory, and only lists files (not directories).

    Args:
        req: Starlette request object.
    
    Returns:
        JSONResponse with list of user files.
    """
    app: Starlette = req.app  # type: ignore
    user_directory: Path = app.state.user_directory
    # Get optional path query parameter
    path_param = req.query_params.get("path", "")
    # Resolve the requested path against the user directory
    requested_path = (user_directory / path_param).resolve()
    # Ensure the requested path is within the user directory
    if not str(requested_path).startswith(str(user_directory)):
        return JSONResponse({"error": "Invalid path"}, status_code=400)
    # List files in the requested directory
    if not requested_path.is_dir():
        return JSONResponse({"error": "Path is not a directory"}, status_code=400)
    entries = []
    for entry in requested_path.iterdir():
        entries.append({
            "name": entry.name,
            "is_dir": entry.is_dir(),
        })
    return JSONResponse({"entries": entries, "summary": {
        "total_entries": len(entries),
        "requested_path": str(requested_path.relative_to(user_directory)),
    }})


def make_app(
    system: SystemConfiguration,
    server: ClientServer, 
    initial_state
) -> Starlette:
    # Determine paths
    user_directory = Path(system.bootstrap.get_user_directory()).resolve()
    
    user_path = user_directory / system.bootstrap.get_main_filename()

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
            Route("/"+INTERNAL_ROUTES["LIST_FILES"], list_user_files)
        )
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
    if system.bootstrap.path is None:
        print("Error: Cannot start server because the path to the main user file is not specified.")
        return
    
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
