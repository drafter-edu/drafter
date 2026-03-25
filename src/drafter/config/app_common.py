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
    engine: EngineType = "skulpt"

    user_directory: Union[FalseType, str] = False
    main_filename: Union[FalseType, str] = False
    asset_directory: Union[FalseType, str] = False
    show_filename_as: Union[FalseType, str] = False
    prerender_initial_page: bool = True
    
    mount_drafter_locally: bool = False

    override_asset_url: Union[bool, str] = False

    site_title: str = "Drafter App Server"
    
    def get_full_main_file_path(self) -> Optional[str]:
        """Get the full path to the main user file.

        Returns:
            Full path to the main user file, or None if not set.
        """
        if self.user_directory is not False and self.main_filename is not False:
            return os.path.join(self.user_directory, self.main_filename)
        return None
                    
    def leverage_filesystem(self):
        if self.user_directory is False:
            found_path = seek_filename_by_line("start_server", self.main_filename)
            self.user_directory = (
                os.path.dirname(found_path) if found_path else os.getcwd()
            )
            self.main_filename = (
                os.path.basename(found_path)
                if found_path
                else (self.main_filename or "main.py")
            )

        elif not os.path.isdir(self.user_directory):
            if os.path.isfile(self.user_directory):
                self.main_filename = os.path.basename(self.user_directory)
                self.user_directory = os.path.dirname(self.user_directory)

        else:
            # TODO: Logic seems redundant, maybe only do it in app_server?
            self.main_filename = (
                self.main_filename if self.main_filename is not False else "main.py"
            )

        if self.show_filename_as is False:
            self.show_filename_as = self.main_filename
            
    @staticmethod
    def parse_env_variables(env_vars: dict) -> dict:
        result = EnvVars(env_vars)
        result.get_string_if_exists("DRAFTER_ENGINE", "engine")
        result.get_bool_if_exists("DRAFTER_PRERENDER_INITIAL_PAGE", "prerender_initial_page")
        result.get_string_if_exists("DRAFTER_USER_DIRECTORY", "user_directory")
        result.get_string_if_exists("DRAFTER_MAIN_FILENAME", "main_filename")
        result.get_string_if_exists("DRAFTER_ASSET_DIRECTORY", "asset_directory")
        result.get_string_if_exists("DRAFTER_SHOW_FILENAME_AS", "show_filename_as")
        result.get_bool_if_exists("DRAFTER_MOUNT_DRAFTER_LOCALLY", "mount_drafter_locally")
        result.get_string_if_exists("DRAFTER_OVERRIDE_ASSET_URL", "override_asset_url")
        result.get_string_if_exists("DRAFTER_SITE_TITLE", "site_title")
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
            "--user-directory",
            type=str,
            help="Directory containing user files (if not specified, will be inferred)",
        )
        group.add_argument(
            "--main-filename",
            type=str,
            help="Main user file to execute (if not specified, will be inferred)",
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
        return group
    
    @staticmethod
    def parse_args(parsed_args: dict) -> dict:
        result = {}
        if parsed_args.get("engine"):
            result["engine"] = parsed_args["engine"]
        if parsed_args.get("prerender_initial_page"):
            result["prerender_initial_page"] = True
        if parsed_args.get("user_directory"):
            result["user_directory"] = parsed_args["user_directory"]
        if parsed_args.get("main_filename"):
            result["main_filename"] = parsed_args["main_filename"]
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
        return result