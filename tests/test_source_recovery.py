"""Tests for running Drafter when the main file is not on disk.

Thonny runs an unsaved editor buffer like `python -c <code>`: `__file__` is
missing and `sys.argv` is `['-c']`. Previously Drafter treated "-c" as the
main filename and the first browser request crashed with a 500. Now:

* configure_system never accepts a placeholder argument as the path,
* serve_app_once recovers the source from Thonny's backend when possible
  and serves it inline,
* otherwise it fails up front with a StudentFacingError, and
* the index handler renders a friendly page if the file disappears later.
"""

import asyncio
import os
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from drafter.app import app_server
from drafter.app.source_recovery import (
    UNSAVED_SOURCE_FILENAME,
    get_thonny_main_source,
    is_placeholder_script_argument,
    main_file_is_available,
    recover_main_source,
)
from drafter.config.app_builder import AppBuilderConfiguration
from drafter.config.app_common import AppCommonConfiguration
from drafter.config.app_server import AppServerConfiguration
from drafter.config.bootstrap import BootstrapConfiguration
from drafter.config.client_server import ClientServerConfiguration
from drafter.config.system import SystemConfiguration
from drafter.configuration import (
    _reset_system_for_testing,
    _set_system_for_testing,
    configure_system,
)
from drafter.data.errors import StudentFacingError

FAKE_SOURCE = "from drafter import *\nstart_server()\n"


def make_system(path: str | None, **kwargs) -> SystemConfiguration:
    app_common = AppCommonConfiguration()
    app_common.prerender_initial_page = False
    system = SystemConfiguration(
        bootstrap=BootstrapConfiguration(path=path),
        client_server=ClientServerConfiguration(),
        app_server=AppServerConfiguration(),
        app_builder=AppBuilderConfiguration(),
        app_common=app_common,
    )
    for key, value in kwargs.items():
        setattr(system.app_server, key, value)
    return system


@pytest.fixture
def fake_thonny(monkeypatch):
    """Install a fake `thonny.plugins.cpython_backend.cp_back` module.

    Returns a setter so tests can control what the executor reports.
    """
    cp_back = types.ModuleType("thonny.plugins.cpython_backend.cp_back")
    backend = types.SimpleNamespace(_current_executor=None)
    cp_back.get_backend = lambda: backend  # type: ignore[attr-defined]

    thonny = types.ModuleType("thonny")
    plugins = types.ModuleType("thonny.plugins")
    cpython_backend = types.ModuleType("thonny.plugins.cpython_backend")
    cpython_backend.cp_back = cp_back  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "thonny", thonny)
    monkeypatch.setitem(sys.modules, "thonny.plugins", plugins)
    monkeypatch.setitem(sys.modules, "thonny.plugins.cpython_backend", cpython_backend)
    monkeypatch.setitem(sys.modules, "thonny.plugins.cpython_backend.cp_back", cp_back)

    def set_source(source):
        backend._current_executor = types.SimpleNamespace(
            _original_cmd=types.SimpleNamespace(source=source)
        )

    return set_source


@pytest.fixture
def no_thonny(monkeypatch):
    """Make sure `import thonny...` fails."""
    monkeypatch.setitem(sys.modules, "thonny", None)


@pytest.fixture(autouse=True)
def reset_system():
    yield
    _reset_system_for_testing()


# ---------------------------------------------------------------------------
# source_recovery helpers
# ---------------------------------------------------------------------------


class TestPlaceholderDetection:
    @pytest.mark.parametrize("arg", ["-c", "-m", "-", "", "  ", None])
    def test_placeholders(self, arg):
        assert is_placeholder_script_argument(arg) is True

    @pytest.mark.parametrize("arg", ["site.py", "C:\\work\\site.py", "./-c.py"])
    def test_real_paths(self, arg):
        assert is_placeholder_script_argument(arg) is False

    def test_main_file_is_available(self, tmp_path):
        existing = tmp_path / "site.py"
        existing.write_text("x = 1", encoding="utf-8")
        assert main_file_is_available(str(existing)) is True
        assert main_file_is_available(str(tmp_path / "missing.py")) is False
        assert main_file_is_available("-c") is False
        assert main_file_is_available(None) is False


