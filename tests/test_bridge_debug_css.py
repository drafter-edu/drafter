"""Tests for the global debug/deploy stylesheet swap.

Regression: hide_debug_information()/show_debug_information() are usually
called before start_server, so their UpdatedConfiguration telemetry is
queued and only replayed to the client bridge AFTER the initial render
already reflects the setting. swap_debug_mode used to be a blind toggle,
so the replayed event flipped the already-correct stylesheet to the wrong
one — hide showed the debug info and show hid it. The swap must therefore
be idempotent: it only changes the link when it does not match the
requested mode.
"""

import sys
from unittest.mock import MagicMock

# drafter.bridge requires a browser 'js' module; stub it for unit tests.
if not hasattr(sys.modules.get("js"), "document"):
    sys.modules["js"] = MagicMock()

from drafter.bridge.dom import swap_debug_mode
from drafter.site.site import DRAFTER_TAG_CLASSES

DEBUG_CLASS = DRAFTER_TAG_CLASSES["DEBUG_CSS"]
NON_DEBUG_CLASS = DRAFTER_TAG_CLASSES["NON_DEBUG_CSS"]


class FakeClassList:
    def __init__(self, *classes):
        self.classes = set(classes)

    def add(self, name):
        self.classes.add(name)

    def remove(self, name):
        self.classes.discard(name)


class FakeLink:
    """Minimal stand-in for a connected <link> element."""

    def __init__(self, href, css_class):
        self.attributes = {"href": href}
        self.classList = FakeClassList(css_class)

    def getAttribute(self, name):
        return self.attributes.get(name)

    def setAttribute(self, name, value):
        self.attributes[name] = value


class FakeRoot:
    """Resolves the class-based querySelector lookups swap_debug_mode makes."""

    def __init__(self, link):
        self.link = link

    def querySelector(self, selector):
        css_class = selector.removeprefix("link.")
        if css_class in self.link.classList.classes:
            return self.link
        return None


def debug_link(href="assets/css/drafter_debug.css"):
    return FakeLink(href, DEBUG_CLASS)


def non_debug_link(href="assets/css/drafter_deploy.css"):
    return FakeLink(href, NON_DEBUG_CLASS)


class TestSwapDebugMode:
    def test_debug_link_swaps_to_deploy_when_hiding(self):
        link = debug_link()
        swap_debug_mode(FakeRoot(link), in_debug_mode=False)

        assert link.getAttribute("href") == "assets/css/drafter_deploy.css"
        assert NON_DEBUG_CLASS in link.classList.classes
        assert DEBUG_CLASS not in link.classList.classes

    def test_deploy_link_swaps_to_debug_when_showing(self):
        link = non_debug_link()
        swap_debug_mode(FakeRoot(link), in_debug_mode=True)

        assert link.getAttribute("href") == "assets/css/drafter_debug.css"
        assert DEBUG_CLASS in link.classList.classes
        assert NON_DEBUG_CLASS not in link.classList.classes

    def test_debug_link_is_untouched_when_showing(self):
        # The replayed show_debug_information() event must not flip an
        # already-debug page to deploy.
        link = debug_link()
        swap_debug_mode(FakeRoot(link), in_debug_mode=True)

        assert link.getAttribute("href") == "assets/css/drafter_debug.css"
        assert DEBUG_CLASS in link.classList.classes

    def test_deploy_link_is_untouched_when_hiding(self):
        # The replayed hide_debug_information() event must not flip an
        # already-deploy page back to debug.
        link = non_debug_link()
        swap_debug_mode(FakeRoot(link), in_debug_mode=False)

        assert link.getAttribute("href") == "assets/css/drafter_deploy.css"
        assert NON_DEBUG_CLASS in link.classList.classes

    def test_href_prefix_is_preserved(self):
        link = debug_link("https://cdn.example.com/v2/css/drafter_debug.css")
        swap_debug_mode(FakeRoot(link), in_debug_mode=False)

        assert (
            link.getAttribute("href")
            == "https://cdn.example.com/v2/css/drafter_deploy.css"
        )

    def test_missing_links_are_a_safe_no_op(self):
        root = MagicMock()
        root.querySelector.return_value = None
        swap_debug_mode(root, in_debug_mode=False)
        swap_debug_mode(root, in_debug_mode=True)
