"""Choosing and opening a web browser for the development server.

The development server opens the site in a browser when it starts. Python's
`webbrowser` module always picks the operating system's default browser, which
on a fresh Mac is Safari. This module lets Drafter prefer Chrome or Firefox
when one is installed, and lets the user name a specific browser through the
`browser` setting.
"""

import os
import subprocess
import sys
import webbrowser
from pathlib import Path

DEFAULT_BROWSER_NAME = "default"
"""The `browser` setting value that always uses the system default browser."""

BROWSER_PREFERENCE_ORDER: tuple[str, ...] = ("chrome", "firefox")
"""Browsers tried in order when the `browser` setting is not given.

If none of these is installed, the system default browser is used.
"""

BROWSER_ALIASES: dict[str, tuple[str, ...]] = {
    "chrome": ("chrome", "google-chrome", "chromium", "chromium-browser"),
    "firefox": ("firefox",),
    "safari": ("safari",),
    "edge": ("edge", "microsoft-edge"),
}
"""Names registered with Python's `webbrowser` module for each friendly name.

The friendly name is what students write (`browser="chrome"`); the aliases
cover the different executable names that platforms register.
"""

MACOS_BROWSER_APPLICATIONS: dict[str, str] = {
    "chrome": "Google Chrome",
    "firefox": "Firefox",
    "safari": "Safari",
    "edge": "Microsoft Edge",
}
"""Application bundle names on macOS for each friendly browser name."""

WINDOWS_BROWSER_EXECUTABLES: dict[str, str] = {
    "chrome": "chrome.exe",
    "firefox": "firefox.exe",
    "edge": "msedge.exe",
}
"""Executable names on Windows, looked up through the registry's App Paths."""


def _macos_application_path(app_name: str) -> Path | None:
    """Return the bundle path of an installed macOS application, if any.

    Args:
        app_name: The application name, such as "Google Chrome".

    Returns:
        The path to the `.app` bundle, or None when it is not installed in
        the system or user Applications folder.
    """
    candidates = [
        Path("/Applications") / f"{app_name}.app",
        Path.home() / "Applications" / f"{app_name}.app",
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return None


def _windows_application_path(executable: str) -> str | None:
    """Return the full path of a Windows browser from the registry, if any.

    Windows records installed browsers under the "App Paths" registry key
    rather than on PATH, so `shutil.which` alone does not find them.

    Args:
        executable: The executable name, such as "chrome.exe".

    Returns:
        The full path to the executable, or None when it is not registered or
        the recorded file no longer exists.
    """
    # `winreg` exists only on Windows. Checking `sys.platform` (rather than
    # catching ImportError) also tells type checkers on other platforms that
    # the registry calls below are not reachable there.
    if sys.platform != "win32":
        return None
    import winreg

    subkey = rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{executable}"
    for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        try:
            with winreg.OpenKey(root, subkey) as key:
                path, _ = winreg.QueryValueEx(key, "")
        except OSError:
            continue
        if isinstance(path, str) and os.path.isfile(path):
            return path
    return None


def find_browser(name: str) -> webbrowser.BaseBrowser | None:
    """Return a controller for the named browser if it appears to be installed.

    The name is matched case-insensitively. Friendly names ("chrome",
    "firefox", "safari", "edge") are looked up in the platform's usual
    install locations first, and then any name is tried against Python's
    `webbrowser` registry, so names like "windows-default" or "xdg-open"
    also work.

    Args:
        name: A friendly browser name or a `webbrowser` registry name.
            `DEFAULT_BROWSER_NAME` ("default") always resolves to the system
            default browser.

    Returns:
        A browser controller, or None when no matching browser was found.
    """
    key = name.strip().lower()
    if not key:
        return None
    if key == DEFAULT_BROWSER_NAME:
        return webbrowser.get()
    if sys.platform == "darwin":
        app_name = MACOS_BROWSER_APPLICATIONS.get(key)
        if app_name is not None:
            if _macos_application_path(app_name) is not None:
                return webbrowser.GenericBrowser(["open", "-a", app_name])
            return None
    if sys.platform.startswith("win"):
        executable = WINDOWS_BROWSER_EXECUTABLES.get(key)
        if executable is not None:
            path = _windows_application_path(executable)
            if path is not None:
                return webbrowser.BackgroundBrowser(path)
    for alias in BROWSER_ALIASES.get(key, (name,)):
        try:
            return webbrowser.get(alias)
        except webbrowser.Error:
            continue
    return None


def choose_browser(name: str | None) -> webbrowser.BaseBrowser:
    """Pick the browser the development server should open.

    Args:
        name: The `browser` setting. When None, the browsers in
            `BROWSER_PREFERENCE_ORDER` are tried in turn and the system
            default is used when none is installed. When given, that browser
            is used; if it cannot be found, a warning is printed and the
            system default is used instead.

    Returns:
        The browser controller to open the site with.
    """
    if name is not None:
        found = find_browser(name)
        if found is not None:
            return found
        print(
            f"Warning: could not find a browser named {name!r}; "
            "opening the system default browser instead."
        )
        return webbrowser.get()
    for preferred in BROWSER_PREFERENCE_ORDER:
        found = find_browser(preferred)
        if found is not None:
            return found
    return webbrowser.get()


def open_in_browser(url: str, name: str | None) -> bool:
    """Open a URL in the chosen browser.

    Args:
        url: The address to open.
        name: The `browser` setting; see `choose_browser`.

    Returns:
        True when the browser reported that it opened the URL.
    """
    try:
        controller = choose_browser(name)
    except webbrowser.Error as error:
        print(f"Warning: could not open a web browser: {error}")
        return False
    try:
        return bool(controller.open(url))
    except (OSError, subprocess.SubprocessError) as error:
        print(f"Warning: could not open a web browser: {error}")
        return False
