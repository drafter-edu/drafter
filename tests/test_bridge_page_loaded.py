"""Tests for when the bridge dispatches the drafter-page-loaded event.

Auto-play audio and media components (Tone, Melody, Sound, Audio, Video)
wait for this event before playing. It used to fire only for full page
loads, so a component inserted by a Fragment (like a piano key returning
`Fragment([Tone(note, auto_play=True)], target="#sound_area")`) waited
forever and never made a sound.
"""

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

# drafter.bridge requires a browser 'js' module; stub it for unit tests.
if not hasattr(sys.modules.get("js"), "document"):
    sys.modules["js"] = MagicMock()

from drafter.bridge.client_bridge import ClientBridge
from drafter.bridge.events import DRAFTER_PAGE_LOADED_EVENT, EventManager
from drafter.config.client_server import ClientServerConfiguration
from drafter.payloads.target import DEFAULT_BODY_TARGET, Target


def make_bridge(body_replaced: bool) -> ClientBridge:
    """A ClientBridge with its DOM collaborators replaced by mocks.

    `SiteRenderer.update_site` returns True only when it replaced the page
    body; injecting a Fragment into another element returns False.
    """
    bridge = ClientBridge.__new__(ClientBridge)
    bridge.configuration = ClientServerConfiguration()
    bridge.debug_panel = None
    bridge.site_renderer = MagicMock()
    bridge.site_renderer.update_site.return_value = body_replaced
    bridge.navigator = MagicMock()
    bridge.events = MagicMock()
    return bridge


def make_response(target: Target | None, body: str | None = "<p>hi</p>"):
    return SimpleNamespace(
        url="play_note",
        request_id=7,
        id=3,
        target=target,
        body=body,
        payload=SimpleNamespace(is_redirect=lambda: False),
    )


class TestHandleResponseDispatch:
    @pytest.mark.parametrize("target", [None, DEFAULT_BODY_TARGET])
    def test_full_page_load_dispatches_non_fragment_event(self, target):
        bridge = make_bridge(body_replaced=True)
        bridge.handle_response(make_response(target), MagicMock())
        bridge.events.dispatch_page_loaded.assert_called_once_with(
            route="play_note", request_id=7, response_id=3, fragment=False
        )

    def test_fragment_dispatches_fragment_event(self):
        bridge = make_bridge(body_replaced=False)
        bridge.handle_response(make_response(Target(id="sound_area")), MagicMock())
        bridge.events.dispatch_page_loaded.assert_called_once_with(
            route="play_note", request_id=7, response_id=3, fragment=True
        )
        # Fragments still leave the page's navigation handlers alone.
        bridge.events.mount_navigation.assert_not_called()

    def test_response_without_content_dispatches_nothing(self):
        bridge = make_bridge(body_replaced=False)
        bridge.handle_response(make_response(None, body=None), MagicMock())
        bridge.events.dispatch_page_loaded.assert_not_called()


class TestDispatchPageLoadedDetail:
    @pytest.mark.parametrize("fragment", [False, True])
    def test_detail_reports_fragment_flag(self, fragment):
        runtime = MagicMock()
        manager = EventManager(runtime)
        manager.dispatch_page_loaded(
            route="index", request_id=1, response_id=0, fragment=fragment
        )
        runtime.create_custom_event.assert_called_once_with(
            DRAFTER_PAGE_LOADED_EVENT,
            {"route": "index", "requestId": 1, "responseId": 0, "fragment": fragment},
        )
        runtime.dispatch_window_event.assert_called_once_with(
            runtime.create_custom_event.return_value
        )
