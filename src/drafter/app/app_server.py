"""Starlette-based development server for Drafter applications.

Provides local development server functionality including live reloading,
file watching, and pre-rendering of initial pages.
"""

import asyncio
import json
import webbrowser
from pathlib import Path

import uvicorn
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse, Response
from starlette.routing import Mount, Route, WebSocketRoute
from starlette.staticfiles import StaticFiles

from drafter.app.error_log import append_error_log_entry, build_log_entry
from drafter.app.hacks import DRAFTER_LOG_CONFIG_FOR_UVICORN
from drafter.app.watcher import ReloadHub, WatchedPath, _watch_and_reload, ws_endpoint
from drafter.client_server.client_server import ClientServer
from drafter.config.system import SystemConfiguration
from drafter.config.urls import INTERNAL_ROUTES, determine_assets_url
from drafter.configuration import get_system_config_modifications
from drafter.scaffolding.templating import render_index_html
from drafter.scaffolding.utils import pkg_assets_dir
from drafter.version import CURRENT_DRAFTER_VERSION


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
        python_url=str(app.state.user_path)
        if not system.app_server.inline_py
        else None,
        dev_ws_url=system.app_server.ws_url,
        assets_url="/" + determine_assets_url(system.app_common.override_asset_url),
        compiled_body=app.state.compiled_body,
        compiled_headers=app.state.compiled_headers,
        pyodide_drafter_path=system.app_common.pyodide_drafter_path
        or f"drafter=={CURRENT_DRAFTER_VERSION}",
    )
    return HTMLResponse(html)


async def list_user_files(req) -> Response:
    """Serve a JSON response listing entries in the user directory.

    If a path is given, it will be resolved as a subpath of the user directory, and only entries within that subpath will be listed.

    Lists both files and directories, with each entry's `is_dir` flag indicating whether it is a folder.

    Does not allow access to paths outside the user directory.

    Args:
        req: Starlette request object.

    Returns:
        JSONResponse with the list of entries, or an error response for
        invalid or non-directory paths.
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
        entries.append(
            {
                "name": entry.name,
                "is_dir": entry.is_dir(),
            }
        )
    return JSONResponse(
        {
            "entries": entries,
            "summary": {
                "total_entries": len(entries),
                "requested_path": str(requested_path.relative_to(user_directory)),
            },
        }
    )


MAX_ERROR_REPORT_BYTES = 256 * 1024
"""Reject browser error reports larger than this many bytes."""


async def record_error_log(req) -> Response:
    """Receive a browser error report and append it to the shared debug log.

    The browser posts errors here while the site is not in production mode
    (see js/src/debug/error_reporter.ts). Each report is combined with
    server-side environment details and appended to the debug log next to
    the student's code (see drafter.app.error_log). Log-write failures are
    reported in the response body but never crash the server.

    Args:
        req: Starlette request whose JSON body is the error report.

    Returns:
        JSONResponse with {"ok": bool}, or an error response for oversized
        or malformed reports.
    """
    app: Starlette = req.app  # type: ignore
    body = await req.body()
    if len(body) > MAX_ERROR_REPORT_BYTES:
        return JSONResponse({"error": "Report too large"}, status_code=413)
    try:
        payload = json.loads(body)
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)
    if not isinstance(payload, dict):
        return JSONResponse({"error": "Invalid report"}, status_code=400)
    system: SystemConfiguration = app.state.system
    entry = build_log_entry(payload, str(system.bootstrap.get_main_filename()))
    written = append_error_log_entry(app.state.user_directory, entry)
    return JSONResponse({"ok": written})


def make_app(
    system: SystemConfiguration, server: ClientServer, initial_state
) -> Starlette:
    """Build the Starlette application for the development server.

    Assembles routes for the index page, the live-reload websocket, static
    assets, and (optionally) user file serving/listing; sets up file watch
    paths; and optionally prerenders the initial page via the client server.
    The configuration, paths, reload hub, and prerendered content are stored
    on the application's state.

    Args:
        system: System configuration controlling paths, asset serving, and
            prerendering behavior.
        server: Client server used to precompile the initial page when
            prerendering is enabled.
        initial_state: Initial application state passed to the client server
            for prerendering.

    Returns:
        Configured Starlette application ready to be served by uvicorn.
    """
    # Determine paths
    user_directory = Path(system.bootstrap.get_user_directory()).resolve()

    user_path = user_directory / system.bootstrap.get_main_filename()

    # Determine watches and routes
    watch_paths = [
        WatchedPath(user_path, False),
    ]
    routes = [
        Route("/", index),
        WebSocketRoute("/" + INTERNAL_ROUTES["WS"], ws_endpoint),
        Route("/" + INTERNAL_ROUTES["ERROR_LOG"], record_error_log, methods=["POST"]),
    ]
    # Handle default assets
    if not system.app_common.override_asset_url:
        assets_dir = (
            Path(system.app_common.asset_directory)
            if isinstance(system.app_common.asset_directory, str)
            else pkg_assets_dir()
        )
        if assets_dir.exists():
            watch_paths.append(WatchedPath(assets_dir, True))
        routes.append(
            Mount(
                "/" + INTERNAL_ROUTES["ASSETS"],
                app=StaticFiles(directory=str(assets_dir)),
                name="assets",
            )
        )
    # Serve user files if enabled
    if system.app_server.serve_adjacent_files:
        watch_paths.append(WatchedPath(user_directory, False))
        routes.append(Route("/" + INTERNAL_ROUTES["LIST_FILES"], list_user_files))
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
    """Run the development server until it exits.

    Validates that a main user file is configured, performs prerendering
    configuration if enabled, builds the Starlette app via make_app, and
    serves it with uvicorn alongside a background file watcher that triggers
    live reloads. Optionally opens a web browser once the server has had a
    moment to bind. Blocks until the server stops; a KeyboardInterrupt is
    swallowed for a clean shutdown.

    Args:
        system: System configuration controlling server host/port, browser
            opening, prerendering, and file paths.
        server: Client server used for prerendering configuration and
            initial page compilation.
        initial_state: Initial application state passed along for
            prerendering.

    Returns:
        None. Prints an error message and returns early if the main user
        file path is missing or prerendering configuration fails.
    """
    if system.bootstrap.path is None:
        print(
            "Error: Cannot start server because the path to the main user file is not specified."
        )
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
            _watch_and_reload(
                app.state.hub,
                app.state.watch_paths,
                system,
                app.state.user_path,
            )
        )
        try:
            uvicorn_config = uvicorn.Config(
                app,
                host=system.app_server.host,
                port=system.app_server.port,
                log_level="info",
                log_config=DRAFTER_LOG_CONFIG_FOR_UVICORN,
                reload=False,
            )
            server = uvicorn.Server(uvicorn_config)
            if system.app_server.open_browser:
                # Delay a touch to let server bind
                loop.call_later(
                    0.8,
                    lambda: webbrowser.open(
                        f"http://{system.app_server.host}:{system.app_server.port}/"
                    ),
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
