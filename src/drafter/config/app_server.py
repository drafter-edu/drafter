"""Configuration for the Drafter development app server.

Defines AppServerConfiguration dataclass for controlling server behavior,
asset serving, file reloading, and UI options.
"""

from dataclasses import dataclass, field
from pathlib import Path

from drafter.config.base import BaseConfiguration
from drafter.config.urls import INTERNAL_ROUTES
from drafter.helpers.env_vars import EnvVars


@dataclass
class AppServerConfiguration(BaseConfiguration):
    """Configuration options for the Drafter development server.

    Controls how the local development server runs, including port/host,
    file watching, code inlining, asset serving, and browser integration.

    Attributes:
        port: Server port number.
        host: Server host address.
        use_reloader: Enable auto-reloader for code changes. When False, the
            file watcher never starts at all.
        open_browser: Automatically open web browser on start.
        inline_py: Inline user code in HTML vs. load via HTTP request.
        serve_adjacent_files: Serve files from user directory.
        watch_adjacent_files: Automatically watch files next to the main
            file. When False, only the main file and explicitly configured
            paths are watched (a deterministic main-file-only mode).
        watch_recursively: Watch the main file's directory recursively
            (after safety checks). When False, safe mode is used instead.
        watch_safe_mode: Run safety checks before recursively watching the
            main file's directory, falling back to safe mode (main file +
            explicit paths + served files) when a check fails. When False,
            the checks are skipped and recursion always proceeds.
        watch_served_files: In safe mode, dynamically add files that the
            server actually serves to the watch set.
        watch_max_files: Safety limit: maximum files allowed in the main
            directory before safe mode is used. None disables the limit.
        watch_max_directories: Safety limit: maximum subdirectories allowed
            before safe mode is used. None disables the limit.
        watch_max_depth: Safety limit: maximum directory nesting depth
            allowed before safe mode is used. None disables the limit.
        watch_broad_locations: Permit recursively watching known broad
            locations (Desktop, Documents, Downloads, ...). The home
            directory and filesystem roots are always refused unless
            watch_force_recursive is set or watch_safe_mode is disabled.
        watch_paths: Extra files, directories, or glob patterns (relative to
            the main file's directory) to always watch.
        ignore_watch_paths: Files, directories (trailing slash), or glob
            patterns whose changes never trigger a reload.
        watch_manifest: Path to a JSON manifest describing the project's
            files: either a list of watch entries, or an object with
            "watch_paths" and "ignore_watch_paths" lists.
        watch_force_recursive: Escape hatch: recursively watch the main
            file's directory even when a safety check would refuse it.
    """

    port: int = 8000
    host: str = "localhost"
    use_reloader: bool = True
    open_browser: bool = True
    inline_py: bool = True
    serve_adjacent_files: bool = True
    # Automatic watching
    watch_adjacent_files: bool = True
    watch_recursively: bool = True
    watch_safe_mode: bool = True
    watch_served_files: bool = True
    # Safety limits
    watch_max_files: int | None = 1000
    watch_max_directories: int | None = 200
    watch_max_depth: int | None = 20
    watch_broad_locations: bool = False
    # Explicit overrides
    watch_paths: list[str | Path] = field(default_factory=list)
    ignore_watch_paths: list[str | Path] = field(default_factory=list)
    watch_manifest: str | Path | None = None
    # Advanced escape hatch
    watch_force_recursive: bool = False

    @staticmethod
    def get_key() -> str:
        """Return the key identifying this configuration section.

        Returns:
            The string "app_server".
        """
        return "app_server"

    # TODO: Additional configuration settings from the scaffolding index
    #       templates (e.g., `scaffolding/index.pyodide.template.html`) go here
    @staticmethod
    def parse_env_variables(env_vars: dict) -> dict:
        """Extract development server settings from environment variables.

        Reads DRAFTER_PORT, DRAFTER_HOST, DRAFTER_USE_RELOADER,
        DRAFTER_OPEN_BROWSER, DRAFTER_INLINE_PY,
        DRAFTER_SERVE_ADJACENT_FILES, and the DRAFTER_WATCH_* family
        (DRAFTER_WATCH_ADJACENT_FILES, DRAFTER_WATCH_RECURSIVELY,
        DRAFTER_WATCH_SAFE_MODE, DRAFTER_WATCH_SERVED_FILES,
        DRAFTER_WATCH_MAX_FILES, DRAFTER_WATCH_MAX_DIRECTORIES,
        DRAFTER_WATCH_MAX_DEPTH, DRAFTER_WATCH_BROAD_LOCATIONS,
        DRAFTER_WATCH_PATHS and DRAFTER_IGNORE_WATCH_PATHS as
        semicolon-separated lists, DRAFTER_WATCH_MANIFEST, and
        DRAFTER_WATCH_FORCE_RECURSIVE).

        Args:
            env_vars: A dictionary of environment variables.

        Returns:
            A dictionary of server configuration values that were present.

        Raises:
            ValueError: If DRAFTER_PORT is set but cannot be parsed as an
                integer.
        """
        result = EnvVars(env_vars)
        result.get_int_if_exists("DRAFTER_PORT", "port", raise_error=True)
        result.get_string_if_exists("DRAFTER_HOST", "host")
        result.get_bool_if_exists("DRAFTER_USE_RELOADER", "use_reloader")
        result.get_bool_if_exists("DRAFTER_OPEN_BROWSER", "open_browser")
        result.get_bool_if_exists("DRAFTER_INLINE_PY", "inline_py")
        result.get_bool_if_exists(
            "DRAFTER_SERVE_ADJACENT_FILES", "serve_adjacent_files"
        )
        result.get_bool_if_exists(
            "DRAFTER_WATCH_ADJACENT_FILES", "watch_adjacent_files"
        )
        result.get_bool_if_exists("DRAFTER_WATCH_RECURSIVELY", "watch_recursively")
        result.get_bool_if_exists("DRAFTER_WATCH_SAFE_MODE", "watch_safe_mode")
        result.get_bool_if_exists("DRAFTER_WATCH_SERVED_FILES", "watch_served_files")
        result.get_int_if_exists("DRAFTER_WATCH_MAX_FILES", "watch_max_files")
        result.get_int_if_exists(
            "DRAFTER_WATCH_MAX_DIRECTORIES", "watch_max_directories"
        )
        result.get_int_if_exists("DRAFTER_WATCH_MAX_DEPTH", "watch_max_depth")
        result.get_bool_if_exists(
            "DRAFTER_WATCH_BROAD_LOCATIONS", "watch_broad_locations"
        )
        result.get_string_list_if_exists("DRAFTER_WATCH_PATHS", "watch_paths", ";")
        result.get_string_list_if_exists(
            "DRAFTER_IGNORE_WATCH_PATHS", "ignore_watch_paths", ";"
        )
        result.get_string_if_exists("DRAFTER_WATCH_MANIFEST", "watch_manifest")
        result.get_bool_if_exists(
            "DRAFTER_WATCH_FORCE_RECURSIVE", "watch_force_recursive"
        )
        return result.as_dict()

    @staticmethod
    def extend_parser(parser):
        """Add development server arguments to the command line parser.

        Adds the "App Server Configuration" group with --port and --host
        (which have argparse defaults, unlike most other options), the
        negative flags --no-reloader, --no-open-browser, --no-inline-py, and
        --no-serve-adjacent-files, which store False on their fields, and
        the watch-policy options (--no-watch-adjacent-files,
        --no-watch-recursively, --no-watch-safe-mode,
        --no-watch-served-files, --watch-max-files, --watch-max-directories,
        --watch-max-depth, --watch-broad-locations, --watch-path,
        --ignore-watch-path, --watch-manifest, --watch-force-recursive).

        Args:
            parser: An argparse.ArgumentParser instance to extend.

        Returns:
            The "App Server Configuration" argument group that was added.
        """
        group = parser.add_argument_group("App Server Configuration")
        group.add_argument(
            "--port", type=int, default=8000, help="Port number for the server"
        )
        group.add_argument(
            "--host", type=str, default="localhost", help="Host address for the server"
        )
        group.add_argument(
            "--no-reloader",
            action="store_false",
            dest="use_reloader",
            help="Disable auto-reloader for code changes",
        )
        group.add_argument(
            "--no-open-browser",
            action="store_false",
            dest="open_browser",
            help="Do not automatically open web browser on start",
        )
        group.add_argument(
            "--no-inline-py",
            action="store_false",
            dest="inline_py",
            help="Do not inline user code in HTML; load via HTTP request instead",
        )
        group.add_argument(
            "--no-serve-adjacent-files",
            action="store_false",
            dest="serve_adjacent_files",
            help="Do not serve files from user directory",
        )
        # Watch policy flags all default to None so that parse_args only
        # reports them when explicitly given (otherwise the argparse default
        # would override lower-precedence sources like environment variables).
        group.add_argument(
            "--no-watch-adjacent-files",
            action="store_false",
            dest="watch_adjacent_files",
            default=None,
            help="Only watch the main file and explicitly configured paths",
        )
        group.add_argument(
            "--no-watch-recursively",
            action="store_false",
            dest="watch_recursively",
            default=None,
            help="Do not recursively watch the main file's directory (use safe mode)",
        )
        group.add_argument(
            "--no-watch-safe-mode",
            action="store_false",
            dest="watch_safe_mode",
            default=None,
            help="Skip safety checks before recursively watching the main file's directory",
        )
        group.add_argument(
            "--no-watch-served-files",
            action="store_false",
            dest="watch_served_files",
            default=None,
            help="In safe mode, do not add served files to the watch set",
        )
        group.add_argument(
            "--watch-max-files",
            type=int,
            default=None,
            help="Maximum files allowed in the main directory before safe mode is used",
        )
        group.add_argument(
            "--watch-max-directories",
            type=int,
            default=None,
            help="Maximum subdirectories allowed before safe mode is used",
        )
        group.add_argument(
            "--watch-max-depth",
            type=int,
            default=None,
            help="Maximum directory nesting depth allowed before safe mode is used",
        )
        group.add_argument(
            "--watch-broad-locations",
            action="store_true",
            default=None,
            help="Permit recursively watching broad locations like Desktop or Documents",
        )
        group.add_argument(
            "--watch-path",
            action="append",
            dest="watch_paths",
            default=None,
            help="Extra file, directory, or glob pattern to watch (repeatable)",
        )
        group.add_argument(
            "--ignore-watch-path",
            action="append",
            dest="ignore_watch_paths",
            default=None,
            help="File, directory, or glob pattern whose changes never trigger a reload (repeatable)",
        )
        group.add_argument(
            "--watch-manifest",
            type=str,
            default=None,
            help="Path to a JSON manifest listing the project's files to watch",
        )
        group.add_argument(
            "--watch-force-recursive",
            action="store_true",
            default=None,
            help="Recursively watch the main file's directory even when a safety check would refuse",
        )
        return group

    @staticmethod
    def parse_args(parsed_args: dict) -> dict:
        """Extract development server settings from parsed command line arguments.

        All values are copied when they are not None (rather than merely
        truthy), so False values from the --no-* flags are preserved.

        Args:
            parsed_args: A dictionary of parsed command line arguments.

        Returns:
            A dictionary of server configuration values that were provided.
        """
        result = {}
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
        for watch_key in (
            "watch_adjacent_files",
            "watch_recursively",
            "watch_safe_mode",
            "watch_served_files",
            "watch_max_files",
            "watch_max_directories",
            "watch_max_depth",
            "watch_broad_locations",
            "watch_paths",
            "ignore_watch_paths",
            "watch_manifest",
            "watch_force_recursive",
        ):
            if parsed_args.get(watch_key) is not None:
                result[watch_key] = parsed_args[watch_key]
        return result

    @property
    def ws_url(self) -> str:
        """Get WebSocket URL for live reload.

        Returns:
            WebSocket URL constructed from host, port, and internal route.
        """
        return f"ws://{self.host}:{self.port}/{INTERNAL_ROUTES['WS']}"
