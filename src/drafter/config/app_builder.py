from typing import Optional, Union
from dataclasses import dataclass, field

from drafter.config.app_backend import AppBackendConfig
from drafter.config.engines import EngineType


@dataclass
class AppBuilderConfiguration(AppBackendConfig):
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
    verbose: bool = False
    output_directory: str = "dist"
    output_filename: str = "index.html"
    create_404: str = "if_missing"  # Options: "always", "never", "if_missing"
    
    zip_output: bool = False
    
    prerender_initial_page: bool = True
    engine: EngineType = "skulpt"
    
    warn_missing_info: bool = True
    
    pyodide_package_style: Optional[str] = "build" # "build", "cdn", or "pypi"
    pyodide_drafter_path: Optional[str] = None
    
    additional_paths: list[str] = field(default_factory=list)
    
    
