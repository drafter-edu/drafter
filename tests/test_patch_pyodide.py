"""Tests for the Pyodide remote-import finder (drafter.files.patch_pyodide).

In the browser, a student's own modules are fetched from the server over
HTTP when imported. The finder used to try only `name.py`, so a project
laid out as a package (`my_project/__init__.py`, e.g. next to a
`pyproject.toml`) ran fine in regular Python but crashed in the browser
with `ModuleNotFoundError: No module named 'my_project'`.

The module is imported with `js` and `pyodide.http` stubbed, and the
finder it installs at import time is removed again so it cannot leak into
the rest of the test process.
"""

import importlib
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest


class FakeServer:
    """Stands in for `pyxhr`: serves a dict of URL -> source, 404 otherwise."""

    def __init__(self, files: dict[str, str], broken: tuple[str, ...] = ()) -> None:
        self.files = files
        self.broken = broken
        self.requested: list[str] = []

    def get(self, url: str) -> SimpleNamespace:
        self.requested.append(url)
        if url in self.broken:
            raise OSError("network error")
        if url in self.files:
            return SimpleNamespace(status_code=200, text=self.files[url])
        return SimpleNamespace(status_code=404, text="Not Found")


@pytest.fixture(scope="module")
def patch_pyodide():
    """Import patch_pyodide with browser modules stubbed, then unhook it."""
    pyodide_http = ModuleType("pyodide.http")
    setattr(pyodide_http, "pyxhr", FakeServer({}))
    pyodide = ModuleType("pyodide")
    setattr(pyodide, "http", pyodide_http)
    stubs = {"pyodide": pyodide, "pyodide.http": pyodide_http}
    if "js" not in sys.modules:
        stubs["js"] = MagicMock()
    saved = {name: sys.modules.get(name) for name in stubs}
    sys.modules.update(stubs)
    sys.modules.pop("drafter.files.patch_pyodide", None)
    try:
        module = importlib.import_module("drafter.files.patch_pyodide")
    finally:
        sys.meta_path[:] = [
            finder
            for finder in sys.meta_path
            if type(finder).__name__ != "RemoteFinder"
        ]
        for name, original in saved.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original
    yield module
    sys.modules.pop("drafter.files.patch_pyodide", None)


@pytest.fixture
def remote_import(patch_pyodide, monkeypatch):
    """Install a RemoteFinder backed by a FakeServer for one test."""
    finder = patch_pyodide.RemoteFinder()
    sys.meta_path.append(finder)
    imported_before = set(sys.modules)

    def install(files: dict[str, str], broken: tuple[str, ...] = ()) -> FakeServer:
        server = FakeServer(files, broken)
        monkeypatch.setattr(patch_pyodide, "pyxhr", server)
        return server

    yield install
    sys.meta_path.remove(finder)
    for name in set(sys.modules) - imported_before:
        if name.startswith("remote_test_"):
            del sys.modules[name]
    patch_pyodide.EXTERNAL_IMPORTS.clear()


def test_imports_a_plain_module(remote_import):
    remote_import({"remote_test_helpers.py": "GREETING = 'hi'"})

    module = importlib.import_module("remote_test_helpers")

    assert module.GREETING == "hi"
    assert not hasattr(module, "__path__")


def test_imports_a_package_from_its_init_file(remote_import):
    server = remote_import({"remote_test_project/__init__.py": "NAME = 'pkg'"})

    module = importlib.import_module("remote_test_project")

    assert module.NAME == "pkg"
    assert module.__package__ == "remote_test_project"
    assert hasattr(module, "__path__")
    # The module file is tried first; the package folder is the fallback.
    assert server.requested == [
        "remote_test_project.py",
        "remote_test_project/__init__.py",
    ]


def test_package_relative_imports_and_submodules_resolve(remote_import):
    remote_import(
        {
            "remote_test_app/__init__.py": "from .helpers import GREETING",
            "remote_test_app/helpers.py": "GREETING = 'Hello from package'",
        }
    )

    package = importlib.import_module("remote_test_app")
    helpers = importlib.import_module("remote_test_app.helpers")

    assert package.GREETING == "Hello from package"
    assert helpers.GREETING == "Hello from package"


def test_module_file_wins_over_package_folder(remote_import):
    server = remote_import(
        {
            "remote_test_both.py": "SOURCE = 'module'",
            "remote_test_both/__init__.py": "SOURCE = 'package'",
        }
    )

    module = importlib.import_module("remote_test_both")

    assert module.SOURCE == "module"
    assert server.requested == ["remote_test_both.py"]


def test_missing_module_still_raises_module_not_found(remote_import):
    remote_import({})

    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("remote_test_missing")


def test_failed_request_falls_through_to_package(remote_import):
    remote_import(
        {"remote_test_flaky/__init__.py": "OK = True"},
        broken=("remote_test_flaky.py",),
    )

    assert importlib.import_module("remote_test_flaky").OK is True


def test_package_imports_are_expired_like_modules(remote_import, patch_pyodide):
    remote_import({"remote_test_reload/__init__.py": "VALUE = 1"})
    importlib.import_module("remote_test_reload")
    assert "remote_test_reload" in patch_pyodide.EXTERNAL_IMPORTS

    patch_pyodide.expire_remote_imports()

    assert "remote_test_reload" not in sys.modules
    assert patch_pyodide.EXTERNAL_IMPORTS == set()
