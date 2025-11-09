"""
This module is not actually built in the Skulpt deployment.
Instead, the js/src/bridge/client.ts file is compiled and included
instead.

This module is provided here so that type checkers and IDEs can
understand its existence and provide type information.
"""

from drafter.data.response import Response
from typing import Callable


def update_site(response: Response, callback: Callable) -> bool:  # type: ignore
    pass


def console_log(event) -> None:  # type: ignore
    pass


def setup_navigation(handle_visit: Callable) -> None:  # type: ignore
    pass


def set_site_title(title: str) -> None:  # type: ignore
    pass


def register_hotkey(keyCombo: str, callback: Callable[[], None]) -> None:  # type: ignore
    """
    Registers a hotkey combination to trigger a callback function when pressed.

    :param keyCombo: The key combination string (e.g., "Ctrl+K").
    :param callback: The function to call when the hotkey is pressed.
    """
    pass
