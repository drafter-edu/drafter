"""Configuration for the Drafter development app server.

Defines AppServerConfiguration dataclass for controlling server behavior,
asset serving, file reloading, and UI options.
"""

from dataclasses import dataclass, fields
from typing import Optional, Union
from drafter.config.app_backend import AppBackendConfig
from drafter.config.engines import EngineType
from drafter.config.urls import INTERNAL_ROUTES


@dataclass
class AppServerConfiguration(AppBackendConfig):
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

    verbose: bool = True
    prerender_initial_page: bool = True
    port: int = 8000
    host: str = "localhost"
    use_reloader: bool = True
    open_browser: bool = True
    inline_py: bool = True
    serve_adjacent_files: bool = True
    
    # TODO: Additional configuration settings from `scaffolding/index.skulpt.template.html` go here

    @property
    def ws_url(self) -> str:
        """Get WebSocket URL for live reload.

        Returns:
            WebSocket URL constructed from host, port, and internal route.
        """
        return f"ws://{self.host}:{self.port}/{INTERNAL_ROUTES['WS']}"

    
