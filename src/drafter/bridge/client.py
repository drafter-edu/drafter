"""
This module is not actually built in the Skulpt deployment.
Instead, the js/src/bridge/client.ts file is compiled and included
instead.

This module is provided here so that type checkers and IDEs can
understand its existence and provide type information.
"""

from drafter.data.response import Response
from drafter.data.request import Request
from drafter.site.site import DRAFTER_TAG_IDS, DRAFTER_TAG_CLASSES
from drafter.monitor.telemetry import TelemetryEvent, TelemetryCorrelation
from drafter.monitor.bus import get_main_event_bus
from typing import Callable, Optional
from dataclasses import dataclass
import js

@dataclass
class NavEvent:
    kind: str
    url: str
    data: js.FormData
    submitter: Optional[str] = None
    
def replaceHTML(tag, html: str):
    scroll_top = js.scrollY
    scroll_left = js.scrollX
    r = js.document.createRange()
    r.selectNode(tag)
    fragment = r.createContextualFragment(html)
    tag.replaceWith(fragment)
    js.window.scrollTo(scroll_left, scroll_top)


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


def setup_debug_menu(client_bridge) -> None:  # type: ignore
    """
    Sets up the debug menu in the client bridge.

    :param client_bridge: The ClientBridge instance to set up the debug menu for.
    """
    pass


def handle_event(event_json: dict) -> None:  # type: ignore
    """
    Handles a telemetry event in the client bridge.

    :param event_json: The telemetry event data as a JSON-serializable dictionary.
    """
    pass
