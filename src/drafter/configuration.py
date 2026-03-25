'''
Handles configuring the Drafter runtime based on command line arguments,
environment variables, and configuration files. This module is responsible
for determining the mode of operation (e.g., start_server or compile_site)
and setting up the necessary runtime environment accordingly.
'''
from pprint import pprint
import sys
import os
from typing import Optional, Any
from drafter.helpers.args import get_argparser
from drafter.helpers.utils import is_web
from drafter.config.system import SystemConfiguration
from drafter.config.bootstrap import BootstrapConfiguration
from drafter.config.app_builder import AppBuilderConfiguration
from drafter.config.app_server import AppServerConfiguration
from drafter.config.app_common import AppCommonConfiguration
from drafter.config.client_server import ClientServerConfiguration



def get_preparser():
    """
    Get the preparser for handling bootstrap configuration.
    """
    preparser_maker = get_argparser()
    if preparser_maker is None:
        return None
    
    preparser = preparser_maker(add_help=False)
    BootstrapConfiguration.extend_parser(preparser)
    return preparser

def get_parser(mode: Optional[str] = None):
    """
    Get the CLI argument parser for the specified mode.
    If no mode is specified, it will default to "start_server".
    
    Args:
        mode: The mode of operation ("start_server" or "compile_site").
        
    Returns:
        An argument parser configured for the specified mode.
    """
    parser_maker = get_argparser()
    if parser_maker is None:
        return None
    
    parser = parser_maker()
    # Have to extend with the Bootstrap parser again to make sure the help text is included in the main CLI parser
    BootstrapConfiguration.extend_parser(parser)
    ClientServerConfiguration.extend_parser(parser)
    AppCommonConfiguration.extend_parser(parser)
    # Only parse the relevant configuration based on the mode
    if mode == "compile_site":
        AppBuilderConfiguration.extend_parser(parser)
    else:
        AppServerConfiguration.extend_parser(parser)
    
    return parser

def configure_system() -> SystemConfiguration:
    """
    Configure the Drafter system based on command line arguments, 
    environment variables, and configuration files. This function will create
    and return a SystemConfiguration object that encapsulates all relevant configurations.
    """
    #### Backup original arguments and environment variables
    original_arguments = sys.argv[1:]
    environment_variables = dict(os.environ)
    
    ##### Bootstrap configuration processing
    bootstrap_config = BootstrapConfiguration()
    # bootstrap_config.merge_in_args(initial_variables, False)
    # Environment variables
    bootstrap_env_vars = BootstrapConfiguration.parse_env_variables(environment_variables)
    bootstrap_config.merge_in_args(bootstrap_env_vars, False)
    # CLI args
    preparser = get_preparser()
    if preparser is not None:
        # Preparse known arguments to determine mode
        parsed_pre, unknown_args = preparser.parse_known_args(original_arguments)
        parsed_args = BootstrapConfiguration.parse_args(vars(parsed_pre))
        bootstrap_config.merge_in_args(parsed_args, raise_errors=False)
    # Config files
    if bootstrap_config.config_file is not None:
        for path in bootstrap_config.config_file:
            bootstrap_config.merge_in_file(path, raise_errors=False)
    
    ##### Create All Other Configurations
    client_server_config = ClientServerConfiguration()
    app_builder_config = AppBuilderConfiguration()
    app_server_config = AppServerConfiguration()
    app_common_config = AppCommonConfiguration()
    
    # Parsing only happens in CLI contexts, not browser contexts
    parser = get_parser(bootstrap_config.mode)
    if parser is not None:
        parsed, unknown_args = parser.parse_known_args(original_arguments)
    else:
        parsed, unknown_args = None, original_arguments
    
    #### Populate All Other Configurations
    # Merge configurations in order of priority:
    # environment variables < CLI args < config files
    for config in [client_server_config, app_builder_config, app_server_config, app_common_config]:
        # Environment variables
        env_vars = config.parse_env_variables(environment_variables)
        config.merge_in_args(env_vars, False)
        # CLI Args
        if parsed:
            parsed_args = config.parse_args(vars(parsed))
            config.merge_in_args(parsed_args, raise_errors=False)
    
        # From files
        if bootstrap_config.config_file is not None:
            for path in bootstrap_config.config_file:
                config.merge_in_file(path, raise_errors=False)
    
        # Leverage filesystem for any additional configuration
        if not is_web():
            config.leverage_filesystem()
    
    #### Create SystemConfiguration
    # Merge all configurations into a single SystemConfiguration
    system = SystemConfiguration(
        bootstrap=bootstrap_config,
        client_server=client_server_config,
        app_common=app_common_config,
        app_builder=app_builder_config,
        app_server=app_server_config
    )
    
    if bootstrap_config.verbose:
        print("Configuration completed. Final configuration:")
        print(system)
    
    return system

    
        
_SYSTEM: SystemConfiguration | None = None

def get_system_configuration() -> SystemConfiguration:
    """
    Get the global SystemConfiguration instance. If it hasn't been created yet,
    this function will call configure_system() to create it.
    """
    global _SYSTEM
    if _SYSTEM is None:
        _SYSTEM = configure_system()
    return _SYSTEM

def _set_system_for_testing(system: SystemConfiguration) -> None:
    """
    Set the global SystemConfiguration instance for testing purposes.
    This allows tests to inject a specific configuration without relying on
    command line arguments or environment variables.
    """
    global _SYSTEM
    _SYSTEM = system
    
def _reset_system_for_testing() -> None:
    """
    Reset the global SystemConfiguration instance for testing purposes.
    This allows tests to clear any previously set configuration and start fresh.
    """
    global _SYSTEM
    _SYSTEM = None