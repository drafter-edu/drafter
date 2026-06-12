import os
from dataclasses import dataclass, field, fields
from typing import Union, Optional, Literal

from drafter.helpers.env_vars import EnvVars
from drafter.helpers.utils import seek_filename_by_line
from drafter.config.engines import EngineType
from drafter.config.base import BaseConfiguration

FalseType = Literal[False]

@dataclass
class AppCommonConfiguration(BaseConfiguration):
    engine: EngineType = "pyodide"

    asset_directory: Union[FalseType, str] = False
    show_filename_as: Union[FalseType, str] = False
    prerender_initial_page: bool = True
    
    mount_drafter_locally: bool = False
    load_packages_automatically: bool = True
    explicit_package_list: Optional[list[str]] = None

    override_asset_url: Union[bool, str] = False

    site_title: str = "Drafter App Server"
    
    @staticmethod
    def get_key() -> str:
        return "app_common"
                        
    def leverage_filesystem(self):
        pass
        
    @staticmethod
    def parse_env_variables(env_vars: dict) -> dict:
        result = EnvVars(env_vars)
        result.get_string_if_exists("DRAFTER_ENGINE", "engine")
        result.get_bool_if_exists("DRAFTER_PRERENDER_INITIAL_PAGE", "prerender_initial_page")
        result.get_string_if_exists("DRAFTER_ASSET_DIRECTORY", "asset_directory")
        result.get_string_if_exists("DRAFTER_SHOW_FILENAME_AS", "show_filename_as")
        result.get_bool_if_exists("DRAFTER_MOUNT_DRAFTER_LOCALLY", "mount_drafter_locally")
        result.get_string_if_exists("DRAFTER_OVERRIDE_ASSET_URL", "override_asset_url")
        result.get_string_if_exists("DRAFTER_SITE_TITLE", "site_title")
        result.get_bool_if_exists("DRAFTER_LOAD_PACKAGES_AUTOMATICALLY", "load_packages_automatically")
        result.get_string_list_if_exists("DRAFTER_EXPLICIT_PACKAGE_LIST", "explicit_package_list", ";")
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
            help="Load Python packages automatically on startup",
        )
        group.add_argument(
            "--explicit-package-list",
            type=str,
            help="List of explicit Python packages to load (semicolon-separated)",
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
        if parsed_args.get("explicit_package_list"):
            result["explicit_package_list"] = parsed_args["explicit_package_list"].split(";")
        return result