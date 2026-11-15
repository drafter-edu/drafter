"""Tests for the default reset route (router/defaults/reset.py).

A page can hold several Drafter sites, each with its own ClientServer.
The reset route must reset the server that is handling the request; it
used to reset whichever server was the "main" one.
"""

from dataclasses import dataclass

import pytest

from drafter import Page
from drafter.client_server import commands
from drafter.client_server.client_server import ClientServer
from drafter.client_server.commands import set_main_server
from drafter.data.request import Request
from drafter.router.defaults.reset import default_reset
from drafter.router.system_routes import _SYSTEM_ROUTES


@dataclass
class State:
    count: int


def bump(state: State) -> Page:
    state.count += 1
    return Page(state, [str(state.count)])


def make_server(name: str) -> ClientServer:
    server = ClientServer(name)
    server.add_route("bump", bump)
    server.do_configuration()
    server.do_start(initial_state=State(0))
    server.do_visit(Request("link", "bump", {}, {}, ""))
    return server


@pytest.fixture(autouse=True)
def isolate_main_server():
    """Save and restore the global current-server pointer around each test."""
    saved = commands.MAIN_SERVER
    yield
    commands.MAIN_SERVER = saved


def test_registered_as_system_route():
    assert _SYSTEM_ROUTES["--reset"] is default_reset


def test_reset_applies_to_the_server_handling_the_request():
    first = make_server("first")
    second = make_server("second")
    assert first.state.current == State(1)
    assert second.state.current == State(1)
    set_main_server(first)

    second.do_visit(Request("link", "--reset", {}, {}, ""))

    assert second.state.current == State(0)
    assert first.state.current == State(1)
