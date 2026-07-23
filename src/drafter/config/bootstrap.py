"""Configuration for bootstrapping a Drafter application.

Defines BootstrapConfiguration, which captures the settings needed before the
system fully starts: the path to the user's main entry file, whether to start
the server or compile the site, any extra configuration files, and verbosity.
"""

import os
from dataclasses import dataclass
from typing import Optional
from drafter.helpers.env_vars import EnvVars
from drafter.config.base import BaseConfiguration


@dataclass
class BootstrapConfiguration(BaseConfiguration):
    """Configuration options for bootstrapping the Drafter system.

    These settings determine what to run and how, before the rest of the
    system starts: the user's entry file, the run mode, and any additional
    configuration files to load.

    Attributes:
        path: Path to the main entry file for the application (e.g.,
            "my_site.py"). Optional at construction, but must be provided at
            some point before the user directory or filename can be resolved.
        mode: What to do on startup; options are "start_server" and
            "compile_site".
        config_file: Optional list of paths to configuration files. Set via
            the semicolon-separated DRAFTER_CONFIG_FILE environment variable
            or by repeating the --config-file flag.
        verbose: Whether to enable verbose output.
    """

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
        """Return the key identifying this configuration section.

        Returns:
            The string "bootstrap".
        """
        return "bootstrap"

    def get_user_directory(self) -> str:
        """Determine the directory containing the user's main entry file.

        Returns:
            The absolute path of the directory containing `path`.

        Raises:
            ValueError: If `path` has not been set.
        """
        if self.path is not None:
            return os.path.dirname(os.path.abspath(self.path))
        # TODO: Should we use the current working directory as a fallback?
        raise ValueError(
            "Cannot determine user directory because the path to the main user file is not specified."
        )

    def get_main_filename(self) -> str:
        """Determine the filename of the user's main entry file.

        Returns:
            The basename of `path` (e.g., "my_site.py").

        Raises:
            ValueError: If `path` has not been set.
        """
        if self.path is not None:
            return os.path.basename(self.path)
        raise ValueError(
            "Cannot determine main filename because the path to the main user file is not specified."
        )

    @staticmethod
    def parse_env_variables(env_vars: dict) -> dict:
        """Extract bootstrap settings from environment variables.

        Reads DRAFTER_ENTRY (path), DRAFTER_MODE (mode), DRAFTER_CONFIG_FILE
        (semicolon-separated list of config files), and DRAFTER_VERBOSE.

        Args:
            env_vars: A dictionary of environment variables.

        Returns:
            A dictionary of bootstrap configuration values that were present.
        """
        result = EnvVars(env_vars)
        result.get_string_if_exists("DRAFTER_ENTRY", "path")
        # TODO: Accept `compile` and `serve` also?
        result.get_string_if_exists("DRAFTER_MODE", "mode")
        result.get_string_list_if_exists("DRAFTER_CONFIG_FILE", "config_file", ";")
        result.get_bool_if_exists("DRAFTER_VERBOSE", "verbose")
        return result.as_dict()

    @staticmethod
    def extend_parser(parser):
        """Add bootstrap arguments to the command line parser.

        Adds the positional `path` argument directly to the parser, then adds
        the "Bootstrap Configuration" group with --compile, --config-file
        (repeatable), and --verbose.

        Args:
            parser: An argparse.ArgumentParser instance to extend.

        Returns:
            The "Bootstrap Configuration" argument group that was added.
        """
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
        """Extract bootstrap settings from parsed command line arguments.

        Note the transform: the --compile flag sets `mode` to "compile_site"
        rather than mapping to a field of the same name.

        Args:
            parsed_args: A dictionary of parsed command line arguments.

        Returns:
            A dictionary of bootstrap configuration values that were provided.
        """
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
