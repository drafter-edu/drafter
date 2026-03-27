"""
ClientBridge: the unified bridge between the Python application and the browser DOM.

Handles site setup, DOM updates, navigation, event handling, request/response
management, channel content, redirect detection, history, hotkeys, and telemetry.
Runtime-specific differences (Skulpt vs Pyodide) are delegated to a RuntimeAdapter.
"""

import json
import time
import html
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
from drafter.constants import SUBMIT_BUTTON_KEY
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

document = js.document  # type: ignore

DOUBLE_PRESS_THRESHOLD = 600  # milliseconds


@dataclass
class NavEvent:
    kind: str
    url: str
    data: dict
    submitter: Optional[Any] = None
    dom_id: Optional[str] = None


@dataclass
class ClientBridge:
    root_id: str
    _true_root_id: str
    _runtime: RuntimeAdapter = field(default_factory=create_runtime)
    channel_history: dict[str, set[str]] = field(default_factory=dict)
    redirect_loop_stack: list[str] = field(default_factory=list)
    navigation_func: Optional[Callable[[Request], Response]] = None
    request_count: int = 1
    site_title: str = "Default Title"
    debug_panel: Optional[Any] = None
    click_handler: Any = None
    submit_handler: Any = None
    popstate_listener: Optional[Callable[[Any], None]] = None
    hotkey_events: dict[str, Callable[[], None]] = field(default_factory=dict)
    last_press_time: int = 0
    hotkey_listener_ready: bool = False

    def __init__(self, configuration: ClientServerConfiguration):
        self.root_id = configuration.root_element_id
        self._true_root_id = configuration.root_element_id
        self._runtime = create_runtime()
        self.channel_history = {}
        self.redirect_loop_stack = []
        self.navigation_func = None
        self.request_count = 1
        self.site_title = "Default Title"
        self.debug_panel = None
        self.click_handler = None
        self.submit_handler = None
        self.popstate_listener = None
        self.hotkey_events = {}
        self.last_press_time = 0
        self.hotkey_listener_ready = False

    # ── Root element access ──────────────────────────────────────────

    def get_root(self):
        # TODO: Handle this correctly for shadowdom
        return document.getElementById(self.root_id)

    # ── Site setup ───────────────────────────────────────────────────

    def setup_site(self, initial_site_data: InitialSiteData) -> None:
        if initial_site_data.error:
            console_log("Error in initial site data: " + repr(initial_site_data))
            true_root = document.getElementById(self._true_root_id)
            true_root.innerHTML = initial_site_data.site_html
            return None

        try:
            true_root = document.getElementById(self._true_root_id)
            self.set_site_title(initial_site_data.site_title)
            remove_existing_theme(true_root, DRAFTER_TAG_CLASSES["THEME"])
            remove_existing_theme(true_root, DRAFTER_TAG_CLASSES["PRECOMPILE_HEADERS"])

            if initial_site_data.use_shadow_dom:
                true_root.innerHTML = SITE_HTML_SHADOW_DOM_TEMPLATE
                shadow_host = document.getElementById(DRAFTER_TAG_IDS["SHADOW_HOST"])
                if not shadow_host:
                    raise ValueError("Shadow host element not found in the document.")
                shadow_root = shadow_host.attachShadow({"mode": "open"})
                shadow_root.innerHTML = initial_site_data.site_html
                root = shadow_root

                for css in initial_site_data.additional_css:
                    css_url = css.url if hasattr(css, "url") else css
                    css_classes = (
                        " ".join(css.classes) if hasattr(css, "classes") else ""
                    )
                    classes = (
                        f"{DRAFTER_TAG_CLASSES['THEME']} {css_classes}".strip()
                    )
                    add_link_to_shadow(shadow_root, css_url, with_class=classes)
                for style in initial_site_data.additional_style:
                    add_style_to_shadow(
                        shadow_root, style, with_class=DRAFTER_TAG_CLASSES["THEME"]
                    )
            else:
                true_root.innerHTML = initial_site_data.site_html
                root = true_root

                for css in initial_site_data.additional_css:
                    css_url = css.url if hasattr(css, "url") else css
                    css_classes = (
                        " ".join(css.classes) if hasattr(css, "classes") else ""
                    )
                    classes = (
                        f"{DRAFTER_TAG_CLASSES['THEME']} {css_classes}".strip()
                    )
                    add_link(root, css_url, with_class=classes)
                for style in initial_site_data.additional_style:
                    add_style(root, style, with_class=DRAFTER_TAG_CLASSES["THEME"])

            for js_code in initial_site_data.additional_js:
                add_js(root, js_code, with_class=DRAFTER_TAG_CLASSES["THEME"])
            for header in initial_site_data.additional_header:
                add_header(root, header)

            self._setup_debug_menu()

            if not initial_site_data.framed:
                self.toggle_frame()

        except Exception as e:
            console_log(f"Error setting up site: {e}")
            raise e

    # ── Title ────────────────────────────────────────────────────────

    def set_site_title(self, title: str):
        self.site_title = title
        js.document.title = title
        debug_log("client.set_title", title)
        if self.debug_panel:
            self.debug_panel.setHeaderTitle(title)

    # ── Debug panel ──────────────────────────────────────────────────

    def _setup_debug_menu(self):
        debug_log("client.setup_debug_menu")
        try:
            self.debug_panel = self._runtime.create_debug_panel(
                DRAFTER_TAG_IDS["DEBUG"], self
            )
        except Exception as e:
            print(f"[Drafter Client] Failed to set up debug menu because of {e}")
            raise e

    # ── Channel content ──────────────────────────────────────────────

    def remove_page_specific_content(self) -> None:
        """
        Removes CSS and JS that were added for the previous page.
        This ensures that page-specific styles/scripts don't persist across navigation.
        """
        remove_page_content(self.get_root())

    def add_channel_content(
        self, channel: Optional[Channel], is_page_specific: bool = False
    ) -> None:
        """
        Processes messages from a channel and adds them to the page.
        Supports 'script' and 'style' message kinds.

        Args:
            channel: The channel containing messages to process.
            is_page_specific: If True, marks content as page-specific (will be removed on navigation).
        """
        if channel:
            root = self.get_root()
            for message in channel.messages:
                if message.sigil is not None:
                    if channel.name not in self.channel_history:
                        self.channel_history[channel.name] = set()
                    if message.sigil in self.channel_history[channel.name]:
                        continue
                    self.channel_history[channel.name].add(message.sigil)
                if message.kind == "script":
                    # TODO: Handle errors while executing this script
                    add_js(root, message.content, is_page_specific=is_page_specific)
                elif message.kind == "style":
                    # TODO: Need to look up whether we are using the shadow dom or not
                    add_style(
                        root,
                        message.content,
                        is_page_specific=is_page_specific,
                    )

    # ── Response handling ────────────────────────────────────────────

    def handle_response(
        self, response: Response, callback: Callable[[Request], Response]
    ) -> bool:
        self.remove_page_specific_content()

        self.add_channel_content(
            response.channels.get(DEFAULT_CHANNEL_BEFORE), is_page_specific=True
        )
        outcome = self.update_site(response, callback)
        self.add_channel_content(
            response.channels.get(DEFAULT_CHANNEL_AFTER), is_page_specific=True
        )
        if response.payload.is_redirect():
            self.handle_redirect(response, callback)
        return outcome

    def update_site(
        self, response: Response, callback: Callable[[Request], Response]
    ) -> bool:
        self.navigation_func = callback

        # Notify the debug panel
        if self.debug_panel:
            self.debug_panel.setRoute(response.url)

        # Replace the body
        body = response.body
        if body is not None:
            # Get the body element
            root_body = js.document.getElementById(DRAFTER_TAG_IDS["BODY"])

            # Convert target to CSS selector
            if response.target:
                selector = response.target.to_selector()
            else:
                selector = f"#{DRAFTER_TAG_IDS['BODY']}"

            elements = js.document.querySelectorAll(selector)

            if not elements:
                # TODO: Handle this more gracefully
                raise RuntimeError("Target element not found in document.")

            elements.forEach(
                lambda element, index, array: replace_html(
                    element,
                    body,
                    response.target.replace if response.target else False,
                )
            )

            debug_log("client.update_site_complete", response)
            if not response.target or response.target.id == DRAFTER_TAG_IDS["BODY"]:
                self.mount_navigation(root_body, self.navigate)

        return True

    # ── Redirect handling ────────────────────────────────────────────

    def clear_redirect_stack(self) -> None:
        self.redirect_loop_stack.clear()

    def handle_redirect(
        self, response: Response, callback: Callable[[Request], Response]
    ) -> None:
        if repr(response.payload) in self.redirect_loop_stack:
            # TODO: Raise an error here instead of just logging
            console_log(
                "Redirect loop detected: " + " -> ".join(self.redirect_loop_stack)
            )
            return
        self.redirect_loop_stack.append(repr(response.payload))
        new_request = self.make_redirect_request_from_response(response)
        callback(new_request)
        self.redirect_loop_stack.pop()

    # ── Request building ─────────────────────────────────────────────

    def make_initial_request(self) -> Request:
        return Request(0, "page_load", "index", {}, {}, "")

    def make_redirect_request_from_response(self, response: Response) -> Request:
        debug_log("client.make_redirect_request_from_response", response)
        target_route, arguments = response.payload.get_redirect()

        new_request = Request(
            self.request_count,
            "redirect",
            target_route,
            arguments if arguments else {},
            {},
            response.target.to_selector() if response.target else "",
        )
        self.request_count += 1
        return new_request

    def make_request(
        self,
        url: str,
        data: dict,
        action: str = "submit",
        dom_id: Optional[str] = None,
    ) -> Request:
        data = dict(data)
        button_pressed = self._extract_button_pressed(data)

        new_request = Request(
            self.request_count,
            action,
            url,
            data,
            {},
            dom_id or "",
            button_pressed=button_pressed,
        )
        self.request_count += 1
        return new_request

    def _extract_button_pressed(self, data: dict) -> str:
        button_pressed = ""
        if SUBMIT_BUTTON_KEY in data:
            button_value = data.pop(SUBMIT_BUTTON_KEY)
            if isinstance(button_value, list) and button_value:
                button_value = button_value[0]
            if isinstance(button_value, str):
                try:
                    button_pressed = json.loads(button_value)
                except (json.JSONDecodeError, TypeError):
                    button_pressed = button_value
        return str(button_pressed)

    # ── Navigation ───────────────────────────────────────────────────

    def goto(
        self,
        url: str,
        data: Optional[dict] = None,
        action="system",
        dom_id=None,
    ):
        if self.navigation_func is None:
            raise RuntimeError("Navigation function not set in ClientBridge.")
        return self.initiate_request(url, data or {}, True, action, dom_id)

    def navigate(self, nav_event: NavEvent):
        return self.initiate_request(
            nav_event.url,
            nav_event.data,
            True,
            nav_event.kind,
            nav_event.dom_id,
        )

    def initiate_request(
        self,
        url: str,
        data: dict,
        remember=True,
        action="submit",
        dom_id: Optional[str] = None,
    ):
        if self.navigation_func is None:
            raise RuntimeError("Navigation function not set in ClientBridge.")
        debug_log("client.initiate_request", url, data, remember, action)
        request = self.make_request(url, data, action, dom_id)
        if remember:
            self.add_to_history(request)
        next_visit = self.navigation_func(request)
        return next_visit

    # ── History ──────────────────────────────────────────────────────

    def add_to_history(self, request: Request):
        url = request.url
        request_id = request.id
        state = {
            "request_id": request_id,
            "url": url,
            # TODO: Track parameters as well
        }
        full_url = self._runtime.create_url(js.location.href)
        js.document.title = f"{self.site_title} - {url}"
        full_url.searchParams.set("route", url)
        self._runtime.history_push_state(state, "", full_url.toString())
        debug_log("client.add_to_history", state, request)

    def handle_popstate(self, event: Any) -> None:
        debug_log("client.handle_popstate", event)
        if (
            event
            and "state" in event
            and "request_id" in event.state
            and event.state["request_id"] is not None
        ):
            request_id = event.state.request_id
            url = event.state.url
            debug_log("client.handle_popstate_with_state", request_id, url)
            js.document.title = f"{self.site_title} - {url}"
            full_url = self._runtime.create_url(js.location.href)
            full_url.searchParams.set("route", url)
            js.history.replaceState(event.state, "", full_url.toString())
            # TODO: Restore the data dictionary
            self.initiate_request(url, {}, False, "back", None)
        else:
            debug_log("client.handle_popstate_no_state_or_request_id", event)
            js.document.title = self.site_title
            full_url = self._runtime.create_url(js.location.href)
            full_url.searchParams.delete("route")
            js.history.replaceState({}, "", full_url.toString())
            self.initiate_request("index", {}, False, "back", None)

    # ── Frame toggle ─────────────────────────────────────────────────

    def toggle_frame(self) -> None:
        FRAME_PIECES = ",".join(
            f".{DRAFTER_TAG_IDS[key]}"
            for key in ["PADDING_V", "PADDING_H", "HEADER", "FOOTER"]
        )
        frames = js.document.querySelectorAll(FRAME_PIECES)
        if frames:
            for frame in frames:
                frame.classList.toggle("drafter-hidden--")
        body = js.document.querySelector("." + DRAFTER_TAG_IDS["BODY"])
        if body:
            body.classList.toggle("drafter-body-frame-hidden--")

    # ── Form data extraction ─────────────────────────────────────────

    def get_all_event_data(
        self, originator: Any, event: Any, submitter: Any
    ) -> dict:
        """ Collect all relevant data for an event, including form data and arguments."""
        data = {}
        # Get form data
        # TODO: Allow specifying a different form or scope for data collection
        form = js.document.getElementById(DRAFTER_TAG_IDS["FORM"])
        if form:
            form_data = self._runtime.create_form_data(form, submitter)
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
                    self._runtime.handle_file_upload(value, data, key)
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

    # ── Event mounting ───────────────────────────────────────────────

    def mount_event_handlers(self, root: Any, on_navigation: Callable):
        """Mount event handlers for components with data--drafter-handlers attribute.
        
        This sets up delegation for events like blur, change, focus, input, etc.,
        that should trigger route dispatches.
        
        Args:
            root: The root element to attach listeners to.
            on_navigation: Callback to handle navigation events.
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
                        
                        data = self.get_all_event_data(target_element, event, None)
                        nav_event = NavEvent(
                            kind=event_name,
                            url=route,
                            data=data,
                            submitter=target_element,
                            dom_id=dom_id,
                        )
                        return on_navigation(nav_event)

                    return handler

                wrapped_handler = self._runtime.wrap_event_handler(
                    make_handler(event_type, route_name)
                )
                element.addEventListener(event_type, wrapped_handler)

    def mount_navigation(self, root: Any, on_navigation: Callable):
        debug_log("client.mount_navigation")
        # Clean up old handlers if they exist
        if self.click_handler is not None:
            root.removeEventListener("click", self.click_handler)
            self._runtime.cleanup_event_handler(self.click_handler)

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
                data = self.get_all_event_data(
                    target, event, None if is_anchor else nearest_nav_link
                )
                nav_event = NavEvent(
                    kind="link",
                    url=name,
                    data=data,
                    submitter=nearest_nav_link,
                    dom_id=dom_id,
                )
                return on_navigation(nav_event)

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
            data = self.get_all_event_data(event.target, event, submitter)
            if submitter is not None and hasattr(submitter, "getAttribute"):
                url = submitter.getAttribute("formaction")
            elif hasattr(form_root, "action"):
                url = form_root.action
            else:
                url = js.location.href
            # Build and dispatch navigation event
            nav_event = NavEvent(
                kind="form",
                url=url,
                data=data,
                submitter=submitter,
                dom_id=dom_id,
            )
            return on_navigation(nav_event)

        self.click_handler = self._runtime.wrap_event_handler(handle_click)
        self.submit_handler = self._runtime.wrap_event_handler(submit_handler)

        root.addEventListener("click", self.click_handler)

        form_root = js.document.getElementById(DRAFTER_TAG_IDS["FORM"])
        if form_root:
            form_root.addEventListener("submit", self.submit_handler)
        else:
            raise RuntimeError("Form root element not found for mounting navigation.")

        # Mount event handlers for components
        self.mount_event_handlers(root, on_navigation)
        debug_log("client.mount_navigation_complete")

    # ── Global event setup ───────────────────────────────────────────

    def setup_events(
        self,
        handle_visit: Callable[[Request], Response],
        handle_toggle_frame: Callable,
        handle_debug_mode: Callable,
    ) -> None:
        debug_log("client.setup_events")
        self.navigation_func = handle_visit

        if self.popstate_listener is not None:
            js.removeEventListener("popstate", self.popstate_listener)
            self._runtime.cleanup_event_handler(self.popstate_listener)

        self.popstate_listener = self._runtime.wrap_event_handler(self.handle_popstate)
        js.addEventListener("popstate", self.popstate_listener)

        # Specialized Drafter events
        drafter_nav_handler = self._runtime.wrap_event_handler(
            lambda event: self.goto(event.detail)
        )
        drafter_toggle_handler = self._runtime.wrap_event_handler(
            lambda event: handle_toggle_frame()
        )
        js.addEventListener("drafter-navigate", drafter_nav_handler)
        js.addEventListener("drafter-toggle-frame", drafter_toggle_handler)
        # Keyboard events
        self.register_hotkey("Q", handle_debug_mode)

    # ── Hotkeys ──────────────────────────────────────────────────────

    def register_hotkey(self, key_combo: str, callback: Callable[[], None]) -> None:
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
            wrapped_handler = self._runtime.wrap_event_handler(hotkey_handler)
            js.document.addEventListener("keydown", wrapped_handler)
            self.hotkey_listener_ready = True
            debug_log("client.hotkey_listener_registered")

    # ── Telemetry ────────────────────────────────────────────────────

    def handle_telemetry_event(self, event: TelemetryEvent) -> None:
        handled = self.handle_event(event.to_json())
        if not handled:
            console_log(event)

    def handle_event(self, event: dict) -> bool:
        debug_log("client.handle_event", event)
        if event["event_type"] == UpdatedConfigurationEvent.event_type:
            if event.get("data", {}).get("key") == "framed":
                self.toggle_frame()
            elif event.get("data", {}).get("key") == "in_debug_mode":
                swap_debug_mode(js.document)
            else:
                print("NEED TO HANDLE CONFIG UPDATE EVENT IN CLIENT", event)
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
        # TODO: Return false instead of raising error
        return False

    def console_log_events(self, event: TelemetryEvent) -> None:
        console_log(event)
