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


class TestSubmitterForFormData:
    """Only a submit button may be handed to FormData as the submitter.

    Any element can carry data-nav (a span written with RawHTML, say), and
    the browser's FormData constructor throws for anything that is not a
    submit button.
    """

    def click(self, monkeypatch, tag, element_type=None):
        manager, runtime = make_manager()
        captured = []
        monkeypatch.setattr(
            events_module,
            "get_all_event_data",
            lambda runtime, target, event, submitter, scope: captured.append(submitter)
            or [],
        )
        runtime.finish_promises.side_effect = lambda promises, callback: callback([])
        do_navigation = MagicMock()
        root = mount(manager, do_navigation)
        event, nav_element = make_click_event("guess", tag=tag, root=root)
        attributes = {"data-nav": "guess", "type": element_type}
        nav_element.getAttribute = attributes.get

        manager.click_handler(event)

        do_navigation.assert_called_once()
        return captured[0], nav_element

    def test_span_is_not_passed_as_the_submitter(self, monkeypatch):
        submitter, _ = self.click(monkeypatch, "SPAN")
        assert submitter is None

    def test_anchor_is_not_passed_as_the_submitter(self, monkeypatch):
        submitter, _ = self.click(monkeypatch, "A")
        assert submitter is None

    def test_plain_button_is_not_passed_as_the_submitter(self, monkeypatch):
        submitter, _ = self.click(monkeypatch, "BUTTON", "button")
        assert submitter is None

    def test_submit_button_is_the_submitter(self, monkeypatch):
        submitter, element = self.click(monkeypatch, "BUTTON", "submit")
        assert submitter is element

    def test_button_without_a_type_is_the_submitter(self, monkeypatch):
        submitter, element = self.click(monkeypatch, "BUTTON")
        assert submitter is element

    def test_submit_input_is_the_submitter(self, monkeypatch):
        submitter, element = self.click(monkeypatch, "INPUT", "submit")
        assert submitter is element

    def test_text_input_is_not_passed_as_the_submitter(self, monkeypatch):
        submitter, _ = self.click(monkeypatch, "INPUT", "text")
        assert submitter is None


class TestBrokenImages:
    """An image the browser cannot load used to fail without a word."""

    def mount_with_events(self, monkeypatch):
        manager, runtime = make_manager()
        reported = []
        monkeypatch.setattr(
            events_module,
            "report_bridge_warning",
            lambda event_type, message, source, details, **extra: reported.append(
                (event_type, message)
            ),
        )
        root = mount(manager, MagicMock())
        return manager, root, reported

    def image_error(self, source, tag="IMG"):
        event = MagicMock()
        event.target.tagName = tag
        event.target.getAttribute = lambda name: source if name == "src" else None
        return event

    def test_listener_catches_the_event_on_the_way_down(self, monkeypatch):
        manager, root, _ = self.mount_with_events(monkeypatch)

        # An image's error event does not bubble, so the listener has to
        # be a capturing one (third argument True).
        root.addEventListener.assert_any_call(
            "error", manager.image_error_handler, True
        )

    def test_missing_image_is_reported_by_name(self, monkeypatch):
        manager, _, reported = self.mount_with_events(monkeypatch)

        manager.image_error_handler(self.image_error("corgi.png"))

        assert reported == [
            ("client.image_load_failed", "The image 'corgi.png' could not be loaded.")
        ]

    def test_same_image_is_reported_once(self, monkeypatch):
        manager, _, reported = self.mount_with_events(monkeypatch)

        manager.image_error_handler(self.image_error("corgi.png"))
        manager.image_error_handler(self.image_error("corgi.png"))
        manager.image_error_handler(self.image_error("cat.png"))

        assert [message for _, message in reported] == [
            "The image 'corgi.png' could not be loaded.",
            "The image 'cat.png' could not be loaded.",
        ]

    def test_other_failed_elements_are_ignored(self, monkeypatch):
        manager, _, reported = self.mount_with_events(monkeypatch)

        manager.image_error_handler(self.image_error("clip.mp4", tag="VIDEO"))

        assert reported == []

    def test_long_data_address_is_shortened(self, monkeypatch):
        manager, _, reported = self.mount_with_events(monkeypatch)

        manager.image_error_handler(
            self.image_error("data:image/png;base64," + "A" * 5000)
        )

        (_, message) = reported[0]
        assert len(message) < 200
        assert "..." in message

    def test_remounting_replaces_the_listener(self, monkeypatch):
        manager, root, _ = self.mount_with_events(monkeypatch)
        first = manager.image_error_handler

        manager.mount_navigation(MagicMock())

        root.removeEventListener.assert_any_call("error", first, True)
        assert manager.image_error_handler is not first

    def test_teardown_releases_the_listener(self, monkeypatch):
        manager, _, _ = self.mount_with_events(monkeypatch)
        handler = manager.image_error_handler

        manager.teardown()

        manager.runtime.cleanup_event_handler.assert_any_call(handler)
        assert manager.image_error_handler is None

    def test_warning_has_friendly_steps(self):
        from drafter.data.error_explainer import ID_EXPLANATIONS

        title, message, steps = ID_EXPLANATIONS["client.image_load_failed"]

        assert title == "Image Did Not Load"
        assert "broken picture" in message
        assert any("capital letters" in step for step in steps)
