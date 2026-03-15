"""Configuration processing for the Drafter app server.

Provides functions to process AppServerConfiguration based on command line
arguments and environment variables.
"""

import os
from typing import Optional
from dataclasses import fields
from drafter.helpers.utils import seek_filename_by_line
from drafter.config.app_server import AppServerConfiguration
from drafter.args.parser import parse_arguments, parse_environment_variables
from drafter.args.mapper import map_to_app_server_config


def process_app_server_configuration(
    config: AppServerConfiguration, 
    argv: Optional[list[str]], 
    local_vars: dict
) -> AppServerConfiguration:
    """Process the AppServerConfiguration based on command line arguments and local variables.

    This function can be used to adjust the server configuration based on command line arguments
    and other local variables, allowing for dynamic adjustments to the server setup.

    Args:
        config: The initial AppServerConfiguration instance.
        argv: The list of command line arguments (typically sys.argv).
        local_vars: A dictionary of local variables that may contain configuration settings.
    Returns:
        The processed AppServerConfiguration instance.
    """
    # Parse arguments if provided
    if argv is not None:
        parsed = parse_arguments(argv)
        env_vars = parse_environment_variables()
        config = map_to_app_server_config(parsed.args, env_vars, config)
    
    # Extract from local variables
    config.extract_from_args(local_vars)
    
    # Apply filesystem-based processing (this is idempotent)
    config.leverage_filesystem()
    
    return config