"""Main entry point for starting Drafter servers.

Provides the start_server() function which routes to either in-browser ClientServer
or local development AppServer based on execution context.
"""

from typing import Optional

from drafter.client_server.commands import get_main_server
from drafter.config.engines import EngineType
from drafter.configuration import get_system_configuration
from drafter.helpers.utils import is_web

MaybeBoolStr = Optional[bool | str]
"""Type alias for parameters that accept a bool, a string, or None."""


def start_server(
    initial_state=None,
    server=None,
    # ClientServer-specific parameters
    server_name: str | None = None,
    in_debug_mode: bool | None = None,
    framed: bool | None = None,
    theme: str | None = None,
    site_title: str | None = None,
    information: dict | None = None,
    # AppServer-specific parameters
    verbose: bool | None = None,
    asset_directory: MaybeBoolStr = None,
    show_filename_as: MaybeBoolStr = None,
    engine: EngineType | None = None,
    port: int | None = None,
    host: str | None = None,
    prerender_initial_page: bool | None = None,
    open_browser: bool | None = None,
    inline_py: bool | None = None,
    use_reloader: bool | None = None,
    # Aliases for compatibility with older versions
    reloader: bool | None = None,
    # Unused parameters that we want to keep for compatibility but not actually use
    cdn_skulpt: str | None = None,
    cdn_skulpt_std: str | None = None,
    cdn_skulpt_drafter: str | None = None,
    # Custom overrides
    argv: list[str] | None = None,
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
        asset_directory: Assets directory (uses Drafter defaults if False).
        show_filename_as: Display filename in UI (if different from actual).
        engine: Python engine ("skulpt" or "pyodide").
        port: Server port for dev mode.
        host: Server host for dev mode.
        prerender_initial_page: Prerender initial page on startup.
        open_browser: Auto-open browser in dev mode.
        inline_py: Inline code in HTML vs. load via HTTP.
        use_reloader: Enable file watcher and auto-reload.
        reloader: Deprecated alias for `use_reloader`, kept for
            compatibility with older versions; used only when
            `use_reloader` is not given.
        cdn_skulpt: Deprecated and ignored; passing a value prints a
            warning.
        cdn_skulpt_std: Deprecated and ignored; passing a value prints a
            warning.
        cdn_skulpt_drafter: Deprecated and ignored; passing a value
            prints a warning.
        argv: Command-line argument override passed into the system
            configuration.
        **extra_configuration: Additional configuration parameters.
    """
    # Handle compatibility for old parameters
    parameters = {}
    if server_name is not None:
        parameters["server_name"] = server_name
    if in_debug_mode is not None:
        parameters["in_debug_mode"] = in_debug_mode
    if framed is not None:
        parameters["framed"] = framed
    if theme is not None:
        parameters["theme"] = theme
    if site_title is not None:
        parameters["site_title"] = site_title
    if information is not None:
        parameters["information"] = information
    if verbose is not None:
        parameters["verbose"] = verbose
    if asset_directory is not None:
        parameters["asset_directory"] = asset_directory
    if show_filename_as is not None:
        parameters["show_filename_as"] = show_filename_as
    if engine is not None:
        parameters["engine"] = engine
    if port is not None:
        parameters["port"] = port
    if host is not None:
        parameters["host"] = host
    if prerender_initial_page is not None:
        parameters["prerender_initial_page"] = prerender_initial_page
    if open_browser is not None:
        parameters["open_browser"] = open_browser
    if inline_py is not None:
        parameters["inline_py"] = inline_py
    if reloader is not None and use_reloader is None:
        parameters["use_reloader"] = reloader
    elif use_reloader is not None:
        parameters["use_reloader"] = use_reloader
    # Handle deprecated parameters that are no longer used but we want to keep for compatibility
    if cdn_skulpt is not None:
        print("Warning: 'cdn_skulpt' parameter is no longer used and will be ignored.")
    if cdn_skulpt_std is not None:
        print(
            "Warning: 'cdn_skulpt_std' parameter is no longer used and will be ignored."
        )
    if cdn_skulpt_drafter is not None:
        print(
            "Warning: 'cdn_skulpt_drafter' parameter is no longer used and will be ignored."
        )
    # Custom overrides
    if argv is not None:
        parameters["argv"] = argv
    parameters.update(extra_configuration)

    system = get_system_configuration()
    system.merge_in_args(parameters)
    server = server or get_main_server()

    # Primary dispatch based on execution context
    if is_web():
        from drafter.bridge import run_client_bridge

        run_client_bridge(system, server, initial_state)
    elif system.bootstrap.mode == "compile_site":
        from drafter.builder.build import compile_site

        compile_site(system, server, initial_state)
    else:
        from drafter.app.app_server import serve_app_once

        serve_app_once(system, server, initial_state)
