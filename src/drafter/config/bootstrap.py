import os
from dataclasses import dataclass
from typing import Optional
from drafter.helpers.env_vars import EnvVars
from drafter.config.base import BaseConfiguration


@dataclass
class BootstrapConfiguration(BaseConfiguration):
    path: Optional[str] = (
        None  # The main entry file for the application (e.g., "my_site.py"). Must be provided SOMEWHERE at SOME POINT.
    )
    mode: str = "start_server"  # Options: "start_server", "compile_site"
    config_file: Optional[list[str]] = (
        # Paths to config files, if needed. Set via the semicolon-separated
        # DRAFTER_CONFIG_FILE env var or by repeating the --config-file flag.
        None
    )
    verbose: bool = False

    @staticmethod
    def get_key() -> str:
        return "bootstrap"

    def get_user_directory(self) -> str:
        if self.path is not None:
            return os.path.dirname(os.path.abspath(self.path))
        # TODO: Should we use the current working directory as a fallback?
        raise ValueError(
            "Cannot determine user directory because the path to the main user file is not specified."
        )

    def get_main_filename(self) -> str:
        if self.path is not None:
            return os.path.basename(self.path)
        raise ValueError(
            "Cannot determine main filename because the path to the main user file is not specified."
        )

    @staticmethod
    def parse_env_variables(env_vars: dict) -> dict:
        result = EnvVars(env_vars)
        result.get_string_if_exists("DRAFTER_ENTRY", "path")
        # TODO: Accept `compile` and `serve` also?
        result.get_string_if_exists("DRAFTER_MODE", "mode")
        result.get_string_list_if_exists("DRAFTER_CONFIG_FILE", "config_file", ";")
        result.get_bool_if_exists("DRAFTER_VERBOSE", "verbose")
        return result.as_dict()

    @staticmethod
    def extend_parser(parser):
        parser.add_argument(
            "path",
            type=str,
            nargs="?",
            help="Path to the main entry file for the application (e.g., my_site.py).",
        )
        group = parser.add_argument_group("Bootstrap Configuration")
        group.add_argument(
            "--compile",
            action="store_true",
            help="Compile the site to a file instead of starting the server",
        )
        group.add_argument(
            "--config-file",
            type=str,
            help="Path to a configuration file (can be specified multiple times for multiple files)",
            action="append",
        )
        group.add_argument(
            "--verbose", action="store_true", help="Enable verbose output"
        )
        return group

    @staticmethod
    def parse_args(parsed_args: dict) -> dict:
        result = {}
        if parsed_args.get("path") is not None:
            result["path"] = parsed_args["path"]
        if parsed_args.get("compile"):
            result["mode"] = "compile_site"
        if parsed_args.get("config_file"):
            result["config_file"] = parsed_args["config_file"]
        if parsed_args.get("verbose"):
            result["verbose"] = True
        return result
