"""Tests for reloading the tab on a page that a form led to.

After a form is submitted the page's address reads `?route=save`. A reload
used to run `save` with none of the form's values and stop on a "Problem
With the Route's Arguments" page. The bridge now asks the server whether
the route can run with no values, and opens the first page when it cannot.
"""

import sys
from unittest.mock import MagicMock

import pytest

# drafter.bridge requires a browser 'js' module; stub it for unit tests.
if not hasattr(sys.modules.get("js"), "document"):
    sys.modules["js"] = MagicMock()

from drafter.bridge.bridger import build_server_hooks
from drafter.client_server import commands
from drafter.client_server.client_server import ClientServer
from drafter.client_server.commands import set_main_server
from drafter.data.error_explainer import ID_EXPLANATIONS
from drafter.data.request import Request
from drafter.payloads.kinds.page import Page
from tests.test_deep_links import make_navigator

WARNING_ID = "bridge.initial_route_needs_arguments"


def index(state):
    return Page(state, ["Hello"])


def save(state, name: str, age: int):
    return Page(state, [name])


def greet(state, who: str = "friend"):
    return Page(state, [who])


def summary(state):
    return Page(state, ["Summary"])


def show(only_parameter):
    return Page(only_parameter, ["Shown"])


def helper(state, _server, extra: str):
    return Page(state, [extra])


@pytest.fixture
def server():
    """A current server with a few routes, restored afterwards."""
    saved = commands.MAIN_SERVER
    server = ClientServer("RELOAD_AFTER_SUBMIT_TEST")
    set_main_server(server)
    for route in (index, save, greet, summary, show, helper):
        server.router.add_route(route.__name__, route)
    yield server
    commands.MAIN_SERVER = saved


def warnings_on(server: ClientServer) -> list:
    return [
        event
        for event in server.event_bus.unprocessed_events
        if event.kind == WARNING_ID
    ]


class TestFindMissingArguments:
    def test_form_route_names_what_it_needs(self, server):
        assert server.find_missing_arguments("save") == ["name", "age"]

    @pytest.mark.parametrize("route", ["index", "summary", "greet", "show"])
    def test_routes_that_run_on_the_state_alone(self, server, route):
        assert server.find_missing_arguments(route) == []

    def test_framework_values_are_not_missing(self, server):
        assert server.find_missing_arguments("helper") == ["extra"]

    def test_unknown_route_is_left_to_the_not_found_page(self, server):
        assert server.find_missing_arguments("no_such_route") == []

    def test_framework_names_match_what_is_injected(self, server):
        request = Request("page_load", "index", {}, {}, "")
        injected = server._get_extra_dependencies(request, MagicMock())

        assert set(injected) == set(ClientServer.FRAMEWORK_DEPENDENCY_NAMES)


class TestInitialRequest:
    def start(self, server: ClientServer, href: str):
        navigator, dispatched = make_navigator(href)
        hooks = build_server_hooks(server, MagicMock(), MagicMock(), MagicMock())
        navigator.find_missing_arguments = hooks.find_missing_arguments
        navigator.do_initial_request()
        return navigator, dispatched

    def test_reload_on_a_form_route_opens_the_first_page(self, server):
        navigator, dispatched = self.start(server, "http://localhost/?route=save")

        assert [request.url for request in dispatched] == ["index"]
        assert dispatched[0].action == "page_load"

    def test_the_route_is_taken_out_of_the_address(self, server):
        navigator, _ = self.start(server, "http://localhost/?route=save&x=1")

        cleared = navigator.history.runtime.history_replace_state.call_args_list[0]
        assert cleared[0][2] == "http://localhost/?x=1"

    def test_the_original_entry_is_stamped_with_the_first_page(self, server):
        navigator, _ = self.start(server, "http://localhost/?route=save")

        stamped = navigator.history.runtime.history_replace_state.call_args[0][0]
        assert stamped["url"] == "index"

    def test_one_warning_names_the_route_and_what_it_needed(self, server):
        self.start(server, "http://localhost/?route=save")

        (warning,) = warnings_on(server)
        assert warning.error.severity == "warning"
        assert "'save'" in warning.error.message
        assert "'name', 'age'" in warning.error.message
        assert warning.error.friendly_title == ID_EXPLANATIONS[WARNING_ID][0]

    @pytest.mark.parametrize("route", ["summary", "greet", "--about", "no_such_route"])
    def test_other_routes_still_open_from_the_address(self, server, route):
        navigator, dispatched = self.start(server, f"http://localhost/?route={route}")

        assert [request.url for request in dispatched] == [route]
        assert warnings_on(server) == []

    def test_without_the_hook_the_address_is_followed(self, server):
        navigator, dispatched = make_navigator("http://localhost/?route=save")

        navigator.do_initial_request()

        assert dispatched[0].url == "save"
