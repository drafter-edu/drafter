"""Tests for the bridge's delegated click navigation (events.py).

External URLs on Link/Button components must leave the Drafter app (native
anchor navigation, or a browser-level location change for buttons) instead
of being dispatched to the router as if they were route names.
"""

import sys
from unittest.mock import MagicMock

# drafter.bridge requires a browser 'js' module; stub it for unit tests.
if not hasattr(sys.modules.get("js"), "document"):
    sys.modules["js"] = MagicMock()

import drafter.bridge.events as events_module
from drafter.bridge.events import EventManager


def make_manager():
    """EventManager with an identity wrap so handlers stay plain functions."""
    runtime = MagicMock()
    runtime.wrap_event_handler = lambda handler: handler
    manager = EventManager(runtime)
    return manager, runtime


def make_click_event(nav_value, tag="a", contained=True, root=None):
    """A fake click event whose target resolves to a data-nav element."""
    nav_element = MagicMock()
    nav_element.getAttribute = lambda name: nav_value if name == "data-nav" else None
    nav_element.tagName = tag
    nav_element.id = "el-1"
    event = MagicMock()
    event.target.closest.return_value = nav_element
    if root is not None:
        root.contains.return_value = contained
    return event, nav_element


def mount(manager, do_navigation):
    root = MagicMock()
    manager.scope = MagicMock()
    manager.scope.querySelector.return_value = root
    manager.mount_event_handlers = MagicMock()
    manager.mount_navigation(do_navigation)
    return root


class TestExternalLinks:
    def test_external_anchor_uses_native_navigation(self):
        manager, runtime = make_manager()
        do_navigation = MagicMock()
        root = mount(manager, do_navigation)
        event, _ = make_click_event("https://example.com/docs", tag="A", root=root)

        manager.click_handler(event)

        # Default not prevented: the browser follows the href itself.
        event.preventDefault.assert_not_called()
        do_navigation.assert_not_called()
        runtime.finish_promises.assert_not_called()

    def test_external_button_navigates_the_browser(self):
        manager, runtime = make_manager()
        do_navigation = MagicMock()
        root = mount(manager, do_navigation)
        event, _ = make_click_event("https://example.com/", tag="BUTTON", root=root)

        manager.click_handler(event)

        # Default prevented (no form submit), and the browser is pointed
        # at the external URL directly.
        event.preventDefault.assert_called_once()
        assert runtime.context.window.location.href == "https://example.com/"
        do_navigation.assert_not_called()

    def test_internal_route_still_dispatches(self, monkeypatch):
        manager, runtime = make_manager()
        do_navigation = MagicMock()
        monkeypatch.setattr(
            events_module, "get_all_event_data", lambda *args, **kwargs: []
        )
        runtime.finish_promises.side_effect = lambda promises, callback: callback([])
        root = mount(manager, do_navigation)
        event, _ = make_click_event("guess", tag="BUTTON", root=root)

        manager.click_handler(event)

        event.preventDefault.assert_called_once()
        do_navigation.assert_called_once()
        request = do_navigation.call_args.args[0]
        assert request.url == "guess"
        assert request.action == "link"

    def test_http_only_prefixes_count_as_external(self, monkeypatch):
        # A route named e.g. "httpsomething" is not external.
        manager, runtime = make_manager()
        do_navigation = MagicMock()
        monkeypatch.setattr(
            events_module, "get_all_event_data", lambda *args, **kwargs: []
        )
        runtime.finish_promises.side_effect = lambda promises, callback: callback([])
        root = mount(manager, do_navigation)
        event, _ = make_click_event("httpsomething", tag="A", root=root)

        manager.click_handler(event)

        do_navigation.assert_called_once()
