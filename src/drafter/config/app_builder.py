from typing import Optional, Union
from dataclasses import dataclass, field

from drafter.helpers.env_vars import EnvVars
from drafter.config.engines import EngineType
from drafter.config.base import BaseConfiguration

@dataclass
class AppBuilderConfiguration(BaseConfiguration):
    """Configuration for the compilation process that builds a static version of the site.
    
    The compilation process will also have access to the current `ClientServerConfiguration` 
    to generate the logic on the actual built page. These settings are the ones unique
    to the compilation process. Note that it also inherits from `AppBackendConfig`, so it also
    includes all the generic backend settings common to both the Starlette server and the compilation process.
    
    # TODO: Single file output, whether to use CDN for assets, etc.
    
    Attributes:
        verbose: Enable verbose logging to stdout.
        output_directory: Directory to output the built site files.
        output_filename: Name of the main HTML file to generate.
        create_404: Whether to create a 404.html file (options: "always", "never", "if_missing").
        prerender_initial_page: Whether to prerender the HTML of the page into the output file.
        engine: Python execution engine to compile for ("skulpt" or "pyodide").
        warn_missing_info: Whether to echo a warning if set_site_information is missing.
        additional_paths: List of additional file paths to make available in the built site (e.g., for `open`).
        zip_output: Whether to zip the output directory after building.
        
        pyodide_drafter_path: Optional custom path to the Drafter Pyodide package (used if engine is "pyodide").
        pyodide_package_style: Optional custom style for the Pyodide package ("build", "cdn", or "pypi"). The "build" option means that the local version of Drafter will be built for pyodide.
    """
    output_directory: str = "dist"
    output_filename: str = "index.html"
    create_404: str = "if_missing"  # Options: "always", "never", "if_missing"
    
    zip_output: bool = False
    
    warn_missing_info: bool = True
    
    pyodide_package_style: Optional[str] = "build" # "build", "cdn", or "pypi"
    pyodide_drafter_path: Optional[str] = None
    
    additional_paths: list[str] = field(default_factory=list)
    
    @staticmethod
    def get_key() -> str:
        return "app_builder"
    
    @staticmethod
    def parse_env_variables(env_vars: dict) -> dict:
        result = EnvVars(env_vars)
        result.get_string_if_exists("DRAFTER_OUTPUT_DIRECTORY", "output_directory")
        result.get_string_if_exists("DRAFTER_OUTPUT_FILENAME", "output_filename")
        result.get_string_if_exists("DRAFTER_CREATE_404", "create_404")
        result.get_bool_if_exists("DRAFTER_ZIP_OUTPUT", "zip_output")
        result.get_bool_if_exists("DRAFTER_WARN_MISSING_INFO", "warn_missing_info")
        result.get_string_list_if_exists("DRAFTER_ADDITIONAL_PATHS", "additional_paths", ";")
        result.get_string_if_exists("DRAFTER_PYODIDE_PACKAGE_STYLE", "pyodide_package_style")
        result.get_string_if_exists("DRAFTER_PYODIDE_DRAFTER_PATH", "pyodide_drafter_path")
        return result.as_dict()
    
    @staticmethod
    def extend_parser(parser):
        group = parser.add_argument_group("App Builder Configuration")
        group.add_argument(
            "--output-directory",
            type=str,
            help="Directory to output the built site files",
        )
        group.add_argument(
            "--output-filename",
            type=str,
            help="Name of the main HTML file to generate",
        )
        group.add_argument(
            "--create-404",
            type=str,
            choices=["always", "never", "if_missing"],
            help="Whether to create a 404.html file (options: 'always', 'never', 'if_missing')",
        )
        group.add_argument(
            "--zip-output",
            action="store_true",
            help="Whether to zip the output directory after building",
        )
        group.add_argument(
            "--warn-missing-info",
            action="store_true",
            help="Whether to echo a warning if set_site_information is missing",
        )
        group.add_argument(
            "--additional-paths",
            type=str,
            help="Semicolon-separated list of additional file paths to make available in the built site (e.g., for `open`)",
        )
        group.add_argument(
            "--pyodide-package-style",
            type=str,
            choices=["build", "cdn", "pypi"],
            help="Optional custom style for the Pyodide package ('build', 'cdn', or 'pypi')",
        )
        group.add_argument(
            "--pyodide-drafter-path",
            type=str,
            help="Optional custom path to the Drafter Pyodide package (used if engine is 'pyodide')",
        )
        return group
    
    @staticmethod
    def parse_args(parsed_args: dict) -> dict:
        result = {}
        if parsed_args.get("output_directory"):
            result["output_directory"] = parsed_args["output_directory"]
        if parsed_args.get("output_filename"):
            result["output_filename"] = parsed_args["output_filename"]
        if parsed_args.get("create_404"):
            result["create_404"] = parsed_args["create_404"]
        if parsed_args.get("zip_output"):
            result["zip_output"] = True
        if parsed_args.get("warn_missing_info"):
            result["warn_missing_info"] = True
        if parsed_args.get("additional_paths"):
            result["additional_paths"] = parsed_args["additional_paths"].split(";")
        if parsed_args.get("pyodide_package_style"):
            result["pyodide_package_style"] = parsed_args["pyodide_package_style"]
        if parsed_args.get("pyodide_drafter_path"):
            result["pyodide_drafter_path"] = parsed_args["pyodide_drafter_path"]
        return result
    
