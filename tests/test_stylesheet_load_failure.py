"""Tests for noticing a stylesheet that fails to load (drafter-edu/drafter#232).

A `<link>` fires an `error` event when its file cannot be fetched. Before
this, a missing theme file left the site unstyled with no explanation (the
2.0.2 release fixed exactly such a case). The site renderer now listens on
every stylesheet link it creates and, on failure, raises a site-level
warning and shows a dismissible notice at the top of the site.
"""

import sys
from unittest.mock import MagicMock

import pytest

# drafter.bridge requires a browser 'js' module; stub it for unit tests.
if not hasattr(sys.modules.get("js"), "document"):
    sys.modules["js"] = MagicMock()

from drafter.bridge.dom import STYLESHEET_NOTICE_TEXT, show_stylesheet_notice
from drafter.client_server.client_server import ClientServer
from drafter.client_server.commands import (
    get_main_event_bus,
    get_main_server,
    set_main_server,
)
from drafter.data.error_explainer import ID_EXPLANATIONS
from drafter.site.site import DRAFTER_TAG_IDS
from tests.test_site_renderer_link_reuse import (
    get_shadow_root,
    make_document_with_root,
    make_renderer,
    make_site_data,
    theme_links,
)

NOTICE_ID = DRAFTER_TAG_IDS["STYLESHEET_NOTICE"]
FAILURE_ID = "client.stylesheet_load_failed"
THEME_CSS = "assets/css/sakura.css"
BASE_CSS = "assets/css/drafter_base.css"


@pytest.fixture
def warnings():
    """Collect stylesheet-failure warnings published during a test."""
    previous = get_main_server()
    set_main_server(ClientServer("STYLESHEET_TEST_SERVER"))
    events = []
    bus = get_main_event_bus()
    subscription = bus.subscribe("*", events.append)
    yield lambda: [event for event in events if event.kind == FAILURE_ID]
    bus.unsubscribe(subscription)
    set_main_server(previous)


def set_up_site(use_shadow_dom: bool):
    """Render a site with two stylesheets; return (scope, their links)."""
    document = make_document_with_root()
    renderer = make_renderer(document)
    renderer.setup(
        make_site_data(css_urls=(BASE_CSS, THEME_CSS), use_shadow_dom=use_shadow_dom)
    )
    link_home = get_shadow_root(document) if use_shadow_dom else document.head
    return renderer, renderer.scope, theme_links(link_home)


def notice_in(scope):
    return scope.querySelector("#" + NOTICE_ID)


def listed_files(notice) -> list[str]:
    return [item.textContent for item in notice.querySelectorAll("li")]


class TestIdRegistry:
    def test_notice_id_follows_the_internal_naming_convention(self):
        assert NOTICE_ID.startswith("drafter-")
        assert NOTICE_ID.endswith("--")


@pytest.mark.parametrize("use_shadow_dom", [False, True], ids=["head", "shadow"])
class TestFailedStylesheet:
    def test_no_notice_while_everything_loads(self, warnings, use_shadow_dom):
        _renderer, scope, _links = set_up_site(use_shadow_dom)

        assert notice_in(scope) is None
        assert warnings() == []

    def test_failure_raises_a_site_level_warning(self, warnings, use_shadow_dom):
        _renderer, _scope, links = set_up_site(use_shadow_dom)

        links[1].dispatch("error")

        (warning,) = warnings()
        assert warning.metadata.level == "warning"
        assert THEME_CSS in warning.error.message
        # No request id: the debug panel keeps site-level problems visible
        # across pages instead of clearing them on the next navigation.
        assert warning.error.context.request_id is None
        assert warning.error.friendly_title == "Styling Did Not Load"
        assert warning.error.friendly_steps

    def test_failure_shows_a_notice_naming_the_file(self, warnings, use_shadow_dom):
        _renderer, scope, links = set_up_site(use_shadow_dom)

        links[1].dispatch("error")

        notice = notice_in(scope)
        assert notice is not None
        assert scope.firstChild is notice
        assert notice.getAttribute("role") == "status"
        assert STYLESHEET_NOTICE_TEXT in [
            child.textContent for child in notice.children
        ]
        assert listed_files(notice) == [THEME_CSS]

    def test_notice_can_be_dismissed_without_python(self, warnings, use_shadow_dom):
        _renderer, scope, links = set_up_site(use_shadow_dom)

        links[0].dispatch("error")

        (button,) = notice_in(scope).querySelectorAll("button")
        assert button.getAttribute("type") == "button"
        assert button.getAttribute("onclick") == "this.parentNode.remove()"

    def test_second_failure_joins_the_same_notice(self, warnings, use_shadow_dom):
        _renderer, scope, links = set_up_site(use_shadow_dom)

        links[0].dispatch("error")
        links[1].dispatch("error")

        assert len(scope.querySelectorAll("#" + NOTICE_ID)) == 1
        assert listed_files(notice_in(scope)) == [BASE_CSS, THEME_CSS]
        assert len(warnings()) == 2

    def test_theme_switch_watches_the_new_stylesheet(self, warnings, use_shadow_dom):
        renderer, scope, _links = set_up_site(use_shadow_dom)
        document = scope.ownerDocument

        renderer.refresh_theme_css([BASE_CSS, "assets/css/missing-theme.css"])
        document.created_links[-1].dispatch("error")

        assert listed_files(notice_in(scope)) == ["assets/css/missing-theme.css"]
        assert len(warnings()) == 1


class TestShowStylesheetNotice:
    def test_same_file_is_listed_once(self):
        document = make_document_with_root()
        scope = document.body

        show_stylesheet_notice(scope, THEME_CSS)
        show_stylesheet_notice(scope, THEME_CSS)

        assert listed_files(notice_in(scope)) == [THEME_CSS]

    def test_file_name_is_text_never_markup(self):
        document = make_document_with_root()
        scope = document.body
        hostile = '"><img src=x onerror=alert(1)>.css'

        notice = show_stylesheet_notice(scope, hostile)

        assert listed_files(notice) == [hostile]
        assert notice.querySelectorAll("img") == []


class TestExplanation:
    def test_failure_has_a_student_friendly_explanation(self):
        title, message, steps = ID_EXPLANATIONS[FAILURE_ID]

        assert title
        assert "Python code still ran" in message
        assert any("add_website_css_file" in step for step in steps)
