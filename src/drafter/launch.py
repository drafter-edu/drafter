"""Main entry point for starting Drafter servers.

Provides the start_server() function which routes to either in-browser ClientServer
or local development AppServer based on execution context.
"""

import sys
import os
from typing import Optional, Union
from drafter.helpers.utils import is_web, seek_filename_by_line
from drafter.config.engines import EngineType
from drafter.config.app_server import AppServerConfiguration
from drafter.client_server.commands import get_main_server


MaybeBoolStr = Optional[Union[bool, str]]


def start_server(
    initial_state=None,
    server=None,
    # ClientServer-specific parameters
    server_name: Optional[str] = None,
    in_debug_mode: Optional[bool] = None,
    framed: Optional[bool] = None,
    theme: Optional[str] = None,
    site_title: Optional[str] = None,
    information: Optional[dict] = None,
    # AppServer-specific parameters
    verbose: Optional[bool] = None,
    user_directory: MaybeBoolStr = None,
    main_filename: MaybeBoolStr = None,
    asset_directory: MaybeBoolStr = None,
    show_filename_as: MaybeBoolStr = None,
    engine: Optional[EngineType] = None,
    port: Optional[int] = None,
    host: Optional[str] = None,
    prerender_initial_page: Optional[bool] = None,
    open_browser: Optional[bool] = None,
    inline_py: Optional[bool] = None,
    use_reloader: Optional[bool] = None,
    **extra_configuration,
) -> None:
    """Start the Drafter server (web or local development mode).

    Routes to either ClientServer (web mode) or AppServer (local dev mode)
    based on execution context. In web mode, initializes browser-side bridge;
    in local mode, starts Starlette dev server with file watching.

    This function is the primary entry point for users and accepts parameters
    for both ClientServer and AppServer modes (the appropriate ones are used
    depending on context).

    Args:
        initial_state: Optional initial application state.
        server: Optional pre-created server instance (defaults to main server).
        server_name: Server identifier name.
        in_debug_mode: Enable debug panel and logging.
        framed: Whether to frame the content.
        theme: Theme name (e.g., "default").
        site_title: Title displayed in UI.
        information: Dict of site information (author, description, etc.).
        verbose: Enable verbose logging.
        user_directory: User code directory (auto-detected if False).
        main_filename: Main Python file name (auto-detected if False).
        asset_directory: Assets directory (uses Drafter defaults if False).
        show_filename_as: Display filename in UI (if different from actual).
        engine: Python engine ("skulpt" or "pyodide").
        port: Server port for dev mode.
        host: Server host for dev mode.
        prerender_initial_page: Prerender initial page on startup.
        open_browser: Auto-open browser in dev mode.
        inline_py: Inline code in HTML vs. load via HTTP.
        use_reloader: Enable file watcher and auto-reload.
        **extra_configuration: Additional configuration parameters.

    Raises:
        Various exceptions from ClientServer or AppServer initialization.
    """
    server = server or get_main_server()
    if is_web():
        # TODO: This logic should really be encoded in a function somewhere
        from drafter.bridge import ClientBridge

        server.do_configuration(extra_configuration)
        configuration = server.get_current_configuration()

        client_bridge = ClientBridge(configuration)
        client_bridge.setup_site(server.do_render())

        server.do_listen_for_events(client_bridge.handle_telemetry_event)

        server.do_start(initial_state=initial_state)
        initial_request = client_bridge.make_initial_request()

        def handle_visit(request):
            response = server.do_visit(request)
            client_bridge.handle_response(response, handle_visit)
            return response

        def handle_toggle_frame():
            server.reconfigure_flip("framed")

        def handle_debug_mode():
            server.reconfigure_flip("in_debug_mode")

        client_bridge.setup_events(handle_visit, handle_toggle_frame, handle_debug_mode)
        handle_visit(initial_request)

    else:
        from drafter.config.cli import parse_command_line_args
        from drafter.app.app_server import serve_app_once

        command_line_args = parse_command_line_args(sys.argv)
        # TODO: Any command_line args must be converted into something the engine can understand

        config = AppServerConfiguration()
        # TODO: Handle environment variables
        # TODO: Handle extra command line arguments
        config.merge_in_args(vars(command_line_args))
        config.extract_from_args(locals())

        print("Final server configuration:", config)

        # TODO: Move this logic into AppServerConfiguration?
        if config.user_directory is False:
            found_path = seek_filename_by_line("start_server", config.main_filename)
            config.user_directory = (
                os.path.dirname(found_path) if found_path else os.getcwd()
            )
            config.main_filename = (
                os.path.basename(found_path)
                if found_path
                else (config.main_filename or "main.py")
            )

        elif not os.path.isdir(config.user_directory):
            if os.path.isfile(config.user_directory):
                config.main_filename = os.path.basename(config.user_directory)
                config.user_directory = os.path.dirname(config.user_directory)

        else:
            # TODO: Logic seems redundant, maybe only do it in app_server?
            config.main_filename = (
                config.main_filename if config.main_filename is not False else "main.py"
            )

        if config.show_filename_as is False:
            config.show_filename_as = config.main_filename

        if config.verbose:
            print("Starting local Drafter server...")

        if config.prerender_initial_page:
            server.do_configuration(extra_configuration)

        serve_app_once(server, config, initial_state)
