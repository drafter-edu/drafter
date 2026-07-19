"""
ClientBridge: the unified bridge between the Python application and the browser DOM.

Handles site setup, DOM updates, navigation, event handling, request/response
management, channel content, redirect detection, history, hotkeys, and telemetry.
Runtime-specific differences (Skulpt vs Pyodide) are delegated to a RuntimeAdapter.
"""

import json
import time
import html

from drafter.bridge.events import EventManager
from drafter.bridge.history import BrowserHistory
from drafter.bridge.navigation import NavigationController
from drafter.bridge.site_renderer import SiteRenderer
import js
from dataclasses import dataclass, field
from drafter.bridge.dom import (
    add_js,
    add_style,
    add_link,
    add_link_to_shadow,
    add_style_to_shadow,
    add_header,
    remove_page_content,
    remove_existing_theme,
    replace_html,
    get_attribute_recursively,
    swap_debug_mode,
    update_subtle_debug_entry,
)
from drafter.bridge.log import debug_log, console_log
from drafter.bridge.persistence import evict_key
from drafter.bridge.error_handling import (
    raise_bridge_system_error,
    report_bridge_error,
)
from drafter.bridge.runtime import RuntimeAdapter, create_runtime
from drafter.config.client_server import ClientServerConfiguration

from drafter.components.page_content import Component
from drafter.data.channel import DEFAULT_CHANNEL_AFTER, DEFAULT_CHANNEL_BEFORE, Channel
from drafter.data.response import Response
from drafter.data.request import Request
from drafter.data.details.config import UpdatedConfigurationEvent
from drafter.data.telemetry import TelemetryRecord
from drafter.site.initial_site_data import InitialSiteData
from drafter.site.site import (
    DRAFTER_TAG_IDS,
    DRAFTER_TAG_CLASSES,
    SITE_HTML_SHADOW_DOM_TEMPLATE,
)
from typing import Callable, Optional, Any


