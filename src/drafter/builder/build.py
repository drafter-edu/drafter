import sys
import os
from typing import Optional
import shutil
import zipfile
from pathlib import Path
from drafter.config.app_builder import AppBuilderConfiguration
from drafter.config.client_server import ClientServerConfiguration
from drafter.builder.configurer import process_builder_config
from drafter.client_server.commands import get_main_server
from drafter.config.urls import determine_assets_url
from drafter.scaffolding.templating import render_index_html
from drafter.scaffolding.utils import pkg_assets_dir, pkg_root, pkg_package_root

def build_zip(source_dir: Path, output_zip: str, skip_extensions: Optional[set[str]] = None):
    """Build a zip file from the source directory.

    Args:
        source_dir: Path to the directory to zip.
        output_zip: Path to the output zip file (should end with .zip).
    """
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        drafter_src = Path("drafter")
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = Path(root) / file
                if skip_extensions and file_path.suffix in skip_extensions:
                    continue
                zipf.write(file_path, drafter_src / file_path.relative_to(source_dir))
        zipf.write(pkg_package_root() / "pyproject.toml", "pyproject.toml")
    print(f"Built zip file at {output_zip}")

def compile_site(
    config: Optional[AppBuilderConfiguration], client_server_config: Optional[ClientServerConfiguration],
    server=None,
    argv: Optional[list] = None,
    initial_state=None,
):
    """Compile a static version of the site based on the provided configuration.

    This function uses the AppBuilderConfiguration to control the compilation process,
    and it also has access to the ClientServerConfiguration to generate the logic on the built page.

    Args:
        config: AppBuilderConfiguration instance with compilation settings.
        client_server_config: ClientServerConfiguration instance with server settings.

    Returns:
        None. The compiled site is output to the specified directory.
    """
    if config is None:
        config = AppBuilderConfiguration()
    if client_server_config is None:
        client_server_config = ClientServerConfiguration()
    if argv is None:
        argv = sys.argv
        
    config = process_builder_config(config, client_server_config, argv)
    
    server = server or get_main_server()
    if config.prerender_initial_page:
        server.do_configuration(client_server_config)
        
    if config.verbose:
        print("Compiling drafter site...")
        
    user_directory = (
        Path(config.user_directory).resolve()
        if isinstance(config.user_directory, str)
        else Path.cwd()
    )
    user_path = user_directory / (
        config.main_filename if isinstance(config.main_filename, str) else "main.py"
    )
    
    output_directory = Path(config.output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    
    # Precompile if needed
    if config.prerender_initial_page:
        # TODO: Need to look into how the start_server can provide this?
        compiled_body, compiled_headers = server.precompile_server(initial_state)
    else:
        compiled_body, compiled_headers = "", ""
    
    # Write main file
    main_output_path = output_directory / config.output_filename
    
    user_code = user_path.read_text(encoding="utf-8")
    
    assets_url = determine_assets_url(config.override_asset_url)
    dest_assets_dir = output_directory / assets_url
    # TODO: Handle if assets_url is a CDN or external URL (in which case we wouldn't copy assets locally)
    
    pyodide_drafter_path = ""
    if config.pyodide_package_style == "build":
        if config.engine != "pyodide":
            raise ValueError("pyodide_package_style can only be set to 'build' if the engine is 'pyodide'.")
        # Need to actually build the package
        pyodide_drafter_path = dest_assets_dir / "drafter.zip"
        build_zip(pkg_root(), str(pyodide_drafter_path.resolve()), skip_extensions={".pyc", ".pyo", ".log", ".tmp"})
        pyodide_drafter_path = assets_url + "/drafter.zip"
        
    else:
        if config.pyodide_package_style not in (None, "cdn", "pypi"):
            raise ValueError("pyodide_package_style must be one of 'build', 'cdn', 'pypi', or None.")
        pyodide_drafter_path = "drafter" if config.pyodide_package_style == "pypi" else config.pyodide_drafter_path
    
    
    true_page = render_index_html(title=config.site_title,
                                  inline_py=True,
                                  user_code=user_code,
                                  python_url=str(config.main_filename),
                                  assets_url=assets_url,
                                  engine=config.engine,
                                  dev_ws_url=None,
                                  compiled_body=compiled_body,
                                  compiled_headers=compiled_headers,
                                  mount_drafter_locally=config.mount_drafter_locally,
                                  pyodide_package_style=config.pyodide_package_style,
                                  pyodide_drafter_path=pyodide_drafter_path or "",)
    
    main_output_path.write_text(true_page, encoding="utf-8")
    print(f"Main page written to {main_output_path}")
    
    src_assets_dir = (
        Path(config.asset_directory)
        if isinstance(config.asset_directory, str)
        else pkg_assets_dir()
    )
    # Copy over all assets to the output directory
    shutil.copytree(src_assets_dir, dest_assets_dir, dirs_exist_ok=True)
    print(f"Assets copied to {dest_assets_dir}")
    
    print(f"Site compiled successfully to {output_directory}")