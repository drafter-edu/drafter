import json
import time
from dataclasses import dataclass, field
from typing import Any, Optional, Callable
from drafter.bridge.runtime import RuntimeAdapter
from drafter.constants import SUBMIT_BUTTON_KEY
from drafter.data.response import Response
from drafter.data.request import Request
from drafter.bridge.log import debug_log, console_log
from drafter.components.page_content import Component
from drafter.monitor.events.config import UpdatedConfigurationEvent
from drafter.monitor.telemetry import TelemetryEvent
from drafter.site.site import DRAFTER_TAG_IDS
from drafter.bridge.dom import (
    get_attribute_recursively,
)
import js

DOUBLE_PRESS_THRESHOLD = 600  # milliseconds


@dataclass
class EventManager:
    runtime: RuntimeAdapter
    click_handler: Any = None
    submit_handler: Any = None
    listeners: dict[str, Callable] = field(default_factory=dict)
    hotkey_events: dict[str, Callable[[], None]] = field(default_factory=dict)
    last_press_time: int = 0
    hotkey_listener_ready: bool = False
    
    def __init__(self, runtime: RuntimeAdapter):
        self.runtime = runtime
        self.click_handler = None
        self.submit_handler = None
        self.listeners = {}

        self.hotkey_events = {}
        self.last_press_time = 0
        self.hotkey_listener_ready = False
        
    # Event Mounts

    def mount_event_handlers(self, root: Any, do_navigation: Callable):
        """Mount event handlers for components with data--drafter-handlers attribute.
        
        This sets up delegation for events like blur, change, focus, input, etc.,
        that should trigger route dispatches.
        
        Args:
            root: The root element to attach listeners to.
            do_navigation: Callback to handle navigation events.
        """
        debug_log("client.mount_event_handlers")

        elements_with_handlers = root.querySelectorAll("[data--drafter-handlers]")

        for element in elements_with_handlers:
            handlers_json = element.getAttribute("data--drafter-handlers")
            if not handlers_json:
                continue

            try:
                handlers = json.loads(handlers_json)
            except:
                console_log(f"Failed to parse event handlers: {handlers_json}")
                continue
            # For each event type in the handlers
            for event_type, route_name in handlers.items():
                # Create a handler function for this event
                def make_handler(event_name, route):
                    def handler(event):
                        debug_log(f"client.event_handler.{event_name}", event)
                        
                        # Don't prevent default for most events (except clicks handled elsewhere)
                        target_element = event.target
                        dom_id = (
                            target_element.id
                            if hasattr(target_element, "id")
                            else None
                        )
                        
                        data = get_all_event_data(self.runtime, target_element, event, None)
                        request = Request(
                            action=event_name,
                            url=route,
                            kwargs=data,
                            event={}, # TODO: Populate this with useful event info
                            dom_id=dom_id or "",
                            button_pressed=target_element
                        )
                        return do_navigation(request)

                    return handler

                wrapped_handler = self.runtime.wrap_event_handler(
                    make_handler(event_type, route_name)
                )
                element.addEventListener(event_type, wrapped_handler)

    def mount_navigation(self, do_navigation: Callable):
        debug_log("client.mount_navigation")
        # Get the body element
        root = js.document.getElementById(DRAFTER_TAG_IDS["BODY"])
        # Clean up old handlers if they exist
        if self.click_handler is not None:
            root.removeEventListener("click", self.click_handler)
            self.runtime.cleanup_event_handler(self.click_handler)

        # Store the navigation callback
        def handle_click(event: Any):
            target = event.target
            if not target:
                return

            # Find nearest element with data-nav or data-call
            nearest_nav_link = target.closest("[data-nav], [data-call]")
            if nearest_nav_link and root.contains(nearest_nav_link):
                event.preventDefault()
                debug_log("client.handle_click", nearest_nav_link)
                name = nearest_nav_link.getAttribute(
                    "data-nav"
                ) or nearest_nav_link.getAttribute("data-call")
                if not name:
                    return

                dom_id = (
                    nearest_nav_link.id
                    if hasattr(nearest_nav_link, "id")
                    else None
                )

                is_anchor = nearest_nav_link.tagName.lower() == "a"
                data = get_all_event_data(
                    self.runtime, target, event, None if is_anchor else nearest_nav_link
                )
                request = Request(
                    action="link",
                    url=name,
                    kwargs=data,
                    event={}, # TODO: Populate this with useful event info
                    dom_id=dom_id or "",
                    button_pressed=nearest_nav_link if not is_anchor else ""
                )
                return do_navigation(request)

        def submit_handler(event: Any):
            debug_log("client.form_submit_handler", event)
            event.preventDefault()
            # Figure out submitter
            if hasattr(event, "submitter"):
                submitter = event.submitter
                dom_id = (
                    submitter.id
                    if submitter and hasattr(submitter, "id")
                    else None
                )
            else:
                submitter = None
                dom_id = None
            data = get_all_event_data(self.runtime, event.target, event, submitter)
            if submitter is not None and hasattr(submitter, "getAttribute"):
                url = submitter.getAttribute("formaction")
            elif hasattr(form_root, "action"):
                url = form_root.action
            else:
                url = js.location.href
            # Build and dispatch navigation event
            request = Request(
                action="form",
                url=url,
                kwargs=data,
                event={}, # TODO: Populate this with useful event info
                dom_id=dom_id or "",
                button_pressed=submitter if submitter else ""
            )
            return do_navigation(request)

        self.click_handler = self.runtime.wrap_event_handler(handle_click)
        self.submit_handler = self.runtime.wrap_event_handler(submit_handler)

        root.addEventListener("click", self.click_handler)

        form_root = js.document.getElementById(DRAFTER_TAG_IDS["FORM"])
        if form_root:
            form_root.addEventListener("submit", self.submit_handler)
        else:
            raise RuntimeError("Form root element not found for mounting navigation.")

        # Mount event handlers for components
        self.mount_event_handlers(root, do_navigation)
        debug_log("client.mount_navigation_complete")

    ### Global Event Handler Registration
    def setup_events(
        self,
        event_handlers: dict[str, Callable[[Any], Any]],
        key_handlers: dict[str, Callable[[], None]],
    ) -> None:
        debug_log("client.setup_events")
        
        # Global events
        for event_name, handler in event_handlers.items():
            self._register_event(event_name, handler)

        # Keyboard events
        for key_combo, handler in key_handlers.items():
            self._register_hotkey(key_combo, handler)

    def _register_event(self, event_name: str, handler: Callable[[Any], Any]) -> None:
        if self.listeners.get(event_name):
            js.removeEventListener(event_name, self.listeners[event_name])
            self.runtime.cleanup_event_handler(self.listeners[event_name])
        wrapped_handler = self.runtime.wrap_event_handler(handler)
        js.addEventListener(event_name, wrapped_handler)
        self.listeners[event_name] = wrapped_handler

    def _register_hotkey(self, key_combo: str, callback: Callable[[], None]) -> None:
        debug_log("client.register_hotkey", key_combo)
        key = key_combo.lower().split("+")[-1].strip()

        def hotkey_handler(event: Any):
            event_key = event.key.lower() if hasattr(event, "key") else ""
            ctrl = getattr(event, "ctrlKey", False) or getattr(
                event, "metaKey", False
            )

            if ctrl and event_key in self.hotkey_events:
                current_time = int(time.time() * 1000)
                time_since_last = current_time - self.last_press_time

                if time_since_last < DOUBLE_PRESS_THRESHOLD:
                    debug_log("client.hotkey_triggered", event_key)
                    event.preventDefault()
                    self.hotkey_events[event_key]()
                    self.last_press_time = 0 # Reset to avoid triple presses being treated as double presses
                else:
                    self.last_press_time = current_time

        self.hotkey_events[key] = callback
        if not self.hotkey_listener_ready:
            wrapped_handler = self.runtime.wrap_event_handler(hotkey_handler)
            js.document.addEventListener("keydown", wrapped_handler)
            self.hotkey_listener_ready = True
            debug_log("client.hotkey_listener_registered")
    

