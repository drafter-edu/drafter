"""Configuration shared by the Drafter app server and site builder.

Defines AppCommonConfiguration, which holds settings common to both serving
and compiling a site: the execution engine, asset locations, page prerendering,
and Python package loading (including Pyodide specifics).
"""

from dataclasses import dataclass
from typing import Literal

from drafter.config.base import BaseConfiguration
from drafter.config.engines import EngineType
from drafter.helpers.env_vars import EnvVars

FalseType = Literal[False]
"""Type alias for the literal value `False`, used in `Union[FalseType, str]`
annotations where a field is either disabled (`False`) or holds a string."""

DEFAULT_SYSTEM_PACKAGES = ["bakery", "pillow"]
"""Default Python packages loaded into the execution engine for student sites.

Matplotlib is intentionally not preloaded; it is installed on demand when
student code imports it or uses the `MatPlotLibPlot` component."""

DEFAULT_PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide"
"""Default base CDN URL that Pyodide is loaded from (without version/branch)."""

DEFAULT_PYODIDE_VERSION = "v314.0.5"
"""Default Pyodide version segment of the URL (e.g. "v314.0.5" or "dev")."""

PyodideBranch = Literal["full", "debug"]
"""Type alias for the Pyodide distribution branch: "full" (minified,
production) or "debug" (unminified, with source maps)."""

DEFAULT_PYODIDE_BRANCH: PyodideBranch = "full"
"""Default Pyodide distribution branch."""


