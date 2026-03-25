from dataclasses import dataclass
from typing import Union, Optional
from drafter.helpers.env_vars import EnvVars
from drafter.config.base import BaseConfiguration

@dataclass
class BootstrapConfiguration(BaseConfiguration):
    mode: str = "start_server"  # Options: "start_server", "compile_site"
    config_file: Optional[list[str]] = None  # Semicolon-separated paths to config files, if needed
    verbose: bool = True
    
    @staticmethod
    def parse_env_variables(env_vars: dict) -> dict:
        result = EnvVars(env_vars)
        result.get_string_if_exists("DRAFTER_MODE", "compile")
        result.get_string_list_if_exists("DRAFTER_CONFIG_FILE", "config_file", ";")
        result.get_bool_if_exists("DRAFTER_VERBOSE", "verbose")
        return result.as_dict()
    
    @staticmethod
    def extend_parser(parser):
        group = parser.add_argument_group("Bootstrap Configuration")
        group.add_argument(
            "--compile",
            action="store_true",
            help="Compile the site to a file instead of starting the server"
        )
        group.add_argument(
            "--config-file",
            type=str,
            help="Path to a configuration file (can be specified multiple times for multiple files)",
            action="append"
        )
        group.add_argument(
            "--verbose",
            action="store_true",
            help="Enable verbose output"
        )
        return group
        
    @staticmethod
    def parse_args(parsed_args: dict) -> dict:
        result = {}
        if parsed_args.get("compile"):
            result["mode"] = "compile_site"
        if parsed_args.get("config_file"):
            result["config_file"] = parsed_args["config_file"]
        if parsed_args.get("verbose"):
            result["verbose"] = True
        return result