class TestThonnySource:
    def test_no_thonny_installed(self, no_thonny):
        assert get_thonny_main_source() is None

    def test_thonny_idle(self, fake_thonny):
        # Backend present, but nothing currently executing.
        assert get_thonny_main_source() is None

    def test_thonny_running_unsaved_buffer(self, fake_thonny):
        fake_thonny(FAKE_SOURCE)
        assert get_thonny_main_source() == FAKE_SOURCE

    def test_thonny_non_string_source_ignored(self, fake_thonny):
        fake_thonny(b"bytes")
        assert get_thonny_main_source() is None

    def test_thonny_internals_changed(self, fake_thonny, monkeypatch):
        # Simulate Thonny renaming the private attribute: must fail soft.
        cp_back = sys.modules["thonny.plugins.cpython_backend.cp_back"]
        monkeypatch.setattr(cp_back, "get_backend", lambda: types.SimpleNamespace())
        assert get_thonny_main_source() is None

    def test_recover_prefers_file_on_disk(self, fake_thonny, tmp_path):
        fake_thonny(FAKE_SOURCE)
        existing = tmp_path / "site.py"
        existing.write_text("x = 1", encoding="utf-8")
        # A readable file wins; recovery is only for when it is unavailable.
        assert recover_main_source(str(existing)) is None

    def test_recover_when_file_unavailable(self, fake_thonny):
        fake_thonny(FAKE_SOURCE)
        assert recover_main_source("-c") == FAKE_SOURCE
        assert recover_main_source(None) == FAKE_SOURCE


# ---------------------------------------------------------------------------
# configure_system: never accept "-c" as the path
# ---------------------------------------------------------------------------


class TestConfigureSystemPlaceholderArgv:
    def test_dash_c_is_not_a_path(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["-c"])
        monkeypatch.delenv("DRAFTER_ENTRY", raising=False)
        system, modified = configure_system(from_cli=False)
        assert system.bootstrap.path is None
        assert "path" not in modified.get("bootstrap", {})
        assert "No entry path" in capsys.readouterr().out

    def test_real_script_still_detected(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["my_site.py"])
        monkeypatch.delenv("DRAFTER_ENTRY", raising=False)
        system, _ = configure_system(from_cli=False)
        assert system.bootstrap.path == "my_site.py"


# ---------------------------------------------------------------------------
# serve_app_once: resolve the source before anything starts
# ---------------------------------------------------------------------------


class TestResolveMainSource:
    def test_existing_file_uses_disk(self, tmp_path, fake_thonny):
        fake_thonny(FAKE_SOURCE)
        existing = tmp_path / "site.py"
        existing.write_text("x = 1", encoding="utf-8")
        system = make_system(str(existing))
        assert app_server._resolve_main_source(system) is None
        assert system.bootstrap.path == str(existing)

    def test_missing_file_without_thonny_raises_friendly(self, no_thonny, tmp_path):
        system = make_system(str(tmp_path / "nope.py"))
        with pytest.raises(StudentFacingError) as excinfo:
            app_server._resolve_main_source(system)
        error = excinfo.value
        assert "nope.py" in str(error)
        assert "save your file" in str(error).lower()
        assert error.friendly_message
        assert any("Save your file" in step for step in error.friendly_steps)

    def test_no_path_without_thonny_raises_friendly(self, no_thonny):
        system = make_system(None)
        with pytest.raises(StudentFacingError) as excinfo:
            app_server._resolve_main_source(system)
        assert "no path" in str(excinfo.value)

    def test_unsaved_thonny_buffer_is_recovered(
        self, fake_thonny, monkeypatch, tmp_path, capsys
    ):
        fake_thonny(FAKE_SOURCE)
        monkeypatch.chdir(tmp_path)
        system = make_system(None)
        assert app_server._resolve_main_source(system) == FAKE_SOURCE
        # A synthetic path is installed so relative paths/error log work.
        assert system.bootstrap.path == os.path.join(
            os.getcwd(), UNSAVED_SOURCE_FILENAME
        )
        assert system.bootstrap.get_user_directory() == str(tmp_path.resolve())
        assert "has not been saved" in capsys.readouterr().out

    def test_serve_app_once_fails_before_starting_server(self, no_thonny, monkeypatch):
        """No uvicorn, no browser, no prerender when the file is missing."""
        started = MagicMock()
        monkeypatch.setattr(app_server, "make_app", started)
        monkeypatch.setattr(app_server.webbrowser, "open", started)
        system = make_system("-c")
        server = MagicMock()
        with pytest.raises(StudentFacingError):
            app_server.serve_app_once(system, server, None)
        started.assert_not_called()
        server.do_configuration.assert_not_called()


