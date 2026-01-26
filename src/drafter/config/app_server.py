"""Configuration for the Drafter development app server.

Defines AppServerConfiguration dataclass for controlling server behavior,
asset serving, file reloading, and UI options.
"""

from dataclasses import dataclass, fields
from typing import Optional, Union
from drafter.config.engines import EngineType
from drafter.config.urls import INTERNAL_ROUTES


@dataclass
class AppServerConfiguration:
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
        mount_drafter_locally: Mount Drafter locally vs. from package.
        override_asset_url: Custom asset URL (False to use defaults).
    """

    verbose: bool = True
    prerender_initial_page: bool = True
    port: int = 8000
    host: str = "localhost"
    use_reloader: bool = True
    open_browser: bool = True
    inline_py: bool = True
    engine: EngineType = "skulpt"

    user_directory: Union[bool, str] = False
    main_filename: Union[bool, str] = False
    asset_directory: Union[bool, str] = False
    show_filename_as: Union[bool, str] = False
    serve_adjacent_files: bool = True
    mount_drafter_locally: bool = False

    override_asset_url: Union[bool, str] = False

    site_title: str = "Drafter App Server"

    # TODO: Additional configuration settings from `scaffolding/index.skulpt.template.html` go here

    @property
    def ws_url(self) -> str:
        """Get WebSocket URL for live reload.

        Returns:
            WebSocket URL constructed from host, port, and internal route.
        """
        return f"ws://{self.host}:{self.port}{INTERNAL_ROUTES['WS']}"

    def merge_in_args(self, new_args: dict) -> None:
        """Merge new arguments into configuration.

        Args:
            new_args: Dict of argument names and values.

        Raises:
            AttributeError: If unknown configuration attribute provided.
        """
        for key, value in new_args.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise AttributeError(f"Unknown configuration attribute: {key}")

    def extract_from_args(self, potential_args: dict):
        """Extract configuration values from argument dict.

        Args:
            potential_args: Dict potentially containing configuration values.
        """
        for field in fields(self):
            if field.name in potential_args:
                value = potential_args[field.name]
                if value is not None:
                    setattr(self, field.name, value)
