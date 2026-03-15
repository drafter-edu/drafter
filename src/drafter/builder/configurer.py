"""Configuration processing for the Drafter builder/compiler.

Provides functions to process AppBuilderConfiguration based on command line
arguments and environment variables.
"""

from typing import Optional
from drafter.config.app_builder import AppBuilderConfiguration
from drafter.config.client_server import ClientServerConfiguration
from drafter.args.parser import parse_arguments, parse_environment_variables
from drafter.args.mapper import map_to_app_builder_config


def process_builder_config(
    config: AppBuilderConfiguration,
    client_server_config: ClientServerConfiguration,
    argv: Optional[list[str]]
) -> AppBuilderConfiguration:
    """Process the AppBuilderConfiguration based on the ClientServerConfiguration.

    This function can be used to adjust the builder configuration based on command line
    arguments and environment variables, allowing for dynamic adjustments to the build process.

    Args:
        config: The initial AppBuilderConfiguration instance.
        client_server_config: The ClientServerConfiguration instance with server settings.
        argv: The list of command line arguments (typically sys.argv).
    Returns:
        The processed AppBuilderConfiguration instance.
    """
    # Parse arguments if provided
    if argv is not None:
        parsed = parse_arguments(argv)
        env_vars = parse_environment_variables()
        config = map_to_app_builder_config(parsed.args, env_vars, config)
    
    # Apply filesystem-based processing
    config.leverage_filesystem()
    
    return config