"""
Client module for interacting with the browser DOM using the js package.
The ClientBridge uses this to manipulate the page content and handle navigation.
This module works with both Skulpt and Pyodide by using the unified `js` module interface.
"""

import json
from drafter.bridge.helpers import swap_debug_mode
from drafter.config.client_server import ClientServerConfiguration
from drafter.data.response import Response
from drafter.data.request import Request
from drafter.monitor.events.config import UpdatedConfigurationEvent
from drafter.site.site import DRAFTER_TAG_IDS, DRAFTER_TAG_CLASSES
from drafter.monitor.telemetry import TelemetryEvent, TelemetryCorrelation
from drafter.helpers.utils import is_skulpt, is_pyodide
from drafter.components.page_content import Component
from typing import Callable, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass, field
import time
import js

if TYPE_CHECKING:
    from drafter.payloads.target import Target

DOUBLE_PRESS_THRESHOLD = 600  # milliseconds


@dataclass
class NavEvent:
    kind: str
    url: str
    data: Any  # FormData-like object
    arguments: list[
        str
    ]  # The JSON blobs of data stored in the data--drafter-arguments attribute of the element and any parents.
    submitter: Optional[Any] = None
    dom_id: Optional[str] = None


def replace_html(tag: Any, html: str, is_fragment: bool = False) -> None:
    # Save current scroll position
    scroll_top = js.scrollY
    scroll_left = js.scrollX

    try:
        r = js.document.createRange()
        r.selectNode(tag)
        fragment = r.createContextualFragment(html)

        if not is_fragment:
            # Existing behavior: replace children only
            tag.replaceChildren(fragment)
            return

        # is_fragment=True: replace the tag itself
        parent = tag.parentNode
        if parent is None:
            # Detached node; best effort fallback: replace children
            tag.replaceChildren(fragment)
            return

        # Snapshot fragment children because moving nodes mutates the fragment
        new_nodes = list(fragment.childNodes)

        if len(new_nodes) == 0:
            # Nothing to insert; remove the tag
            parent.removeChild(tag)
        elif len(new_nodes) == 1:
            # Simple node-for-node replacement
            parent.replaceChild(new_nodes[0], tag)
        else:
            # Replace tag with multiple nodes:
            # insert each before tag, then remove tag
            for node in new_nodes:
                parent.insertBefore(node, tag)
            parent.removeChild(tag)

    finally:
        # Restore scroll position
        js.scrollTo(scroll_left, scroll_top)


def get_attribute_recursively(element: Any, attribute_name: str) -> list[str]:
    current_element = element
    attributes = []
    while current_element:
        if current_element.hasAttribute(attribute_name):
            attributes.append(current_element.getAttribute(attribute_name))
        current_element = current_element.parentElement
    return attributes


