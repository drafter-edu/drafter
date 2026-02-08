"""Utility functions for Drafter package asset discovery.

Provides helpers to locate package resources including assets, templates,
and scaffolding files.
"""

import shutil
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
    return pkg_root() / "assets"


def pkg_scaffold_dir() -> Path:
    """Get the scaffolding directory of the drafter package.

    Returns:
        Path to src/drafter/scaffolding/.
    """
    return pkg_root() / "scaffolding"


def copy_assets_to(target_dir: Path) -> None:
    """Copy package assets to target directory.

    Args:
        target_dir: Destination directory path.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    src = pkg_assets_dir()
    for p in src.iterdir():
        if p.is_file():
            shutil.copy2(p, target_dir / p.name)