# ---------------------------------------------------------------------------
# make_app / index: serving recovered source and handling vanished files
# ---------------------------------------------------------------------------


class FakeClient:
    """Drive the index handler directly (no httpx/TestClient needed)."""

    def __init__(self, app):
        self.app = app

    def get(self, path):
        assert path == "/"
        request = types.SimpleNamespace(app=self.app)
        response = asyncio.run(app_server.index(request))
        response.text = response.body.decode("utf-8")
        return response


def make_client(system: SystemConfiguration, user_source=None) -> FakeClient:
    _set_system_for_testing(system)
    app = app_server.make_app(system, MagicMock(), None, user_source=user_source)
    return FakeClient(app)


class TestIndexWithRecoveredSource:
    def test_recovered_source_is_inlined(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        system = make_system(str(tmp_path / UNSAVED_SOURCE_FILENAME), inline_py=False)
        client = make_client(system, user_source=FAKE_SOURCE)
        response = client.get("/")
        assert response.status_code == 200
        # Inlined even though inline_py is False: there is no file to fetch.
        assert FAKE_SOURCE in response.text

    def test_recovered_source_does_not_watch_missing_file(self, tmp_path):
        system = make_system(str(tmp_path / UNSAVED_SOURCE_FILENAME))
        _set_system_for_testing(system)
        app = app_server.make_app(system, MagicMock(), None, user_source=FAKE_SOURCE)
        watched = [wp.directory for wp in app.state.watch_paths]
        assert Path(tmp_path / UNSAVED_SOURCE_FILENAME) not in watched
        # Adjacent-file changes can only do a full reload (nothing to re-read).
        adjacent = [
            wp for wp in app.state.watch_paths if wp.directory == tmp_path.resolve()
        ]
        assert adjacent and all(wp.full_reload for wp in adjacent)

    def test_file_on_disk_is_watched_normally(self, tmp_path):
        existing = tmp_path / "site.py"
        existing.write_text(FAKE_SOURCE, encoding="utf-8")
        system = make_system(str(existing))
        _set_system_for_testing(system)
        app = app_server.make_app(system, MagicMock(), None)
        assert app.state.user_source is None
        assert any(
            wp.directory == existing.resolve() and not wp.full_reload
            for wp in app.state.watch_paths
        )


class TestIndexWhenFileVanishes:
    def test_friendly_page_instead_of_traceback(self, tmp_path):
        existing = tmp_path / "site.py"
        existing.write_text(FAKE_SOURCE, encoding="utf-8")
        system = make_system(str(existing))
        client = make_client(system)
        assert client.get("/").status_code == 200

        existing.unlink()  # student renamed/deleted it while running
        response = client.get("/")
        assert response.status_code == 500
        assert "could not find your file" in response.text
        assert "site.py" in response.text
        assert "Traceback" not in response.text
