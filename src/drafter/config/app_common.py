from dataclasses import dataclass
from typing import Union, Optional, Literal

from drafter.helpers.env_vars import EnvVars
from drafter.config.engines import EngineType
from drafter.config.base import BaseConfiguration

FalseType = Literal[False]

DEFAULT_SYSTEM_PACKAGES = ["bakery", "matplotlib", "pillow"]
# "https://cdn.jsdelivr.net/pyodide/v0.29.0/debug/"
DEFAULT_PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v0.29.0/full/"


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
        engine: Python execution engine ("skulpt" or "pyodide").
        show_filename_as: Display name for main file in UI (if different).
        prerender_initial_page: Prerender initial page on server start.
        load_packages_automatically: Automatically load system and project packages.
        system_packages: List of system packages to load.
        project_packages: List of project-specific packages to load.
        pyodide_drafter_path: Optional custom path to the Drafter Pyodide package. If building from local, this is the relative path to the file (to be used as a URL). If using a CDN, this will be the full path to the wheel on PyPi or other CDN.
        pyodide_url: URL to load Pyodide from.

    """

    engine: EngineType = "pyodide"

    asset_directory: Union[FalseType, str] = False
    show_filename_as: Union[FalseType, str] = False
    prerender_initial_page: bool = True

    mount_drafter_locally: bool = False
    load_packages_automatically: bool = True

    system_packages: Optional[list[str]] = None
    project_packages: Optional[list[str]] = None
    pyodide_drafter_path: Optional[str] = None
    pyodide_url: Optional[str] = DEFAULT_PYODIDE_URL

    override_asset_url: Union[bool, str] = False

    site_title: str = "Drafter App Server"

    def __post_init__(self):
        # Skulpt's dataclass implementation is stricter with mutable defaults, so
        # initialize defaults after construction instead of using a list default.
        if self.system_packages is None:
            self.system_packages = list(DEFAULT_SYSTEM_PACKAGES)

    @staticmethod
    def get_key() -> str:
        return "app_common"

    @staticmethod
    def parse_env_variables(env_vars: dict) -> dict:
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
        result.get_string_if_exists("DRAFTER_OVERRIDE_ASSET_URL", "override_asset_url")
        result.get_string_if_exists("DRAFTER_SITE_TITLE", "site_title")
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
            help=f"Custom URL for loading Pyodide (default: '{DEFAULT_PYODIDE_URL}')",
        )

        group.add_argument(
            "--pyodide-drafter-path",
            type=str,
            help="Optional custom path to the Drafter Pyodide package (used if engine is 'pyodide')",
        )
        return group

    @staticmethod
    def parse_args(parsed_args: dict) -> dict:
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
        if parsed_args.get("load_packages_automatically"):
            result["load_packages_automatically"] = True
        if parsed_args.get("project_packages"):
            result["project_packages"] = parsed_args["project_packages"].split(";")
        if parsed_args.get("system_packages"):
            result["system_packages"] = parsed_args["system_packages"].split(";")
        if parsed_args.get("pyodide_url"):
            result["pyodide_url"] = parsed_args["pyodide_url"]
        if parsed_args.get("pyodide_drafter_path"):
            result["pyodide_drafter_path"] = parsed_args["pyodide_drafter_path"]
        return result
