"""
ClientBridge: the unified bridge between the Python application and the browser DOM.

Handles site setup, DOM updates, navigation, event handling, request/response
management, channel content, redirect detection, history, hotkeys, and telemetry.
Runtime-specific differences (Skulpt vs Pyodide) are delegated to a RuntimeAdapter.
"""

import json
import time
import html

from drafter.bridge.events import EventManager, get_all_event_data
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
)
from drafter.bridge.log import debug_log, console_log
from drafter.bridge.runtime import RuntimeAdapter, create_runtime
from drafter.config.client_server import ClientServerConfiguration

from drafter.components.page_content import Component
from drafter.data.channel import DEFAULT_CHANNEL_AFTER, DEFAULT_CHANNEL_BEFORE, Channel
from drafter.data.response import Response
from drafter.data.request import Request
from drafter.monitor.events.config import UpdatedConfigurationEvent
from drafter.monitor.telemetry import TelemetryEvent
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
    debug_panel: Optional[Any] = None
    runtime: RuntimeAdapter = field(default_factory=create_runtime)
    site_title: str = "Default Title"
    

    def __init__(self, configuration: ClientServerConfiguration):
        self.runtime = create_runtime()
        self.site_renderer = SiteRenderer(self.runtime, configuration.root_element_id, configuration.root_element_id)
        self.navigator = NavigationController(self.runtime)
        self.events = EventManager(self.runtime)
        self.debug_panel = None
    
    def setup_site(self, initial_site_data: InitialSiteData) -> None:
        self.set_site_title(initial_site_data.site_title)
        self.site_renderer.setup(initial_site_data)
        self._setup_debug_menu()
        
    def setup_events(self, handle_visit: Callable[[Request], Response], handle_toggle_frame: Callable, handle_debug_mode: Callable) -> None:
        self.navigator.set_navigation_func(handle_visit)
        self.events.setup_events({
            "drafter-toggle-frame": lambda event: handle_toggle_frame(), 
            "drafter-navigate": lambda event: self.navigator.goto(event.detail),
            "popstate": self.navigator.handle_popstate
        }, {
            "Q": handle_debug_mode,
        })
        
    def start(self):
        """
        Load the initial request.
        """
        self.navigator.do_initial_request()

    ### Debug Panel

    def _setup_debug_menu(self):
        debug_log("client.setup_debug_menu")
        try:
            self.debug_panel = self.runtime.create_debug_panel(
                DRAFTER_TAG_IDS["DEBUG"], self
            )
        except Exception as e:
            # TODO: Surface this error in the UI instead of just logging it
            print(f"[Drafter Client] Failed to set up debug menu because of {e}")
            raise e
        
    def _handle_debug_events(self, event: dict) -> bool:
        if self.debug_panel:
            try:
                handled = self.debug_panel.handleEvent(event)
                return handled
            except Exception as e:
                print(
                    f"[Drafter Client] Failed to handle event {event} because of {e}"
                )
                raise e
        else:
            print(f"[Drafter Client] No debug panel to handle event {event}")
            raise RuntimeError("No debug panel to handle event.")
        
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
        self.site_renderer.apply_after_channel(response)
        if response.payload.is_redirect():
            self.navigator.handle_redirect(response, callback)
        return updated

    ### Event Handling
    def handle_server_event(self, event_data: TelemetryEvent) -> bool:
        event = event_data.to_json()
        debug_log("client.handle_event", event)
        if event["event_type"] == UpdatedConfigurationEvent.event_type:
            if event.get("data", {}).get("key") == "framed":
                self.site_renderer.toggle_frame()
            elif event.get("data", {}).get("key") == "in_debug_mode":
                swap_debug_mode(js.document)
            else:
                print("NEED TO HANDLE CONFIG UPDATE EVENT IN CLIENT", event)
        handled = self._handle_debug_events(event)
        
        # Any unhandled events get logged to the console for now
        if not handled:
            console_log(event)
        
        return handled
        
    ### Specialized Helpers
    
    def set_site_title(self, title: str) -> None:
        self.site_title = title
        js.document.title = title
        if self.debug_panel:
            self.debug_panel.setHeaderTitle(title)
        # debug_log("client.set_title", title)