@dataclass
class AppCommonConfiguration(BaseConfiguration):
    """
    Common configuration options for the Drafter app, in terms of the server and compiler behavior.
    Settings for student site stuff actually belong in the ClientServer section.

    Attributes:
        mount_drafter_locally: Mount Drafter locally vs. from package. Used for local dev.
        asset_directory: Static assets directory (uses the packages' `src/drafter/assets/` folder if false and exists, then falls back to `js/dist/` if not, otherwise throws error).
        override_asset_url: Custom asset URL (False to use defaults). When building, this will be used to name the output folder.
        site_title: Browser tab title.
        favicon: URL or adjacent file path for the browser tab icon; empty
            string uses the built-in Drafter favicon.
        engine: Python execution engine ("skulpt" or "pyodide").
        show_filename_as: Display name for main file in UI (if different).
        prerender_initial_page: Prerender initial page on server start.
        load_packages_automatically: Automatically load system and project packages.
        system_packages: List of system packages to load.
        project_packages: List of project-specific packages to load.
        pyodide_drafter_path: Optional custom path to the Drafter Pyodide package. If building from local, this is the relative path to the file (to be used as a URL). If using a CDN, this will be the full path to the wheel on PyPi or other CDN.
        pyodide_url: Base URL to load Pyodide from (e.g. the jsDelivr CDN root).
            The version and branch are appended to this; see `get_pyodide_url`.
        pyodide_version: Pyodide version segment of the URL, such as
            "v314.0.5" or "dev".
        pyodide_branch: Pyodide distribution branch, "full" (default) or "debug".

    """

    engine: EngineType = "pyodide"

    asset_directory: FalseType | str = False
    show_filename_as: FalseType | str = False
    prerender_initial_page: bool = True

    mount_drafter_locally: bool = False
    load_packages_automatically: bool = True

    system_packages: list[str] | None = None
    project_packages: list[str] | None = None
    pyodide_drafter_path: str | None = None
    pyodide_url: str | None = DEFAULT_PYODIDE_URL
    pyodide_version: str | None = DEFAULT_PYODIDE_VERSION
    pyodide_branch: PyodideBranch | None = DEFAULT_PYODIDE_BRANCH

    override_asset_url: bool | str = False

    site_title: str = "Drafter App Server"
    favicon: str = ""

    def __post_init__(self):
        """Populate mutable field defaults after dataclass construction."""
        # Skulpt's dataclass implementation is stricter with mutable defaults, so
        # initialize defaults after construction instead of using a list default.
        if self.system_packages is None:
            self.system_packages = list(DEFAULT_SYSTEM_PACKAGES)
        if self.pyodide_branch is not None and self.pyodide_branch not in (
            "full",
            "debug",
        ):
            raise ValueError(
                f"pyodide_branch must be 'full' or 'debug', not {self.pyodide_branch!r}"
            )

    def get_pyodide_url(self) -> str:
        """Compose the full URL that Pyodide is loaded from.

        Joins `pyodide_url` (base), `pyodide_version`, and `pyodide_branch`
        with slashes, falling back to the defaults for any that are unset and
        ignoring duplicate slashes at the joins.

        Returns:
            The full Pyodide URL, e.g.
            "https://cdn.jsdelivr.net/pyodide/v314.0.5/full".
        """
        base = (self.pyodide_url or DEFAULT_PYODIDE_URL).rstrip("/")
        version = (self.pyodide_version or DEFAULT_PYODIDE_VERSION).strip("/")
        branch = (self.pyodide_branch or DEFAULT_PYODIDE_BRANCH).strip("/")
        return f"{base}/{version}/{branch}"

    @staticmethod
    def get_key() -> str:
        """Return the key identifying this configuration section.

        Returns:
            The string "app_common".
        """
        return "app_common"

    @staticmethod
    def parse_env_variables(env_vars: dict) -> dict:
        """Extract common app settings from environment variables.

        Reads the DRAFTER_-prefixed variables for the engine, prerendering,
        asset directory, filename display, local mounting, Pyodide Drafter
        path, Pyodide URL/version/branch, asset URL override, site title, favicon, automatic package
        loading, and the semicolon-separated project/system package lists.

        Args:
            env_vars: A dictionary of environment variables.

        Returns:
            A dictionary of common app configuration values that were present.
        """
        result = EnvVars(env_vars)
        result.get_string_if_exists("DRAFTER_ENGINE", "engine")
        result.get_bool_if_exists(
            "DRAFTER_PRERENDER_INITIAL_PAGE", "prerender_initial_page"
        )
        result.get_string_if_exists("DRAFTER_ASSET_DIRECTORY", "asset_directory")
        result.get_string_if_exists("DRAFTER_SHOW_FILENAME_AS", "show_filename_as")
        result.get_bool_if_exists(
            "DRAFTER_MOUNT_DRAFTER_LOCALLY", "mount_drafter_locally"
        )
        result.get_string_if_exists(
            "DRAFTER_PYODIDE_DRAFTER_PATH", "pyodide_drafter_path"
        )
        result.get_string_if_exists("DRAFTER_PYODIDE_URL", "pyodide_url")
        result.get_string_if_exists("DRAFTER_PYODIDE_VERSION", "pyodide_version")
        result.get_string_if_exists("DRAFTER_PYODIDE_BRANCH", "pyodide_branch")
        result.get_string_if_exists("DRAFTER_OVERRIDE_ASSET_URL", "override_asset_url")
        result.get_string_if_exists("DRAFTER_SITE_TITLE", "site_title")
        result.get_string_if_exists("DRAFTER_FAVICON", "favicon")
        result.get_bool_if_exists(
            "DRAFTER_LOAD_PACKAGES_AUTOMATICALLY", "load_packages_automatically"
        )
        result.get_string_list_if_exists(
            "DRAFTER_PROJECT_PACKAGES", "project_packages", ";"
        )
        result.get_string_list_if_exists(
            "DRAFTER_SYSTEM_PACKAGES", "system_packages", ";"
        )
        return result.as_dict()

    @staticmethod
    def extend_parser(parser):
        """Add common app arguments to the command line parser.

        Adds the "App Common Configuration" group with options such as
        --engine, --prerender-initial-page, --asset-directory, --site-title,
        --project-packages, --system-packages, --pyodide-url,
        --pyodide-version, --pyodide-branch, and --pyodide-drafter-path.

        Args:
            parser: An argparse.ArgumentParser instance to extend.

        Returns:
            The "App Common Configuration" argument group that was added.
        """
        group = parser.add_argument_group("App Common Configuration")
        group.add_argument(
            "--engine",
            type=str,
            choices=["skulpt", "pyodide"],
            help="Python execution engine to compile for ('skulpt' or 'pyodide')",
        )
        group.add_argument(
            "--prerender-initial-page",
            action="store_true",
            help="Prerender the initial page on server start",
        )
        group.add_argument(
            "--asset-directory",
            type=str,
            help="Directory containing assets (if not specified, will be inferred)",
        )
        group.add_argument(
            "--show-filename-as",
            type=str,
            help="Display name for main file in UI (if different)",
        )
        group.add_argument(
            "--mount-drafter-locally",
            action="store_true",
            help="Mount Drafter locally vs. from package. Used for local dev.",
        )
        group.add_argument(
            "--override-asset-url",
            type=str,
            help="Custom asset URL (False to use defaults)",
        )
        group.add_argument(
            "--site-title",
            type=str,
            help="Browser tab title",
        )
        group.add_argument(
            "--favicon",
            type=str,
            help=(
                "Icon shown in the browser tab: a URL or the path to an "
                "image file (svg, png, ico, ...) adjacent to your site"
            ),
        )
        group.add_argument(
            "--load-packages-automatically",
            action="store_true",
            help="Load Python packages detected in students' code automatically on startup. This will be in addition to whatever are explicitly listed in the --system-packages and --project-packages options.",
        )
        group.add_argument(
            "--project-packages",
            type=str,
            help="List of project-specific Python packages to load (semicolon-separated)",
        )
        group.add_argument(
            "--system-packages",
            type=str,
            help=f"List of system-specific Python packages to load (semicolon-separated). The defaults ('{';'.join(DEFAULT_SYSTEM_PACKAGES)}') are usually fine, but you can override them if needed.",
        )
        group.add_argument(
            "--pyodide-url",
            type=str,
            help=f"Base URL for loading Pyodide; the version and branch are appended (default: '{DEFAULT_PYODIDE_URL}')",
        )
        group.add_argument(
            "--pyodide-version",
            type=str,
            help=f"Pyodide version to load, e.g. 'v314.0.5' or 'dev' (default: '{DEFAULT_PYODIDE_VERSION}')",
        )
        group.add_argument(
            "--pyodide-branch",
            type=str,
            choices=["full", "debug"],
            help=f"Pyodide distribution branch: 'full' or 'debug' (default: '{DEFAULT_PYODIDE_BRANCH}')",
        )

        group.add_argument(
            "--pyodide-drafter-path",
            type=str,
            help="Optional custom path to the Drafter Pyodide package (used if engine is 'pyodide')",
        )
        return group

    @staticmethod
    def parse_args(parsed_args: dict) -> dict:
        """Extract common app settings from parsed command line arguments.

        The --project-packages and --system-packages values are split on
        semicolons into lists.

        Args:
            parsed_args: A dictionary of parsed command line arguments.

        Returns:
            A dictionary of common app configuration values that were provided.
        """
        result = {}
        if parsed_args.get("engine"):
            result["engine"] = parsed_args["engine"]
        if parsed_args.get("prerender_initial_page"):
            result["prerender_initial_page"] = True
        if parsed_args.get("asset_directory"):
            result["asset_directory"] = parsed_args["asset_directory"]
        if parsed_args.get("show_filename_as"):
            result["show_filename_as"] = parsed_args["show_filename_as"]
        if parsed_args.get("mount_drafter_locally"):
            result["mount_drafter_locally"] = True
        if parsed_args.get("override_asset_url"):
            result["override_asset_url"] = parsed_args["override_asset_url"]
        if parsed_args.get("site_title"):
            result["site_title"] = parsed_args["site_title"]
        if parsed_args.get("favicon"):
            result["favicon"] = parsed_args["favicon"]
        if parsed_args.get("load_packages_automatically"):
            result["load_packages_automatically"] = True
        if parsed_args.get("project_packages"):
            result["project_packages"] = parsed_args["project_packages"].split(";")
        if parsed_args.get("system_packages"):
            result["system_packages"] = parsed_args["system_packages"].split(";")
        if parsed_args.get("pyodide_url"):
            result["pyodide_url"] = parsed_args["pyodide_url"]
        if parsed_args.get("pyodide_version"):
            result["pyodide_version"] = parsed_args["pyodide_version"]
        if parsed_args.get("pyodide_branch"):
            result["pyodide_branch"] = parsed_args["pyodide_branch"]
        if parsed_args.get("pyodide_drafter_path"):
            result["pyodide_drafter_path"] = parsed_args["pyodide_drafter_path"]
        return result
