"""
Bridge functions for interacting with the web page in Skulpt.
"""

from dataclasses import dataclass, field
from drafter.data.channel import DEFAULT_CHANNEL_AFTER, DEFAULT_CHANNEL_BEFORE, Channel
from drafter.data.response import Response
from drafter.data.request import Request
from drafter.bridge.client import (
    update_site,
    console_log,
    setup_navigation,
    set_site_title,
)
from drafter.monitor.bus import get_main_event_bus
from drafter.monitor.telemetry import TelemetryEvent
from drafter.payloads.page import Page
from drafter.site import DRAFTER_TAG_IDS
from typing import Callable, Optional
import document  # type: ignore


@dataclass
class ClientBridge:
    channel_history: dict[str, set[str]] = field(default_factory=dict)
    
    def remove_page_specific_content(self) -> None:
        """
        Removes CSS and JS that were added for the previous page.
        This ensures that page-specific styles/scripts don't persist across navigation.
        """
        remove_page_content()

    def add_channel_content(self, channel: Optional[Channel], is_page_specific: bool = False) -> None:
        """
        Processes messages from a channel and adds them to the page.
        Supports 'script' and 'style' message kinds.
        
        :param channel: The channel containing messages to process.
        :param is_page_specific: If True, marks content as page-specific (will be removed on navigation).
        """
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
        self, response: Response, callback: Callable[[Request], None]
    ) -> bool:
        # Remove page-specific content from previous page before adding new content
        self.remove_page_specific_content()
        
        # Add new page-specific content
        self.add_channel_content(response.channels.get(DEFAULT_CHANNEL_BEFORE), is_page_specific=True)
        outcome = update_site(response, callback)
        self.add_channel_content(response.channels.get(DEFAULT_CHANNEL_AFTER), is_page_specific=True)
        return outcome

    def make_initial_request(self) -> Request:
        return Request(0, "load", "index", [], {}, {})

    def handle_telemetry_event(self, content: str) -> None:
        # print("Telemetry Event:", event.event_type, event.data)
        debug_info = document.getElementById(DRAFTER_TAG_IDS["DEBUG"])
        if debug_info:
            debug_info.innerHTML = content

    def console_log_events(self, event: TelemetryEvent) -> None:
        console_log(event)

    def setup_site(self, site_html: str, site_title: str) -> None:
        root_tag = document.getElementById(DRAFTER_TAG_IDS["ROOT"])
        root_tag.innerHTML = site_html
        set_site_title(site_title)

    def connect_to_event_bus(self) -> None:
        event_bus = get_main_event_bus()
        event_bus.subscribe("*", self.console_log_events)

    def setup_navigation(self, handle_visit: Callable[[Request], None]) -> None:
        setup_navigation(handle_visit)


def add_script(src: str, is_page_specific: bool = False) -> None:
    """
    Adds a script to the page.
    
    :param src: The script source URL or content.
    :param is_page_specific: If True, marks the script as page-specific (will be removed on navigation).
    """
    script = document.createElement("script")
    script.src = src
    if is_page_specific:
        script.setAttribute("data-drafter-page-specific", "true")
    head = document.getElementsByTagName("head")[0]
    head.appendChild(script)
    return script


def add_style(css: str, is_page_specific: bool = False) -> None:
    """
    Adds CSS content to the page by creating a style element.
    
    :param css: CSS content to add to the page.
    :param is_page_specific: If True, marks the style as page-specific (will be removed on navigation).
    """
    style = document.createElement("style")
    style.textContent = css
    if is_page_specific:
        style.setAttribute("data-drafter-page-specific", "true")
    head = document.getElementsByTagName("head")[0]
    head.appendChild(style)
    return style


def remove_page_content() -> None:
    """
    Removes all page-specific CSS and JS that were added for the previous page.
    This ensures that page-specific styles/scripts don't persist across navigation.
    """
    # Remove page-specific style tags
    styles = document.getElementsByTagName("style")
    styles_to_remove = []
    for i in range(len(styles)):
        style = styles[i]
        if hasattr(style, 'getAttribute') and style.getAttribute("data-drafter-page-specific") == "true":
            styles_to_remove.append(style)
    
    for style in styles_to_remove:
        if style.parentNode:
            style.parentNode.removeChild(style)
    
    # Remove page-specific script tags
    scripts = document.getElementsByTagName("script")
    scripts_to_remove = []
    for i in range(len(scripts)):
        script = scripts[i]
        if hasattr(script, 'getAttribute') and script.getAttribute("data-drafter-page-specific") == "true":
            scripts_to_remove.append(script)
    
    for script in scripts_to_remove:
        if script.parentNode:
            script.parentNode.removeChild(script)