@dataclass
class ClientBridge:
    site_renderer: SiteRenderer
    navigator: NavigationController
    configuration: ClientServerConfiguration = field(init=False)
    debug_panel: Optional[Any] = None
    runtime: RuntimeAdapter = field(default_factory=create_runtime)
    site_title: str = "Default Title"

    def __init__(self, configuration: ClientServerConfiguration):
        self.runtime = create_runtime()
        self.configuration = configuration
        self.site_renderer = SiteRenderer(
            self.runtime, configuration.root_element_id, configuration.root_element_id
        )
        self.navigator = NavigationController(self.runtime)
        self.events = EventManager(self.runtime)
        self.debug_panel = None

    def setup_site(self, initial_site_data: InitialSiteData) -> None:
        self.set_site_title(initial_site_data.site_title)
        self.site_renderer.setup(initial_site_data)
        update_subtle_debug_entry(
            self.site_renderer.get_scope(),
            self.configuration.in_debug_mode,
            self.configuration.enable_subtle_debug_entry,
        )
        # Scope this instance's event lookups (BODY/FORM) to the same node the
        # renderer rendered into (its shadow root, when shadow DOM is on), so
        # concurrent instances never resolve each other's elements.
        self.events.set_scope(self.site_renderer.scope)
        self._setup_debug_menu()

    def setup_events(
        self,
        handle_visit: Callable[[Request], Response],
        handle_toggle_frame: Callable,
        handle_debug_mode: Callable,
    ) -> None:
        self.navigator.set_navigation_func(handle_visit)
        self.events.setup_events(
            {
                "drafter-toggle-frame": lambda event: handle_toggle_frame(),
                "drafter-toggle-debug-mode": lambda event: handle_debug_mode(),
                "drafter-evict-persistent": lambda event: self.evict_persistent(
                    event
                ),
                "drafter-navigate": lambda event: self.navigator.goto(event.detail),
                "popstate": self.navigator.handle_popstate,
            },
            {
                "Q": handle_debug_mode,
            },
        )

    def start(self):
        """
        Load the initial request.
        """
        self.navigator.do_initial_request()

    def evict_persistent(self, event) -> None:
        """Evict a persisted component by key (from the debug panel UI)."""
        key = getattr(event, "detail", None)
        if not key:
            return
        parking_area = self.site_renderer.get_parking_area()
        if parking_area is not None:
            evict_key(parking_area, str(key))

    ### Debug Panel

    def _setup_debug_menu(self):
        debug_log("client.setup_debug_menu")
        try:
            self.debug_panel = self.runtime.create_debug_panel(
                DRAFTER_TAG_IDS["DEBUG"], self, self.site_renderer.scope
            )
        except Exception as e:
            raise_bridge_system_error(
                "client.setup_debug_menu_failed",
                "Failed to set up debug panel",
                "bridge.client_bridge._setup_debug_menu",
                f"Container id: {DRAFTER_TAG_IDS['DEBUG']}",
                exception=e,
                phase="setup",
            )

    def _handle_debug_events(self, event: dict) -> bool:
        try:
            js_event = self.runtime.convert_to_js(event)
        except Exception as e:
            report_bridge_error(
                "client.convert_event_to_js",
                f"Error converting event to JS: {repr(e)}",
                "bridge.client_bridge.handle_server_event",
                f"Exception: {repr(e)}",
                exception=e,
                phase="event_dispatch",
            )
            return False
        if self.debug_panel:
            try:
                handled = self.debug_panel.handleEvent(js_event)
                return handled
            except Exception as e:
                raise_bridge_system_error(
                    "client.handle_debug_event_failed",
                    "Failed to handle debug panel event",
                    "bridge.client_bridge._handle_debug_events",
                    f"Event: {repr(event)}",
                    exception=e,
                    phase="event_dispatch",
                )
        else:
            raise_bridge_system_error(
                "client.no_debug_panel",
                "No debug panel is available to handle telemetry event",
                "bridge.client_bridge._handle_debug_events",
                f"Event: {repr(event)}",
                phase="event_dispatch",
            )
        return False

    def _notify_debug_panel(self, response_url: str):
        if self.debug_panel:
            self.debug_panel.setRoute(response_url)

    ### Response Handling

    def handle_response(
        self, response: Response, callback: Callable[[Request], Response]
    ) -> bool:
        self.site_renderer.remove_page_specific_content()
        self.site_renderer.apply_before_channel(response)
        self.navigator.set_navigation_func(callback)
        self._notify_debug_panel(response.url)
        updated = self.site_renderer.update_site(response)
        if updated:
            self.events.mount_navigation(self.navigator.navigate)
            # TODO: Improve this check for a full page load
            if not response.target or response.target.is_page_load:
                self.events.dispatch_page_loaded(
                    route=response.url,
                    request_id=response.request_id,
                    response_id=response.id,
                )
        self.site_renderer.apply_after_channel(response)
        if response.payload.is_redirect():
            self.navigator.handle_redirect(response, callback)
        return updated

    ### Event Handling
    def handle_server_event(self, event_data: TelemetryRecord) -> bool:
        try:
            event = event_data.to_json()
            debug_log("client.handle_event", event)
        except Exception as e:
            report_bridge_error(
                "client.convert_event_to_json",
                f"Error converting event to JSON: {repr(e)}",
                "bridge.client_bridge.handle_server_event",
                f"Exception: {repr(e)}",
                exception=e,
                phase="event_dispatch",
            )
            return False
        if event["kind"] == UpdatedConfigurationEvent.kind:
            if event.get("key") == "framed":
                self.site_renderer.toggle_frame()
            elif event.get("key") == "in_debug_mode":
                self.configuration.in_debug_mode = bool(event.get("value"))
                swap_debug_mode(js.document)
                update_subtle_debug_entry(
                    self.site_renderer.get_scope(),
                    self.configuration.in_debug_mode,
                    self.configuration.enable_subtle_debug_entry,
                )
            elif event.get("key") == "enable_subtle_debug_entry":
                self.configuration.enable_subtle_debug_entry = bool(event.get("value"))
                update_subtle_debug_entry(
                    self.site_renderer.get_scope(),
                    self.configuration.in_debug_mode,
                    self.configuration.enable_subtle_debug_entry,
                )
            else:
                report_bridge_error(
                    "client.unhandled_config_update",
                    "Unhandled configuration update event",
                    "bridge.client_bridge.handle_server_event",
                    f"Event payload: {repr(event)}",
                    phase="event_dispatch",
                )
        handled = self._handle_debug_events(event)

        # Any unhandled events get logged to the console for now
        if not handled:
            console_log(event)

        return handled

    ### Specialized Helpers

    def set_site_title(self, title: str) -> None:
        self.site_title = title
        # Only the primary instance (the default root) owns the shared page
        # <title>; embedded/secondary instances must not fight over it.
        if self.site_renderer.root_id == DRAFTER_TAG_IDS["ROOT"]:
            js.document.title = title
        if self.debug_panel:
            self.debug_panel.setHeaderTitle(title)
        # debug_log("client.set_title", title)
