"""Configuration for the Drafter development app server.

Defines AppServerConfiguration dataclass for controlling server behavior,
asset serving, file reloading, and UI options.
"""

from dataclasses import dataclass, fields
from typing import Optional, Union
from drafter.helpers.env_vars import EnvVars
from drafter.config.engines import EngineType
from drafter.config.urls import INTERNAL_ROUTES
from drafter.config.base import BaseConfiguration


@dataclass
class AppServerConfiguration(BaseConfiguration):
    """Configuration options for the Drafter development server.

    Controls how the local development server runs, including port/host,
    file watching, code inlining, asset serving, and browser integration.

    Attributes:
        verbose: Enable verbose logging to stdout.
        prerender_initial_page: Prerender initial page on server start.
        port: Server port number.
        host: Server host address.
        use_reloader: Enable auto-reloader for code changes.
        open_browser: Automatically open web browser on start.
        inline_py: Inline user code in HTML vs. load via HTTP request.
        engine: Python execution engine ("skulpt" or "pyodide").
        user_directory: Main user folder path (auto-detected if False).
        main_filename: Main user Python file name (auto-detected if False).
        asset_directory: Static assets directory (uses Drafter defaults if False).
        show_filename_as: Display name for main file in UI (if different).
        site_title: Browser tab title.
        serve_adjacent_files: Serve files from user directory.
        mount_drafter_locally: Mount Drafter locally vs. from package. Used for local dev.
        override_asset_url: Custom asset URL (False to use defaults).
    """
    port: int = 8000
    host: str = "localhost"
    use_reloader: bool = True
    open_browser: bool = True
    inline_py: bool = True
    serve_adjacent_files: bool = True
    
    # TODO: Additional configuration settings from `scaffolding/index.skulpt.template.html` go here
    @staticmethod
    def parse_env_variables(env_vars: dict) -> dict:
        result = EnvVars(env_vars)
        result.get_int_if_exists("DRAFTER_PORT", "port", raise_error=True)
        result.get_string_if_exists("DRAFTER_HOST", "host")
        result.get_bool_if_exists("DRAFTER_USE_RELOADER", "use_reloader")
        result.get_bool_if_exists("DRAFTER_OPEN_BROWSER", "open_browser")
        result.get_bool_if_exists("DRAFTER_INLINE_PY", "inline_py")
        result.get_bool_if_exists("DRAFTER_SERVE_ADJACENT_FILES", "serve_adjacent_files")
        return result.as_dict()
    
    @staticmethod
    def extend_parser(parser):
        group = parser.add_argument_group("App Server Configuration")
        group.add_argument(
            "--port",
            type=int,
            default=8000,
            help="Port number for the server"
        )
        group.add_argument(
            "--host",
            type=str,
            default="localhost",
            help="Host address for the server"
        )
        group.add_argument(
            "--no-reloader",
            action="store_false",
            dest="use_reloader",
            help="Disable auto-reloader for code changes"
        )
        group.add_argument(
            "--no-open-browser",
            action="store_false",
            dest="open_browser",
            help="Do not automatically open web browser on start"
        )
        group.add_argument(
            "--no-inline-py",
            action="store_false",
            dest="inline_py",
            help="Do not inline user code in HTML; load via HTTP request instead"
        )
        group.add_argument(
            "--no-serve-adjacent-files",
            action="store_false",
            dest="serve_adjacent_files",
            help="Do not serve files from user directory"
        )
        return group
    
    @staticmethod
    def parse_args(parsed_args: dict) -> dict:
        result = {}
        if parsed_args.get("prerender_initial_page") is not None:
            result["prerender_initial_page"] = parsed_args["prerender_initial_page"]
        if parsed_args.get("port") is not None:
            result["port"] = parsed_args["port"]
        if parsed_args.get("host") is not None:
            result["host"] = parsed_args["host"]
        if parsed_args.get("use_reloader") is not None:
            result["use_reloader"] = parsed_args["use_reloader"]
        if parsed_args.get("open_browser") is not None:
            result["open_browser"] = parsed_args["open_browser"]
        if parsed_args.get("inline_py") is not None:
            result["inline_py"] = parsed_args["inline_py"]
        if parsed_args.get("serve_adjacent_files") is not None:
            result["serve_adjacent_files"] = parsed_args["serve_adjacent_files"]
        return result

    @property
    def ws_url(self) -> str:
        """Get WebSocket URL for live reload.

        Returns:
            WebSocket URL constructed from host, port, and internal route.
        """
        return f"ws://{self.host}:{self.port}/{INTERNAL_ROUTES['WS']}"

    
