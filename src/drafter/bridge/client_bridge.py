"""
Bridge functions for interacting with the web page in Skulpt.
"""

from dataclasses import dataclass, field
from drafter.config.client_server import ClientServerConfiguration
from drafter.data.channel import DEFAULT_CHANNEL_AFTER, DEFAULT_CHANNEL_BEFORE, Channel
from drafter.data.response import Response
from drafter.data.request import Request
from drafter.bridge.client import (
    Client,
    PyodideClient,
    console_log,
)
from drafter.bridge.helpers import (
    add_script,
    add_style,
    add_header,
    add_link,
    remove_page_content,
    remove_existing_theme,
)
from drafter.monitor.telemetry import TelemetryEvent
from drafter.site.initial_site_data import InitialSiteData
from drafter.site.site import (
    DRAFTER_TAG_IDS,
    DRAFTER_TAG_CLASSES,
    SITE_HTML_SHADOW_DOM_TEMPLATE,
)
from drafter.helpers.utils import is_pyodide
from typing import Callable, Optional
import js

document = js.document  # type: ignore


@dataclass
class ClientBridge:
    client: Client
    channel_history: dict[str, set[str]] = field(default_factory=dict)
    redirect_loop_stack: list[str] = field(default_factory=list)

    def __init__(self, configuration: ClientServerConfiguration):
        # Use PyodideClient for Pyodide runtime, otherwise use base Client (Skulpt)
        if is_pyodide():
            self.client = PyodideClient(
                configuration.root_element_id, configuration.root_element_id
            )
        else:
            self.client = Client(
                configuration.root_element_id, configuration.root_element_id
            )
        self.channel_history = {}
        self.redirect_loop_stack = []

    def get_root(self):
        # TODO: Handle this correctly for shadowdom
        return document.getElementById(self.client.root_id)

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

        :param channel: The channel containing messages to process.
        :param is_page_specific: If True, marks content as page-specific (will be removed on navigation).
        """
        # console_log("Message Received:" + repr(channel))
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
                    add_script(root, message.content, is_page_specific=is_page_specific)
                elif message.kind == "style":
                    add_style(root, message.content, is_page_specific=is_page_specific)

    def handle_response(
        self, response: Response, callback: Callable[[Request], Response]
    ) -> bool:
        # Remove page-specific content from previous page before adding new content
        self.remove_page_specific_content()

        # Add new page-specific content
        self.add_channel_content(
            response.channels.get(DEFAULT_CHANNEL_BEFORE), is_page_specific=True
        )
        outcome = self.client.update_site(response, callback)
        self.add_channel_content(
            response.channels.get(DEFAULT_CHANNEL_AFTER), is_page_specific=True
        )
        if response.payload.is_redirect():
            self.handle_redirect(response, callback)
        return outcome

    def clear_redirect_stack(self) -> None:
        """
        Clears the redirect loop stack to prevent false positives on future redirects.
        """
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
        new_request = self.client.make_redirect_request_from_response(response)
        callback(new_request)
        self.redirect_loop_stack.pop()

    def make_initial_request(self) -> Request:
        return self.client.make_initial_request()

    def handle_telemetry_event(self, event: TelemetryEvent) -> None:
        handled = self.client.handle_event(event.to_json())
        if not handled:
            console_log(event)

    def console_log_events(self, event: TelemetryEvent) -> None:
        console_log(event)

    def setup_site(self, initial_site_data: InitialSiteData) -> None:
        try:
            true_root_id = self.client._true_root_id
            true_root = document.getElementById(true_root_id)
            self.client.set_site_title(initial_site_data.site_title)
            remove_existing_theme(true_root, DRAFTER_TAG_CLASSES["THEME"])

            # Set up shadow DOM if enabled
            if initial_site_data.use_shadow_dom:
                true_root.innerHTML = SITE_HTML_SHADOW_DOM_TEMPLATE
                shadow_host = document.getElementById(DRAFTER_TAG_IDS["SHADOW_HOST"])
                if not shadow_host:
                    raise ValueError("Shadow host element not found in the document.")
                shadow_root = shadow_host.attachShadow({"mode": "open"})
                shadow_root.innerHTML = initial_site_data.site_html
                root = shadow_root

                # Move styles into shadow DOM
                for css in initial_site_data.additional_css:
                    self._add_link_to_shadow(
                        shadow_root, css, with_class=DRAFTER_TAG_CLASSES["THEME"]
                    )
                for style in initial_site_data.additional_style:
                    self._add_style_to_shadow(
                        shadow_root, style, with_class=DRAFTER_TAG_CLASSES["THEME"]
                    )
            else:
                true_root.innerHTML = initial_site_data.site_html
                root = true_root

                # Normal mode without shadow DOM
                for css in initial_site_data.additional_css:
                    add_link(root, css, with_class=DRAFTER_TAG_CLASSES["THEME"])
                for style in initial_site_data.additional_style:
                    add_style(root, style, with_class=DRAFTER_TAG_CLASSES["THEME"])
            for js_code in initial_site_data.additional_js:
                add_script(root, js_code, with_class=DRAFTER_TAG_CLASSES["THEME"])
            for header in initial_site_data.additional_header:
                add_header(root, header)

            self.client.setup_debug_menu(self)
        except Exception as e:
            console_log(f"Error setting up site: {e}")
            raise e

    def setup_events(
        self,
        handle_visit: Callable[[Request], Response],
        handle_toggle_frame: Callable,
        handle_debug_mode: Callable,
    ) -> None:
        self.client.setup_events(handle_visit, handle_toggle_frame, handle_debug_mode)

    def register_hotkey(self, keyCombo: str, callback: Callable[[], None]) -> None:
        self.client.register_hotkey(keyCombo, callback)

    def _add_style_to_shadow(self, shadow_root, css: str, with_class: str = "") -> None:
        """
        Adds CSS content to the shadow DOM by creating a style element.

        :param shadow_root: The shadow root to append the style to.
        :param css: CSS content to add.
        :param with_class: Optional class name to add to the style element.
        """
        style = document.createElement("style")
        style.innerHTML = css
        if with_class:
            style.setAttribute("class", with_class)
        shadow_root.appendChild(style)

    def _add_link_to_shadow(
        self, shadow_root, css_link: str, with_class: str = ""
    ) -> None:
        """
        Adds a link element to the shadow DOM for CSS files.

        :param shadow_root: The shadow root to append the link to.
        :param css_link: The href of the CSS file to add.
        :param with_class: Optional class name to add to the link element.
        """
        link = document.createElement("link")
        link.setAttribute("type", "text/css")
        link.setAttribute("rel", "stylesheet")
        link.setAttribute("href", css_link)
        if with_class:
            link.setAttribute("class", with_class)
        shadow_root.appendChild(link)