@dataclass
class Client:
    root_id: str
    _true_root_id: str
    navigation_func: Optional[Callable[[Request], Response]] = None
    request_count: int = 1
    site_title: str = "Default Title"
    debug_panel: Optional[Any] = None
    click_handler: Any = None
    submit_handler: Any = None
    popstate_listener: Optional[Callable[[Any], None]] = None
    hotkey_events: dict[str, Callable[[], None]] = field(default_factory=dict)
    last_press_time: int = 0
    hotkey_listener_ready = False

    def reset(self):
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

    def set_site_title(self, title: str):
        self.site_title = title
        js.document.title = title
        debug_log("client.set_title", title)
        if self.debug_panel:
            self.debug_panel.setHeaderTitle(title)

    def goto(
        self,
        url: str,
        form_data: Any = None,
        action="system",
        arguments=None,
        dom_id=None,
    ):
        if self.navigation_func is None:
            raise RuntimeError("Navigation function not set in Client.")
        return self.initiate_request(url, form_data, True, action, arguments, dom_id)

    def navigate(self, nav_event: NavEvent):
        return self.initiate_request(
            nav_event.url,
            nav_event.data,
            True,
            nav_event.kind,
            nav_event.arguments,
            nav_event.dom_id,
        )

    def setup_debug_menu(self, client_bridge):
        debug_log("client.setup_debug_menu")
        try:
            self.debug_panel = self._create_debug_panel(client_bridge)
        except Exception as e:
            print(f"[Drafter Client] Failed to set up debug menu because of {e}")
            raise e

    def _create_debug_panel(self, client_bridge):
        """Create a debug panel instance. Override in subclasses for runtime-specific construction."""
        return js.DebugPanel(DRAFTER_TAG_IDS["DEBUG"], client_bridge)

    def _create_url(self, href: str):
        """Create a URL object. Override in subclasses for runtime-specific construction."""
        return js.URL(href)

    def _create_form_data(self, form: Any, submitter: Any = None):
        """Create a FormData object. Override in subclasses for runtime-specific construction."""
        return js.FormData(form, submitter)

    def _wrap_event_handler(self, handler: Callable) -> Any:
        """Wrap an event handler appropriately for the runtime. Override in subclasses if needed."""
        return handler

    def _handle_file_upload(self, file: Any, data: dict, key: str) -> None:
        """Handle file upload from form data. Override in subclasses for async handling."""
        buffer = file.arrayBuffer()
        raw_bytes = js.Uint8Array(buffer)
        content = bytes(raw_bytes)
        file_data = {
            "filename": file.name,
            "content": content,
            "type": file.type,
            "size": file.size,
            "__file_upload__": True,
        }
        if key not in data:
            data[key] = file_data
        else:
            if not isinstance(data[key], list):
                data[key] = [data[key]]
            data[key].append(file_data)

    def _finalize_request(
        self, action: str, url: str, data: dict, dom_id: Optional[str]
    ) -> Request:
        """Finalize and return a request. Override in subclasses for async handling."""
        new_request = Request(self.request_count, action, url, data, {}, dom_id or "")
        self.request_count += 1
        return new_request

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
            # print("Attempting to handle event in debug panel:", event)
            try:
                handled = self.debug_panel.handleEvent(event)
                return handled
            except Exception as e:
                print(f"[Drafter Client] Failed to handle event {event} because of {e}")
                raise e
        else:
            print(f"[Drafter Client] No debug panel to handle event {event}")
            raise RuntimeError("No debug panel to handle event.")
        # TODO: Return false instead of raising error
        return False

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

    def make_initial_request(self) -> Request:
        return Request(0, "page_load", "index", {}, {}, "")

    def make_request(
        self,
        url: str,
        form_data: Any = None,
        action: str = "submit",
        arguments: Optional[list[str]] = None,
        dom_id: Optional[str] = None,
    ) -> Request:
        data = {}
        # Convert form data to a regular dict, handling file uploads as well
        if form_data:
            for key, value in form_data.entries():
                if isinstance(value, str):
                    if key in data:
                        if not isinstance(data[key], list):
                            data[key] = [data[key]]
                        data[key].append(value)
                    else:
                        data[key] = value
                else:
                    self._handle_file_upload(value, data, key)
        # Add arguments to the data dict
        for i, arg in enumerate(reversed(arguments or [])):
            # TODO: Handle both of these more elegantly in case they are corrupted in some way
            parsed = json.loads(arg)
            data.update(parsed)

        return self._finalize_request(action, url, data, dom_id)

    def add_to_history(self, request: Request):
        url = request.url
        request_id = request.id
        state = {
            "request_id": request_id,
            "url": url,
            # TODO: Track parameters as well
        }
        full_url = self._create_url(js.location.href)
        js.document.title = f"{self.site_title} - {url}"
        full_url.searchParams.set("route", url)
        self._history_push_state(state, "", full_url.toString())
        debug_log("client.add_to_history", state, request)

    def _history_push_state(self, state: dict, title: str, url: str) -> None:
        """Push a new state to the browser history. Override in subclasses for runtime-specific handling."""
        js.history.pushState(state, title, url)

    def initiate_request(
        self,
        url: str,
        form_data: Any = None,
        remember=True,
        action="submit",
        arguments: Optional[list[str]] = None,
        dom_id: Optional[str] = None,
    ):
        if self.navigation_func is None:
            raise RuntimeError("Navigation function not set in Client.")
        debug_log("client.initiate_request", url, form_data, remember, action)
        request = self.make_request(url, form_data, action, arguments, dom_id)
        if remember:
            self.add_to_history(request)
        next_visit = self.navigation_func(request)
        return next_visit

    def mount_event_handlers(self, root: Any, on_navigation: Callable):
        """Mount event handlers for components with data--drafter-handlers attribute.
        
        This sets up delegation for events like blur, change, focus, input, etc.,
        that should trigger route dispatches.
        
        Args:
            root: The root element to attach listeners to.
            on_navigation: Callback to handle navigation events.
        """
        debug_log("client.mount_event_handlers")
        
        # Get all elements with event handlers
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
                        dom_id = target_element.id if hasattr(target_element, "id") else None
                        
                        # Get arguments from the element and its parents
                        arguments = get_attribute_recursively(
                            target_element, Component.DRAFTER_DATA_ARGUMENT_NAME
                        )
                        
                        # Get the current form data
                        form = js.document.getElementById(DRAFTER_TAG_IDS["FORM"])
                        if form:
                            form_data = self._create_form_data(form, None)
                            nav_event = NavEvent(
                                kind=event_name,
                                url=route,
                                data=form_data,
                                submitter=target_element,
                                arguments=arguments,
                                dom_id=dom_id,
                            )
                            return on_navigation(nav_event)
                        else:
                            console_log(f"Form element not found for {event_name} event handler")
                    return handler
                
                wrapped_handler = self._wrap_event_handler(make_handler(event_type, route_name))
                element.addEventListener(event_type, wrapped_handler)

    def mount_navigation(self, root: Any, on_navigation: Callable):
        debug_log("client.mount_navigation")
        # Clean up old handlers if they exist
        if self.click_handler is not None:
            root.removeEventListener("click", self.click_handler)
            self._cleanup_event_handler(self.click_handler)

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
                    nearest_nav_link.id if hasattr(nearest_nav_link, "id") else None
                )

                # Get the arguments from the clicked element and its parents
                arguments = get_attribute_recursively(
                    target, Component.DRAFTER_DATA_ARGUMENT_NAME
                )

                # Get the form element
                form = js.document.getElementById(DRAFTER_TAG_IDS["FORM"])
                if form:
                    is_anchor = nearest_nav_link.tagName.lower() == "a"
                    form_data = self._create_form_data(
                        form, None if is_anchor else nearest_nav_link
                    )
                    nav_event = NavEvent(
                        kind="link",
                        url=name,
                        data=form_data,
                        submitter=nearest_nav_link,
                        arguments=arguments,
                        dom_id=dom_id,
                    )
                    return on_navigation(nav_event)
                else:
                    raise RuntimeError("Form element not found for navigation.")

        def submit_handler(event: Any):
            debug_log("client.form_submit_handler", event)
            event.preventDefault()
            # Figure out submitter
            if hasattr(event, "submitter"):
                submitter = event.submitter
                dom_id = (
                    submitter.id if submitter and hasattr(submitter, "id") else None
                )
            else:
                submitter = None
                dom_id = None
            # Get the form data
            form_data = self._create_form_data(event.target, submitter)
            # Handle arguments
            # Get the arguments from the clicked element and its parents
            arguments = get_attribute_recursively(
                event.target, Component.DRAFTER_DATA_ARGUMENT_NAME
            )
            # Figure out URL
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
                data=form_data,
                submitter=submitter,
                arguments=arguments,
                dom_id=dom_id,
            )
            return on_navigation(nav_event)

        self.click_handler = self._wrap_event_handler(handle_click)
        self.submit_handler = self._wrap_event_handler(submit_handler)

        root.addEventListener("click", self.click_handler)

        form_root = js.document.getElementById(DRAFTER_TAG_IDS["FORM"])
        if form_root:
            form_root.addEventListener("submit", self.submit_handler)
        else:
            raise RuntimeError("Form root element not found for mounting navigation.")
        
        # Mount event handlers for components
        self.mount_event_handlers(root, on_navigation)
        
        debug_log("client.mount_navigation_complete")

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
                    element, body, response.target.replace if response.target else False
                )
            )
            # for element in elements:
            #    replace_html(element, body, bool(response.target))

            debug_log("client.update_site_complete", response)
            if not response.target or response.target.id == DRAFTER_TAG_IDS["BODY"]:
                self.mount_navigation(root_body, self.navigate)

        return True

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
            self._cleanup_event_handler(self.popstate_listener)

        self.popstate_listener = self._wrap_event_handler(self.handle_popstate)
        js.addEventListener("popstate", self.popstate_listener)

        # Specialized Drafter events
        drafter_nav_handler = self._wrap_event_handler(
            lambda event: self.goto(event.detail)
        )
        drafter_toggle_handler = self._wrap_event_handler(
            lambda event: handle_toggle_frame()
        )
        js.addEventListener("drafter-navigate", drafter_nav_handler)
        js.addEventListener("drafter-toggle-frame", drafter_toggle_handler)
        # Keyboard events
        self.register_hotkey("Q", handle_debug_mode)

    def _cleanup_event_handler(self, handler: Any, proxy: Any = None) -> None:
        """Clean up an event handler. Override in subclasses for runtime-specific cleanup."""
        pass

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
            full_url = self._create_url(js.location.href)
            full_url.searchParams.set("route", url)
            js.history.replaceState(event.state, "", full_url.toString())
            self.initiate_request(url, None, False, "back", None, None)
        else:
            debug_log("client.handle_popstate_no_state_or_request_id", event)
            js.document.title = self.site_title
            full_url = self._create_url(js.location.href)
            full_url.searchParams.delete("route")
            js.history.replaceState({}, "", full_url.toString())
            self.initiate_request("index", None, False, "back", None, None)

    def register_hotkey(self, key_combo: str, callback: Callable[[], None]) -> None:
        debug_log("client.register_hotkey", key_combo)
        key = key_combo.lower().split("+")[-1].strip()

        def hotkey_handler(event: Any):
            event_key = event.key.lower() if hasattr(event, "key") else ""
            ctrl = getattr(event, "ctrlKey", False) or getattr(event, "metaKey", False)

            if ctrl and event_key in self.hotkey_events:
                current_time = int(time.time() * 1000)
                time_since_last = current_time - self.last_press_time

                if time_since_last < DOUBLE_PRESS_THRESHOLD:
                    debug_log("client.hotkey_triggered", event_key)
                    event.preventDefault()
                    self.hotkey_events[event_key]()
                    self.last_press_time = 0  # Reset to avoid triple presses being treated as double presses
                else:
                    self.last_press_time = current_time

        self.hotkey_events[key] = callback
        if not self.hotkey_listener_ready:
            wrapped_handler = self._wrap_event_handler(hotkey_handler)
            js.document.addEventListener("keydown", wrapped_handler)
            self.hotkey_listener_ready = True
            debug_log("client.hotkey_listener_registered")


