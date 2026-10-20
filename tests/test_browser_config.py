"""Tests for the app_server `browser` configuration setting.

The setting names the browser the development server opens the site in.
When it is not given, Drafter prefers Chrome, then Firefox, then the system
default browser. These tests cover the configuration pipeline (defaults,
environment variables, CLI parsing, start_server keyword) and the browser
selection logic, with the real `webbrowser` registry and platform lookups
patched out so no browser is ever launched.
"""

import argparse
import webbrowser

import pytest

from drafter.app import browser_launch
from drafter.app.browser_launch import (
    BROWSER_PREFERENCE_ORDER,
    choose_browser,
    find_browser,
    open_in_browser,
)
from drafter.config.app_server import AppServerConfiguration


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    AppServerConfiguration.extend_parser(parser)
    return parser


class FakeBrowser(webbrowser.BaseBrowser):
    """A controller that records the URL it was asked to open."""

    def __init__(self, name: str, succeeds: bool = True) -> None:
        super().__init__(name)
        self.succeeds = succeeds
        self.opened: list[str] = []

    def open(self, url, new=0, autoraise=True):
        self.opened.append(url)
        return self.succeeds


@pytest.fixture
def registry(monkeypatch):
    """Replace the platform lookups with an in-memory browser registry.

    Returns the dictionary; tests add entries keyed by `webbrowser` name.
    The "default" entry stands in for the system default browser.
    """
    browsers: dict[str, FakeBrowser] = {"default": FakeBrowser("default")}

    def fake_get(using=None):
        if using is None:
            return browsers["default"]
        if using in browsers:
            return browsers[using]
        raise webbrowser.Error(f"could not locate runnable browser {using}")

    monkeypatch.setattr(browser_launch.webbrowser, "get", fake_get)
    # Pretend to be a platform without special install-location lookups so
    # the tests exercise the registry path on every operating system.
    monkeypatch.setattr(browser_launch.sys, "platform", "linux")
    return browsers


class TestBrowserDefaults:
    def test_default_is_none(self):
        assert AppServerConfiguration().browser is None

    def test_preference_order_is_chrome_then_firefox(self):
        assert BROWSER_PREFERENCE_ORDER == ("chrome", "firefox")


class TestBrowserEnvVars:
    def test_env_var_parsed(self):
        result = AppServerConfiguration.parse_env_variables(
            {"DRAFTER_BROWSER": "firefox"}
        )
        assert result["browser"] == "firefox"

    def test_env_var_absent(self):
        assert "browser" not in AppServerConfiguration.parse_env_variables({})


class TestBrowserCli:
    def test_browser_flag(self):
        parser = make_parser()
        parsed, _ = parser.parse_known_args(["--browser", "chrome"])
        result = AppServerConfiguration.parse_args(vars(parsed))
        assert result["browser"] == "chrome"

    def test_browser_not_given(self):
        parser = make_parser()
        parsed, _ = parser.parse_known_args([])
        assert "browser" not in AppServerConfiguration.parse_args(vars(parsed))

    def test_merges_into_configuration(self):
        parser = make_parser()
        parsed, _ = parser.parse_known_args(["--browser", "safari"])
        config = AppServerConfiguration()
        config.merge_in_args(AppServerConfiguration.parse_args(vars(parsed)), False)
        assert config.browser == "safari"


class TestStartServerKeyword:
    def test_browser_keyword_reaches_configuration(self, monkeypatch):
        from drafter import launch
        from drafter.app import app_server
        from drafter.configuration import get_system_configuration

        captured = {}

        def fake_serve(system, server, initial_state):
            captured["browser"] = system.app_server.browser

        monkeypatch.setattr(launch, "is_web", lambda: False)
        monkeypatch.setattr(app_server, "serve_app_once", fake_serve)
        system = get_system_configuration()
        monkeypatch.setattr(launch, "get_system_configuration", lambda: system)
        launch.start_server(browser="firefox", open_browser=False, argv=[])
        assert captured["browser"] == "firefox"


