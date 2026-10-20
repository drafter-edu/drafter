"""Tests for the default stop-server page (router/defaults/stop_server.py).

The --stop-server system route explains what stopping the local development
server does and renders the well-known button that the client bridge wires
to the debug panel's stop request. Visiting the page must not stop anything
by itself; only the button does.
"""

from types import SimpleNamespace

from drafter.components import Header
from drafter.payloads.kinds.page import Page
from drafter.router.defaults.stop_server import (
    StopServerButton,
    default_stop_server,
)
from drafter.router.system_routes import _SYSTEM_ROUTES
from drafter.site.site import DRAFTER_TAG_IDS


def make_page():
    return default_stop_server("state", SimpleNamespace())


def page_headers(page):
    return [item.body for item in page.content if isinstance(item, Header)]


def page_text(page):
    return " ".join(repr(item) for item in page.content)


class TestDefaultStopServer:
    def test_registered_as_system_route(self):
        assert _SYSTEM_ROUTES["--stop-server"] is default_stop_server

    def test_returns_page_with_state(self):
        page = make_page()
        assert isinstance(page, Page)
        assert page.state == "state"

    def test_explains_what_stopping_does(self):
        headers = page_headers(make_page())
        assert "Stop the Server?" in headers
        assert "What happens when you stop it" in headers

        text = page_text(make_page())
        assert "Ctrl+C" in text
        assert "run your Python file again" in text

    def test_includes_stop_button_with_well_known_id(self):
        page = make_page()
        buttons = [item for item in page.content if isinstance(item, StopServerButton)]
        assert len(buttons) == 1
        assert buttons[0].get_id() == DRAFTER_TAG_IDS["STOP_SERVER"]

    def test_offers_a_way_back_to_the_index(self):
        assert "index" in page_text(make_page())

    def test_rendered_button_is_not_a_submit_button(self):
        html = make_page().render("state", None)
        assert f'id="{DRAFTER_TAG_IDS["STOP_SERVER"]}"' in html
        # type="button" keeps the click from submitting the site form.
        assert 'type="button"' in html
        assert "Yes, stop the server" in html
