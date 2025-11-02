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

    def add_scripts(self, channel: Optional[Channel]) -> None:
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
                    add_script(message.content)

    def handle_response(
        self, response: Response, callback: Callable[[Request], None]
    ) -> bool:
        self.add_scripts(response.channels.get(DEFAULT_CHANNEL_BEFORE))
        outcome = update_site(response, callback)
        self.add_scripts(response.channels.get(DEFAULT_CHANNEL_AFTER))
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


def add_script(src: str) -> None:
    script = document.createElement("script")
    script.src = src
    head = document.getElementsByTagName("head")[0]
    head.appendChild(script)
    return script
