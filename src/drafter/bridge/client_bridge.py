"""
Bridge functions for interacting with the web page in Skulpt.
"""

from dataclasses import dataclass, field
from drafter.data.channel import DEFAULT_CHANNEL_AFTER, DEFAULT_CHANNEL_BEFORE, Channel
from drafter.data.response import Response
from drafter.data.request import Request
from drafter.bridge.client import (
    Client,
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
from drafter.site.site import DRAFTER_TAG_IDS, DRAFTER_TAG_CLASSES
from typing import Callable, Optional
import js

document = js.document  # type: ignore


@dataclass
class ClientBridge:
    client: Client
    channel_history: dict[str, set[str]] = field(default_factory=dict)
    redirect_loop_stack: list[str] = field(default_factory=list)

    def __init__(self):
        self.client = Client()
        self.channel_history = {}
        self.redirect_loop_stack = []

    def remove_page_specific_content(self) -> None:
        """
        Removes CSS and JS that were added for the previous page.
        This ensures that page-specific styles/scripts don't persist across navigation.
        """
        remove_page_content()

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
            for message in channel.messages:
                if message.sigil is not None:
                    if channel.name not in self.channel_history:
                        self.channel_history[channel.name] = set()
                    if message.sigil in self.channel_history[channel.name]:
                        continue
                    self.channel_history[channel.name].add(message.sigil)
                if message.kind == "script":
                    # TODO: Handle errors while executing this script
                    add_script(message.content, is_page_specific=is_page_specific)
                elif message.kind == "style":
                    add_style(message.content, is_page_specific=is_page_specific)

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
        self.client.handle_event(event.to_json())
        # print("Telemetry Event:", event.event_type, event.data)
        # debug_info = document.getElementById(DRAFTER_TAG_IDS["DEBUG"])
        # if debug_info:
        #    debug_info.innerHTML = content

    def console_log_events(self, event: TelemetryEvent) -> None:
        console_log(event)

    def setup_site(self, initial_site_data: InitialSiteData) -> None:
        root_tag = document.getElementById(DRAFTER_TAG_IDS["ROOT"])
        root_tag.innerHTML = initial_site_data.site_html
        self.client.set_site_title(initial_site_data.site_title)
        remove_existing_theme(DRAFTER_TAG_CLASSES["THEME"])
        for css in initial_site_data.additional_css:
            add_link(css, with_class=DRAFTER_TAG_CLASSES["THEME"])
        for js_code in initial_site_data.additional_js:
            add_script(js_code, with_class=DRAFTER_TAG_CLASSES["THEME"])
        for style in initial_site_data.additional_style:
            add_style(style, with_class=DRAFTER_TAG_CLASSES["THEME"])
        for header in initial_site_data.additional_header:
            add_header(header)

    def setup_debug_menu(self) -> None:
        self.client.setup_debug_menu(self)

    def setup_navigation(self, handle_visit: Callable[[Request], Response]) -> None:
        self.client.setup_navigation(handle_visit)

    def register_hotkey(self, keyCombo: str, callback: Callable[[], None]) -> None:
        self.client.register_hotkey(keyCombo, callback)
