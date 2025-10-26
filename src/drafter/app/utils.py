import shutil
from importlib.resources import files
from pathlib import Path


def pkg_root() -> Path:
    return Path(__file__).resolve().parent.parent


def pkg_assets_dir() -> Path:
    return pkg_root() / "assets"


def pkg_scaffold_dir() -> Path:
    return pkg_root() / "scaffolding"


def copy_assets_to(target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    src = pkg_assets_dir()
    for p in src.iterdir():
        if p.is_file():
            shutil.copy2(p, target_dir / p.name)