class PyodideClient(Client):
    """Pyodide-specific client implementation with proper proxy management."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from pyodide.ffi import create_proxy, to_js

        self._create_proxy = create_proxy
        self._to_js = to_js
        # Store proxies to prevent garbage collection
        self._click_proxy: Any = None
        self._submit_proxy: Any = None
        self._popstate_proxy: Any = None
        self._hotkey_proxy: Any = None
        self._drafter_nav_proxy: Any = None
        self._drafter_toggle_proxy: Any = None

    def reset(self):
        super().reset()
        self._click_proxy = None
        self._submit_proxy = None
        self._popstate_proxy = None
        self._hotkey_proxy = None
        self._drafter_nav_proxy = None
        self._drafter_toggle_proxy = None

    def _create_debug_panel(self, client_bridge):
        """Create a debug panel using Pyodide's .new() constructor."""
        return js.DebugPanel.new(DRAFTER_TAG_IDS["DEBUG"], client_bridge)

    def _create_url(self, href: str):
        """Create a URL object using Pyodide's .new() constructor."""
        return js.URL.new(href)

    def _create_form_data(self, form: Any, submitter: Any = None):
        """Create a FormData object using Pyodide's .new() constructor."""
        return js.FormData.new(form, submitter)

    def _wrap_event_handler(self, handler: Callable) -> Any:
        """Wrap an event handler with create_proxy to prevent automatic destruction."""
        return self._create_proxy(handler)

    def _cleanup_event_handler(self, handler: Any, proxy: Any = None) -> None:
        """Destroy a Pyodide proxy to prevent memory leaks."""
        if handler is not None and hasattr(handler, "destroy"):
            handler.destroy()

    def _handle_file_upload(self, file: Any, data: dict, key: str) -> None:
        """Handle file upload asynchronously in Pyodide (currently raises NotImplementedError)."""
        # TODO: Implement async file handling for Pyodide
        raise NotImplementedError(
            "Async file upload handling in Pyodide not implemented yet."
        )

    def _finalize_request(
        self, action: str, url: str, data: dict, dom_id: Optional[str]
    ) -> Request:
        return super()._finalize_request(action, url, data, dom_id)

    def mount_navigation(self, root: Any, on_navigation: Callable):
        """Override to properly store and clean up Pyodide proxies."""
        debug_log("pyodide_client.mount_navigation")
        # Clean up old proxies
        if self._click_proxy is not None:
            root.removeEventListener("click", self._click_proxy)
            self._cleanup_event_handler(self._click_proxy)
            self._click_proxy = None
        if self._submit_proxy is not None:
            form_root = js.document.getElementById(DRAFTER_TAG_IDS["FORM"])
            if form_root:
                form_root.removeEventListener("submit", self._submit_proxy)
            self._cleanup_event_handler(self._submit_proxy)
            self._submit_proxy = None

        # Call parent implementation which will use our wrapped methods
        super().mount_navigation(root, on_navigation)

        # Store the wrapped proxies
        self._click_proxy = self.click_handler
        self._submit_proxy = self.submit_handler

    def setup_events(
        self,
        handle_visit: Callable[[Request], Response],
        handle_toggle_frame: Callable,
        handle_debug_mode: Callable,
    ) -> None:
        """Override to properly store and clean up Pyodide proxies."""
        debug_log("pyodide_client.setup_events")

        # Clean up old proxies
        if self._popstate_proxy is not None:
            js.removeEventListener("popstate", self._popstate_proxy)
            self._cleanup_event_handler(self._popstate_proxy)
            self._popstate_proxy = None
        if self._drafter_nav_proxy is not None:
            js.removeEventListener("drafter-navigate", self._drafter_nav_proxy)
            self._cleanup_event_handler(self._drafter_nav_proxy)
            self._drafter_nav_proxy = None
        if self._drafter_toggle_proxy is not None:
            js.removeEventListener("drafter-toggle-frame", self._drafter_toggle_proxy)
            self._cleanup_event_handler(self._drafter_toggle_proxy)
            self._drafter_toggle_proxy = None

        self.navigation_func = handle_visit

        # Create and store popstate proxy
        self.popstate_listener = self._wrap_event_handler(self.handle_popstate)
        self._popstate_proxy = self.popstate_listener
        js.addEventListener("popstate", self._popstate_proxy)

        # Create and store Drafter event proxies
        self._drafter_nav_proxy = self._wrap_event_handler(
            lambda event: self.goto(event.detail)
        )
        self._drafter_toggle_proxy = self._wrap_event_handler(
            lambda event: handle_toggle_frame()
        )
        js.addEventListener("drafter-navigate", self._drafter_nav_proxy)
        js.addEventListener("drafter-toggle-frame", self._drafter_toggle_proxy)

        # Keyboard events
        self.register_hotkey("Q", handle_debug_mode)

    def register_hotkey(self, key_combo: str, callback: Callable[[], None]) -> None:
        """Override to properly store and clean up the hotkey proxy."""
        debug_log("pyodide_client.register_hotkey", key_combo)
        key = key_combo.lower().split("+")[-1].strip()

        def hotkey_handler(event: Any):
            event_key = event.key.lower() if hasattr(event, "key") else ""
            ctrl = getattr(event, "ctrlKey", False) or getattr(event, "metaKey", False)

            if ctrl and event_key in self.hotkey_events:
                current_time = int(time.time() * 1000)
                time_since_last = current_time - self.last_press_time

                if time_since_last < DOUBLE_PRESS_THRESHOLD:
                    debug_log("pyodide_client.hotkey_triggered", event_key)
                    event.preventDefault()
                    self.hotkey_events[event_key]()
                    self.last_press_time = 0
                else:
                    self.last_press_time = current_time

        self.hotkey_events[key] = callback
        if not self.hotkey_listener_ready:
            self._hotkey_proxy = self._wrap_event_handler(hotkey_handler)
            js.document.addEventListener("keydown", self._hotkey_proxy)
            self.hotkey_listener_ready = True
            debug_log("pyodide_client.hotkey_listener_registered")

    def _history_push_state(self, state: dict, title: str, url: str) -> None:
        """Push a new state to the browser history. Override in subclasses for runtime-specific handling."""
        js.history.pushState(self._to_js(state), title, url)


def debug_log(event_name: str, *args: Any) -> None:
    # try:
    #     event_bus = get_main_event_bus()
    #     event = TelemetryEvent(
    #         event_type=event_name,
    #         correlation=TelemetryCorrelation(),
    #         source="client",
    #     )
    #     event_bus.publish(event)
    # except Exception as e:
    #     print(f"[Drafter Client] Failed to log event {event_name} with args {args}, because of {e}")
    try:
        # Convert args to safe strings to avoid issues with destroyed PyProxies
        safe_args = []
        for arg in args:
            try:
                safe_args.append(str(arg))
            except:
                safe_args.append("<unprintable>")
        print(f"[Drafter Client] {event_name}: ", *safe_args)
    except Exception as e:
        print(f"[Drafter Client] {event_name} (failed to log args: {e})")


def console_log(event) -> None:
    try:
        repr_str = repr(event)
        print(f"[Drafter (Unhandled)] {repr_str}")
    except Exception as e:
        print(
            f"[Drafter/Internal] Failed to log event because of {e}\nOriginal Event:",
            event,
        )
