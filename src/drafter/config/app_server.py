from dataclasses import dataclass, fields
from typing import Optional, Union
from drafter.config.engines import EngineType
from drafter.config.urls import INTERNAL_ROUTES


@dataclass
class AppServerConfiguration:
    """
    Configuration options for the Drafter App Server.

    Attributes:
        verbose: Whether to enable verbose logging on stdout.
        prerender_initial_page: Whether to prerender the initial page on server start.
        port: The port on which to run the server.
        host: The host on which to run the server.
        use_reloader: Whether to use the auto-reloader for development; any edits to the user code will
                      restart the server and reload the page.
        open_browser: Whether to automatically open the web browser when the server starts.
        inline_py: Whether to inline the user Python code into the HTML page (for small scripts).
                   If False, the user code is loaded via a separate HTTP request.
        engine: The Python execution engine to use (e.g., "skulpt", "pyodide").
        user_directory: The directory path to the main user folder to serve. If not specified,
                        then it will detect the first file that called `start_server` in the current
                        call stack, and use that file's directory (and also assign `main_filename`).
        main_filename: The filename to use for the main user Python file. Will be auto-detected
                       if not specified based on the `start_server`.
        asset_directory: The directory path to serve static assets from. If not specified, it will
                         use the default Drafter assets.
        show_filename_as: The displayed filename of the main user file in the UI (if different from `main_filename`).
        site_title: The title of the site to display in the browser tab.
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

    override_asset_url: Union[bool, str] = False

    site_title: str = "Drafter App Server"

    # TODO: Additional configuration settings from `scaffolding/index.skulpt.template.html` go here

    @property
    def ws_url(self) -> str:
        return f"ws://{self.host}:{self.port}{INTERNAL_ROUTES['WS']}"

    def merge_in_args(self, new_args: dict) -> None:
        for key, value in new_args.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise AttributeError(f"Unknown configuration attribute: {key}")

    def extract_from_args(self, potential_args: dict):
        for field in fields(self):
            if field.name in potential_args:
                value = potential_args[field.name]
                if value is not None:
                    setattr(self, field.name, value)
