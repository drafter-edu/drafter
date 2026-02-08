import os
from typing import Optional
from drafter.helpers.utils import seek_filename_by_line
from drafter.config.app_server import AppServerConfiguration
from drafter.helpers.args import get_argparser


def parse_command_line_args(argv):
    argparser = get_argparser()
    if argparser is None:
        return {}
    parser = argparser(description="Launch the Drafter App Server.")

    parser.add_argument(
        "main_filename", help="The main Python file to run in the App Server."
    )

    parser.add_argument("--engine", type=str, choices=["skulpt", "pyodide"])
    parser.add_argument(
        "--mount_drafter_locally",
        action="store_true",
        help="Mount the Drafter package directory locally in the web environment.",
    )

    return vars(parser.parse_args(argv))

def process_app_server_configuration(config: AppServerConfiguration, argv: Optional[list[str]], local_vars: dict) -> AppServerConfiguration:
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
    # TODO: Handle environment variables
    # TODO: Handle config files
    config.merge_in_args(parse_command_line_args(argv))
    config.extract_from_args(locals())
    config.leverage_filesystem()
    
    return config