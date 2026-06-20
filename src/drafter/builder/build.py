from glob import glob
import sys
import os
from typing import Optional
import shutil
import zipfile
from pathlib import Path
from drafter.client_server.client_server import ClientServer
from drafter.config.app_builder import AppBuilderConfiguration
from drafter.config.client_server import ClientServerConfiguration
from drafter.client_server.commands import get_main_server
from drafter.config.system import SystemConfiguration
from drafter.config.urls import determine_assets_url, INTERNAL_FILES
from drafter.configuration import get_system_config_modifications
from drafter.scaffolding.templating import render_index_html
from drafter.scaffolding.utils import pkg_assets_dir, pkg_root, pkg_package_root
from drafter.version import CURRENT_DRAFTER_VERSION


def build_zip(
    source_dir: Path, output_zip: str, skip_extensions: Optional[set[str]] = None
):
    """Build a zip file from the source directory.

    Args:
        source_dir: Path to the directory to zip.
        output_zip: Path to the output zip file (should end with .zip).
    """
    os.makedirs(os.path.dirname(output_zip), exist_ok=True)
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        drafter_src = Path("drafter")
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = Path(root) / file
                if skip_extensions and file_path.suffix in skip_extensions:
                    continue
                zipf.write(file_path, drafter_src / file_path.relative_to(source_dir))
        zipf.write(pkg_package_root() / "pyproject.toml", "pyproject.toml")
    print(f"Built zip file at {output_zip}")


def iter_additional_paths(pattern: str, base_dir: Path):
    path = Path(pattern)

    # Resolve relative globs relative to the app/user file directory
    search_pattern = str(path if path.is_absolute() else base_dir / path)

    matches = [Path(p) for p in glob(search_pattern, recursive=True)]

    if not matches:
        print(f"Warning: additional_path matched nothing: {pattern}")

    return matches


def compile_site(
    system: SystemConfiguration,
    server: ClientServer,
    initial_state,
):
    """Compile a static version of the site based on the provided configuration.

    This function uses the AppBuilderConfiguration to control the compilation process,
    and it also has access to the ClientServerConfiguration to generate the logic on the built page.

    Args:
        system: The SystemConfiguration instance containing all configuration settings.
        server: The ClientServer instance to use for precompilation.
        initial_state: The initial state to pass to the server for precompilation.

    Returns:
        None. The compiled site is output to the specified directory.
    """

    server = server or get_main_server()
    if system.app_common.prerender_initial_page:
        possible_error = server.do_configuration()
        if possible_error:
            print("Error during prerendering configuration:", possible_error)
            return

    if system.bootstrap.verbose:
        print("Compiling drafter site...")

    if system.bootstrap.path is None:
        print(
            "Error: Cannot compile site because the path to the main user file is not specified."
        )
        return

    user_path = Path(system.bootstrap.path)

    output_directory = Path(system.app_builder.output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)

    # Precompile if needed
    if system.app_common.prerender_initial_page:
        # TODO: Need to look into how the start_server can provide this?
        compiled_body, compiled_headers = server.precompile_server(initial_state)
    else:
        compiled_body, compiled_headers = "", ""

    # Write main file
    main_output_path = output_directory / system.app_builder.output_filename

    user_code = user_path.read_text(encoding="utf-8")

    assets_url = determine_assets_url(system.app_common.override_asset_url)
    dest_assets_dir = output_directory / assets_url
    # TODO: Handle if assets_url is a CDN or external URL (in which case we wouldn't copy assets locally)

    pyodide_drafter_path = ""
    if system.app_builder.pyodide_package_style == "build":
        # if system.app_common.engine != "pyodide":
        #     raise ValueError("pyodide_package_style can only be set to 'build' if the engine is 'pyodide'.")
        # Need to actually build the package
        destination_name = INTERNAL_FILES["DRAFTER_PYODIDE_FILE"]
        pyodide_drafter_path = dest_assets_dir / destination_name
        build_zip(
            pkg_root(),
            str(pyodide_drafter_path.resolve()),
            skip_extensions={".pyc", ".pyo", ".log", ".tmp"},
        )
        pyodide_drafter_path = f"{assets_url}/{destination_name}"

    else:
        if system.app_builder.pyodide_package_style not in (None, "cdn", "pypi"):
            raise ValueError(
                "pyodide_package_style must be one of 'build', 'cdn', 'pypi', or None."
            )
        pyodide_drafter_path = (
            (
                system.app_common.pyodide_drafter_path
                or f"drafter=={CURRENT_DRAFTER_VERSION}"
            )
            if system.app_builder.pyodide_package_style == "pypi"
            else system.app_common.pyodide_drafter_path
        )

    true_page = render_index_html(
        system=system,
        modified_system=get_system_config_modifications(),
        inline_py=True,
        user_code=user_code,
        python_url=str(system.bootstrap.get_main_filename()),
        assets_url=assets_url,
        dev_ws_url=None,
        compiled_body=compiled_body,
        compiled_headers=compiled_headers,
        pyodide_drafter_path=pyodide_drafter_path or "",
    )

    main_output_path.write_text(true_page, encoding="utf-8")
    if system.bootstrap.verbose:
        print(f"Main page written to {main_output_path}")

    # Copy over all assets to the output directory
    src_assets_dir = (
        Path(system.app_common.asset_directory)
        if isinstance(system.app_common.asset_directory, str)
        else pkg_assets_dir()
    )
    shutil.copytree(src_assets_dir, dest_assets_dir, dirs_exist_ok=True)

    # Copy over additional paths
    base_dir = user_path.parent
    for additional_pattern in system.app_builder.additional_paths:
        for additional_path in iter_additional_paths(additional_pattern, base_dir):
            if not additional_path.exists():
                continue

            try:
                relative_path = additional_path.relative_to(base_dir)
            except ValueError:
                # If it cannot be made relative, just use the name
                relative_path = Path(additional_path.name)

            dest_path = output_directory / relative_path

            print(f"- Copying additional path {additional_path} to {dest_path}")
            if additional_path.is_dir():
                shutil.copytree(additional_path, dest_path, dirs_exist_ok=True)
            else:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(additional_path, dest_path)

    if system.bootstrap.verbose:
        print(f"Assets copied to {dest_assets_dir}")

    if system.bootstrap.verbose:
        print(f"Site compiled successfully to {output_directory}")
