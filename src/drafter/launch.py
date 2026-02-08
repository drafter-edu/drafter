"""Main entry point for starting Drafter servers.

Provides the start_server() function which routes to either in-browser ClientServer
or local development AppServer based on execution context.
"""

import sys
import os
from typing import Optional, Union
from drafter.config.client_server import ClientServerConfiguration
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
    # Aliases for compatibility with older versions
    reloader: Optional[bool] = None,
    # Unused parameters that we want to keep for compatibility but not actually use
    cdn_skulpt: Optional[str] = None,
    cdn_skulpt_std: Optional[str] = None,
    cdn_skulpt_drafter: Optional[str] = None,
    # Custom overrides
    argv: Optional[list[str]] = None,
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
    # Handle compatibility for old parameters
    if reloader is not None and use_reloader is None:
        use_reloader = reloader
    # Handle deprecated parameters that are no longer used but we want to keep for compatibility
    if cdn_skulpt is not None:
        print("Warning: 'cdn_skulpt' parameter is no longer used and will be ignored.")
        del cdn_skulpt
    if cdn_skulpt_std is not None:
        print("Warning: 'cdn_skulpt_std' parameter is no longer used and will be ignored.")
        del cdn_skulpt_std
    if cdn_skulpt_drafter is not None:
        print("Warning: 'cdn_skulpt_drafter' parameter is no longer used and will be ignored.")
        del cdn_skulpt_drafter
    
    server = server or get_main_server()
    if is_web():
        # TODO: This logic should really be encoded in a function somewhere
        from drafter.bridge import ClientBridge

        # Configuration Phase
        possible_error_data = server.do_configuration(extra_configuration)
        # Rendering Phase
        if possible_error_data:
            # TODO: Need to handle the case where configuration failed and is None
            rendered_site = possible_error_data
            configuration = ClientServerConfiguration()
        else:
            configuration = server.get_current_configuration()
            rendered_site = server.do_render()
        client_bridge = ClientBridge(configuration)
        client_bridge.setup_site(rendered_site)
        
        if rendered_site.error:
            return

        server.do_listen_for_events(client_bridge.handle_telemetry_event)
        
        def handle_visit(request):
            # Visiting Phase
            response = server.do_visit(request)
            # Committing Phase
            client_bridge.handle_response(response, handle_visit)
            # Idle Phase
            server.do_finish_visit()
            return response

        def handle_toggle_frame():
            server.reconfigure_flip("framed")

        def handle_debug_mode():
            server.reconfigure_flip("in_debug_mode")

        client_bridge.setup_events(handle_visit, handle_toggle_frame, handle_debug_mode)
        # Starting Phase
        server.do_start(initial_state=initial_state)
        # Started Phase
        initial_request = client_bridge.make_initial_request()
        handle_visit(initial_request)

    else:
        from drafter.app.configurer import process_app_server_configuration
        from drafter.app.app_server import serve_app_once

        config = AppServerConfiguration()
        config = process_app_server_configuration(config,
                                                  sys.argv if argv is None else argv,
                                                  locals())        
        print("Final server configuration:", config)

        if config.prerender_initial_page:
            possible_error = server.do_configuration(extra_configuration)
            if possible_error:
                print("Error during prerendering configuration:", possible_error)
                return
        
        if config.verbose:
            print("Starting local Drafter server...")

        serve_app_once(server, config, initial_state)
