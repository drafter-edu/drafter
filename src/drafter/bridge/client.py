"""
Client module for interacting with the browser DOM using the js package.
The ClientBridge uses this to manipulate the page content and handle navigation.
This module works with both Skulpt and Pyodide by using the unified `js` module interface.
"""

import json
from drafter.config.client_server import ClientServerConfiguration
from drafter.data.response import Response
from drafter.data.request import Request
from drafter.monitor.events.config import UpdatedConfigurationEvent
from drafter.site.site import DRAFTER_TAG_IDS, DRAFTER_TAG_CLASSES
from drafter.monitor.telemetry import TelemetryEvent, TelemetryCorrelation
from drafter.helpers.utils import is_skulpt, is_pyodide
from drafter.components.page_content import Component
from typing import Callable, Optional, Any
from dataclasses import dataclass, field
import time
import js

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


def replaceHTML(tag: Any, html: str):
    # Save current scroll position
    scroll_top = js.scrollY
    scroll_left = js.scrollX
    # Replace content
    r = js.document.createRange()
    r.selectNode(tag)
    fragment = r.createContextualFragment(html)
    tag.replaceChildren(fragment)
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

    def goto(self, url: str, form_data: Any = None, action="system", arguments=None):
        if self.navigation_func is None:
            raise RuntimeError("Navigation function not set in Client.")
        return self.initiate_request(url, form_data, True, action, arguments)

    def navigate(self, nav_event: NavEvent):
        return self.initiate_request(
            nav_event.url, nav_event.data, True, nav_event.kind, nav_event.arguments
        )

    def setup_debug_menu(self, client_bridge):
        debug_log("client.setup_debug_menu")
        try:
            self.debug_panel = js.DebugPanel(DRAFTER_TAG_IDS["DEBUG"], client_bridge)
        except Exception as e:
            print(f"[Drafter Client] Failed to set up debug menu because of {e}")
            raise e

    def handle_event(self, event: dict) -> bool:
        debug_log("client.handle_event", event)
        if event["event_type"] == UpdatedConfigurationEvent.event_type:
            if event.get("data", {}).get("key") == "framed":
                self.toggle_frame()
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
        )
        self.request_count += 1
        return new_request

    def make_initial_request(self) -> Request:
        return Request(0, "page_load", "index", {}, {})

    def make_request(
        self,
        url: str,
        form_data: Any = None,
        action: str = "submit",
        arguments: Optional[list[str]] = None,
    ) -> Request:
        data = {}
        if is_pyodide():
            file_promise_chain = js.Promise.resolve()
        else:
            file_promise_chain = None
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
                    if is_skulpt():
                        get_file_skulpt(value, data, key)
                    elif is_pyodide():
                        # Note: This is async in Pyodide, so we need a callback to continue processing
                        # TODO: Figure out what this logic should actually be
                        def callback(file_data):
                            if file_promise_chain is None:
                                return
                            file_promise_chain.then(lambda *args: file_data)

                        get_file_pyodide(value, data, key, callback)
        # Add arguments to the data dict
        for i, arg in enumerate(reversed(arguments or [])):
            # TODO: Handle both of these more elegantly in case they are corrupted in some way
            parsed = json.loads(arg)
            data.update(parsed)

        if is_pyodide():
            raise NotImplementedError(
                "Async request handling in Pyodide not implemented yet."
            )
        elif is_skulpt():
            new_request = Request(self.request_count, action, url, data, {})
            self.request_count += 1
            return new_request
        else:
            raise RuntimeError("Unknown web runtime.")

    def add_to_history(self, request: Request):
        url = request.url
        request_id = request.id
        state = {
            "request_id": request_id,
            "url": url,
            # TODO: Track parameters as well
        }
        full_url = get_full_url()
        js.document.title = f"{self.site_title} - {url}"
        full_url.searchParams.set("route", url)
        js.history.pushState(state, "", full_url.toString())
        debug_log("client.add_to_history", state, request)

    def initiate_request(
        self,
        url: str,
        form_data: Any = None,
        remember=True,
        action="submit",
        arguments: Optional[list[str]] = None,
    ):
        if self.navigation_func is None:
            raise RuntimeError("Navigation function not set in Client.")
        debug_log("client.initiate_request", url, form_data, remember, action)
        request = self.make_request(url, form_data, action, arguments)
        if remember:
            self.add_to_history(request)
        next_visit = self.navigation_func(request)
        return next_visit

    def mount_navigation(self, root: Any, on_navigation: Callable):
        debug_log("client.mount_navigation", root, on_navigation)
        # Clean up old handlers if they exist
        if self.click_handler is not None:
            root.removeEventListener("click", self.click_handler)

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

                # Get the arguments from the clicked element and its parents
                arguments = get_attribute_recursively(
                    target, Component.DRAFTER_DATA_ARGUMENT_NAME
                )

                # Get the form element
                form = js.document.getElementById(DRAFTER_TAG_IDS["FORM"])
                if form:
                    is_anchor = nearest_nav_link.tagName.lower() == "a"
                    if is_pyodide():
                        form_data = js.FormData.new(
                            form, None if is_anchor else nearest_nav_link
                        )
                    elif is_skulpt():
                        form_data = js.FormData(
                            form, None if is_anchor else nearest_nav_link
                        )
                    else:
                        raise RuntimeError("Unknown web runtime.")
                    nav_event = NavEvent(
                        kind="link",
                        url=name,
                        data=form_data,
                        submitter=nearest_nav_link,
                        arguments=arguments,
                    )
                    return on_navigation(nav_event)
                else:
                    raise RuntimeError("Form element not found for navigation.")

        def submit_handler(event: Any):
            debug_log("client.form_submit_handler", event)
            event.preventDefault()
            # Figure out submitter
            if "submitter" in event:
                submitter = event.submitter
            else:
                submitter = None
            # Get the form data
            if is_pyodide():
                form_data = js.FormData.new(event.target, submitter)
            elif is_skulpt():
                form_data = js.FormData(event.target, submitter)
            else:
                raise RuntimeError("Unknown web runtime.")
            # Handle arguments
            # Get the arguments from the clicked element and its parents
            arguments = get_attribute_recursively(
                event.target, Component.DRAFTER_DATA_ARGUMENT_NAME
            )
            # Figure out URL
            if submitter is not None and "getAttribute" in submitter:
                url = submitter.getAttribute("formaction")
            elif "action" in form_root:
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
            )
            return on_navigation(nav_event)

        self.click_handler = handle_click
        self.submit_handler = submit_handler
        root.addEventListener("click", self.click_handler)

        form_root = js.document.getElementById(DRAFTER_TAG_IDS["FORM"])
        if form_root:
            # TODO: Check if this removal is necessary
            # if self.submit_handler is not None:
            #     form_root.removeEventListener("submit", self.submit_handler)
            form_root.addEventListener("submit", self.submit_handler)
        else:
            raise RuntimeError("Form root element not found for mounting navigation.")
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
            element = js.document.getElementById(DRAFTER_TAG_IDS["BODY"])
            if not element:
                raise RuntimeError("Body element not found in document.")
            replaceHTML(element, body)

            debug_log("client.update_site_complete", response)
            self.mount_navigation(element, self.navigate)

        return True

    def setup_events(
        self, handle_visit: Callable[[Request], Response], handle_toggle_frame: Callable
    ) -> None:
        debug_log("client.setup_events")
        self.navigation_func = handle_visit

        if self.popstate_listener is not None:
            # TODO: Handle pyodide separately, if needed
            js.removeEventListener("popstate", self.popstate_listener)

        self.popstate_listener = self.handle_popstate
        js.addEventListener("popstate", self.handle_popstate)

        js.addEventListener("drafter-navigate", lambda event: self.goto(event.detail))
        js.addEventListener("drafter-toggle-frame", lambda event: handle_toggle_frame())

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
            full_url = get_full_url()
            full_url.searchParams.set("route", url)
            js.history.replaceState(event.state, "", full_url.toString())
            self.initiate_request(url, None, False, "back", None)
        else:
            debug_log("client.handle_popstate_no_state_or_request_id", event)
            js.document.title = self.site_title
            full_url = get_full_url()
            full_url.searchParams.delete("route")
            js.history.replaceState({}, "", full_url.toString())
            self.initiate_request("index", None, False, "back", None)

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
                self.last_press_time = current_time

        self.hotkey_events[key] = callback
        if not self.hotkey_listener_ready:
            js.document.addEventListener("keydown", hotkey_handler)
            self.hotkey_listener_ready = True
            debug_log("client.hotkey_listener_registered")


def get_full_url():
    if is_pyodide():
        return js.URL.new(js.location.href)
    elif is_skulpt():
        return js.URL(js.location.href)
    else:
        raise RuntimeError("Unknown web runtime.")


def get_file_skulpt(file: Any, data: Any, key: str):
    buffer = file.arrayBuffer()
    raw_bytes = js.Uint8Array(buffer)
    content = bytes(raw_bytes)
    # TODO: Handle TypeError, RangeError, and any other errors thrown during this process
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


def get_file_pyodide(file: Any, data: Any, key: str, callback):
    def handle_buffer(buffer: Any):
        raw_bytes = js.Uint8Array.new(buffer)
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
        callback()

    file.arrayBuffer().then(handle_buffer)


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
    print(f"[Drafter Client] {event_name}: ", *args)


def console_log(event) -> None:
    try:
        repr_str = repr(event)
        print(f"[Drafter (Unhandled)] {repr_str}")
    except Exception as e:
        print(
            f"[Drafter/Internal] Failed to log event because of {e}\nOriginal Event:",
            event,
        )