def get_all_event_data(
    runtime: RuntimeAdapter, originator: Any, event: Any, submitter: Any
) -> dict:
    """ Collect all relevant data for an event, including form data and arguments."""
    data = {}
    # Get form data
    # TODO: Allow specifying a different form or scope for data collection
    form = js.document.getElementById(DRAFTER_TAG_IDS["FORM"])
    if form:
        form_data = runtime.create_form_data(form, submitter)
        # First convert all form data to a regular dict, handling file uploads as well
        for key, value in form_data.entries():
            if isinstance(value, str):
                if key in data:
                    if not isinstance(data[key], list):
                        data[key] = [data[key]]
                    data[key].append(value)
                else:
                    data[key] = value
            else:
                runtime.handle_file_upload(value, data, key)
        # Look for `data-transform` attributes to decode any special fields (e.g., JSON-encoded arguments)
        for element in form.elements:
            if element.hasAttribute("data-transform"):
                transform = element.getAttribute("data-transform")
                if transform == "json-decode":
                    key = element.name
                    value = element.value
                    try:
                        decoded_value = json.loads(value)
                        data[key] = decoded_value
                    except json.JSONDecodeError:
                        data[key] = value # Fallback to raw value if JSON decoding fails
                        # TODO: Log an error somewhere

    # Get arguments from the originator and its parents
    arguments = get_attribute_recursively(
        originator, Component.DRAFTER_DATA_ARGUMENT_NAME
    )
    for i, arg in enumerate(reversed(arguments)):
        # TODO: Handle corruption more elegantly
        parsed = json.loads(arg)
        data.update(parsed)

    return data