class TestFindBrowser:
    def test_registered_name(self, registry):
        registry["firefox"] = FakeBrowser("firefox")
        assert find_browser("firefox") is registry["firefox"]

    def test_name_is_case_insensitive(self, registry):
        registry["firefox"] = FakeBrowser("firefox")
        assert find_browser("Firefox") is registry["firefox"]

    def test_chrome_aliases(self, registry):
        registry["google-chrome"] = FakeBrowser("google-chrome")
        assert find_browser("chrome") is registry["google-chrome"]

    def test_default_name_is_system_default(self, registry):
        assert find_browser("default") is registry["default"]

    def test_unknown_name_is_none(self, registry):
        assert find_browser("netscape") is None

    def test_empty_name_is_none(self, registry):
        assert find_browser("  ") is None


class TestChooseBrowser:
    def test_unset_prefers_chrome(self, registry):
        registry["chrome"] = FakeBrowser("chrome")
        registry["firefox"] = FakeBrowser("firefox")
        assert choose_browser(None) is registry["chrome"]

    def test_unset_falls_back_to_firefox(self, registry):
        registry["firefox"] = FakeBrowser("firefox")
        assert choose_browser(None) is registry["firefox"]

    def test_unset_falls_back_to_system_default(self, registry):
        assert choose_browser(None) is registry["default"]

    def test_named_browser_wins_over_preference(self, registry):
        registry["chrome"] = FakeBrowser("chrome")
        registry["firefox"] = FakeBrowser("firefox")
        assert choose_browser("firefox") is registry["firefox"]

    def test_default_name_skips_preference(self, registry):
        registry["chrome"] = FakeBrowser("chrome")
        assert choose_browser("default") is registry["default"]

    def test_missing_named_browser_warns_and_uses_default(self, registry, capsys):
        registry["chrome"] = FakeBrowser("chrome")
        assert choose_browser("opera") is registry["default"]
        assert "could not find a browser named 'opera'" in capsys.readouterr().out


class TestOpenInBrowser:
    def test_opens_url_in_chosen_browser(self, registry):
        registry["chrome"] = FakeBrowser("chrome")
        assert open_in_browser("http://localhost:8000/", None) is True
        assert registry["chrome"].opened == ["http://localhost:8000/"]
        assert registry["default"].opened == []

    def test_reports_failure_without_raising(self, registry):
        registry["default"] = FakeBrowser("default", succeeds=False)
        assert open_in_browser("http://localhost:8000/", None) is False

    def test_no_browser_available(self, monkeypatch, capsys):
        def no_browsers(using=None):
            raise webbrowser.Error("could not locate runnable browser")

        monkeypatch.setattr(browser_launch.webbrowser, "get", no_browsers)
        monkeypatch.setattr(browser_launch.sys, "platform", "linux")
        assert open_in_browser("http://localhost:8000/", None) is False
        assert "could not open a web browser" in capsys.readouterr().out


class TestPlatformLookups:
    def test_macos_uses_open_when_app_installed(self, monkeypatch):
        monkeypatch.setattr(browser_launch.sys, "platform", "darwin")
        monkeypatch.setattr(
            browser_launch, "_macos_application_path", lambda app: "/Applications"
        )
        controller = find_browser("chrome")
        assert isinstance(controller, webbrowser.GenericBrowser)
        assert controller.name == "open"
        assert controller.args == ["-a", "Google Chrome"]

    def test_macos_missing_app_is_none(self, monkeypatch):
        monkeypatch.setattr(browser_launch.sys, "platform", "darwin")
        monkeypatch.setattr(browser_launch, "_macos_application_path", lambda app: None)
        # The webbrowser registry on macOS would claim Chrome exists even
        # when it is not installed, so it must not be consulted.
        monkeypatch.setattr(
            browser_launch.webbrowser, "get", lambda using=None: FakeBrowser("osa")
        )
        assert find_browser("chrome") is None

    def test_windows_uses_registry_path(self, monkeypatch):
        monkeypatch.setattr(browser_launch.sys, "platform", "win32")
        monkeypatch.setattr(
            browser_launch,
            "_windows_application_path",
            lambda exe: r"C:\Browsers\chrome.exe" if exe == "chrome.exe" else None,
        )
        controller = find_browser("chrome")
        assert isinstance(controller, webbrowser.BackgroundBrowser)
        assert controller.name == r"C:\Browsers\chrome.exe"
