from typing import Optional
from drafter.config.app_builder import AppBuilderConfiguration
from drafter.config.client_server import ClientServerConfiguration
from drafter.helpers.args import get_argparser


def parse_command_line_args(argv):
    argparser = get_argparser()
    if argparser is None:
        return {}
    parser = argparser(description="Launch the Drafter App Server.")

    parser.add_argument(
        "main_filename", help="The main Python file to run in the App Server."
    )
    
    parser.add_argument("--output_directory",
                        help="The directory to output the built website to.")
    parser.add_argument("--output_filename",
                        help="The filename for the main output HTML file.")
    
    
    parser.add_argument("--user_directory", help="The user directory to serve files from.")
    
    parser.add_argument("--prerender_initial_page", action='store_true', 
                        help="Whether to prerender the initial page into the output HTML file.")

    parser.add_argument("--engine", type=str, choices=["skulpt", "pyodide"])
    parser.add_argument(
        "--mount_drafter_locally",
        action="store_true",
        help="Mount the Drafter package directory locally in the web environment.",
    )
    
    parser.add_argument("--pyodide_package_style", type=str, choices=["build", "cdn", "pypi"],
                        help="Custom style for the Pyodide package (used if engine is 'pyodide'). The 'build' option means that the local version of Drafter will be built for pyodide.")
    
    parser.add_argument(
        "--pyodide_drafter_path",
        type=str,
        help="Custom path to the Drafter Pyodide package (used if engine is 'pyodide')."
    )

    return vars(parser.parse_args(argv))


def process_builder_config(config: AppBuilderConfiguration, client_server_config: ClientServerConfiguration, argv: Optional[list[str]]) -> AppBuilderConfiguration:
    """Process the AppBuilderConfiguration based on the ClientServerConfiguration.

    This function can be used to adjust the builder configuration based on the server configuration,
    allowing for dynamic adjustments to the build process.

    Args:
        config: The initial AppBuilderConfiguration instance.
        client_server_config: The ClientServerConfiguration instance with server settings.
    Returns:
        The processed AppBuilderConfiguration instance.
    """
    config.merge_in_args(parse_command_line_args(argv))
    config.leverage_filesystem()
    return config