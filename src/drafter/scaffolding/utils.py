"""Utility functions for Drafter package asset discovery.

Provides helpers to locate package resources including assets, templates,
and scaffolding files.
"""

import os
from pathlib import Path


def pkg_root() -> Path:
    """Get the root directory of the drafter package.

    Returns:
        Path to src/drafter/.
    """
    # src/drafter/app/utils.py -> src/drafter/
    return Path(__file__).resolve().parent.parent


def pkg_package_root() -> Path:
    """Get the true root directory of the drafter package (package root).

    This is the directory that should contain the pyproject.toml files.

    Returns:
        Path to the package root (the directory containing the drafter package).
    """
    return Path(__file__).resolve().parent.parent.parent.parent


def pkg_assets_dir() -> Path:
    """Get the assets directory of the drafter package.

    Returns:
        Path to src/drafter/assets/.
    """
    chosen_path = pkg_root() / "assets"
    if os.path.exists(chosen_path):
        return chosen_path
    alternate_path = pkg_root().parent.parent / "js" / "dist"
    if os.path.exists(alternate_path):
        return alternate_path
    raise FileNotFoundError(
        "Assets directory not found in either src/drafter/assets/ or js/dist/"
    )


def pkg_scaffold_dir() -> Path:
    """Get the scaffolding directory of the drafter package.

    Returns:
        Path to src/drafter/scaffolding/.
    """
    return pkg_root() / "scaffolding"
