"""Tests for visits whose state contains a circular reference.

The debug panel turns every visit into an `assert_equal(...)` regression
test (the ResponseEvent's `formatted_page_content`). A value that contains
itself cannot be written as a Python literal, so such a visit must produce
a one-line comment in place of a test: the Copy and Download output of the
debug panel has to stay Python that can be pasted and run. The JavaScript
half (keeping the comment among the tests) is covered by
js/src/__tests__/debug-panel.test.tsx.
"""

import ast
from dataclasses import dataclass, field

import pytest

from drafter.client_server.client_server import ClientServer
from drafter.client_server.commands import (
    get_main_event_bus,
    get_main_server,
    set_main_server,
)
from drafter.data.errors import STATUS_OK
from drafter.data.request import Request
from drafter.history.formatting import (
    NOT_FROZEN_PREFIX,
    describe_unfrozen_circular_visit,
)
from drafter.history.utils import has_circular_reference
from drafter.payloads.kinds.page import Page


@dataclass
class Owner:
    """Module-level so get_type_hints can resolve it during conversion."""

    name: str
    pets: list["Pet"] = field(default_factory=list)


@dataclass
class Pet:
    """Holds its owner while the owner holds its pets: a circular pair."""

    name: str
    owner: Owner | None = None


def make_circular_pet() -> Pet:
    owner = Owner("Grace")
    pet = Pet("Ada", owner)
    owner.pets.append(pet)
    return pet


@pytest.fixture
def server():
    """A started throwaway main server, so telemetry lands on its bus."""
    previous = get_main_server()
    server = ClientServer("CIRCULAR_TEST_SERVER")
    set_main_server(server)
    server.do_configuration()
    server.do_start()
    yield server
    set_main_server(previous)


def visit_and_get_generated_test(server: ClientServer, route: str) -> str:
    """Visit a route and return the generated test of its ResponseEvent."""
    events = []
    bus = get_main_event_bus()
    subscription = bus.subscribe("*", events.append)
    try:
        response = server.do_visit(Request("link", route, {}, {}, ""))
    finally:
        bus.unsubscribe(subscription)
    assert response.status_code == STATUS_OK
    (response_event,) = [event for event in events if event.kind == "ResponseEvent"]
    return response_event.formatted_page_content


class TestHasCircularReference:
    def test_plain_values_are_not_circular(self):
        assert not has_circular_reference(5)
        assert not has_circular_reference("text")
        assert not has_circular_reference(None)
        assert not has_circular_reference([1, [2, 3], {"a": (4, 5)}])
        assert not has_circular_reference(Pet("Ada", Owner("Grace")))

    def test_a_value_used_twice_is_not_circular(self):
        shared = Owner("Grace")

        assert not has_circular_reference([shared, shared, Pet("Ada", shared)])

    def test_a_list_appended_to_itself_is_circular(self):
        items: list = [1, 2]
        items.append(items)

        assert has_circular_reference(items)

    def test_a_dictionary_holding_itself_is_circular(self):
        data: dict = {"name": "loop"}
        data["me"] = data

        assert has_circular_reference(data)

    def test_a_back_pointer_between_dataclasses_is_circular(self):
        assert has_circular_reference(make_circular_pet())

    def test_a_cycle_nested_inside_other_containers_is_found(self):
        assert has_circular_reference({"pets": (make_circular_pet(),)})


class TestUnfrozenComment:
    def test_comment_names_the_route_and_is_one_line_of_python(self):
        comment = describe_unfrozen_circular_visit(
            "add(Pet(name='Ada', owner=<strong>Circular Reference</strong>))"
        )

        assert comment == (
            "# Not frozen: add(...) has a state with a circular reference, "
            "which cannot be written as a test."
        )
        assert comment.startswith(NOT_FROZEN_PREFIX)
        assert "\n" not in comment
        # A comment is valid Python on its own.
        ast.parse(comment)


class TestGeneratedTestForCircularState:
    def test_circular_state_gets_a_comment_in_place_of_a_test(self, server):
        def add(state: Pet) -> Page:
            return Page(state, ["Hello ", state.name])

        server.add_route("add", add)
        server.state.update(make_circular_pet())

        generated = visit_and_get_generated_test(server, "add")

        assert generated == (
            "# Not frozen: add(...) has a state with a circular reference, "
            "which cannot be written as a test."
        )
        # Neither formatter's marker for the cycle reaches the output.
        assert "Circular Reference" not in generated
        assert "owner=..." not in generated
        ast.parse(generated)

    def test_state_made_circular_by_the_route_gets_the_comment(self, server):
        def tangle(state: Pet) -> Page:
            owner = Owner("Grace")
            state.owner = owner
            owner.pets.append(state)
            return Page(state, ["Tangled"])

        server.add_route("tangle", tangle)
        server.state.update(Pet("Ada"))

        generated = visit_and_get_generated_test(server, "tangle")

        assert generated.startswith(f"{NOT_FROZEN_PREFIX} tangle(...)")

    def test_cycle_removed_by_the_route_still_gets_the_comment(self, server):
        # The route call was recorded with the circular state it received,
        # so it still cannot be written down.
        def untangle(state: Pet) -> Page:
            state.owner = None
            return Page(state, ["Untangled"])

        server.add_route("untangle", untangle)
        server.state.update(make_circular_pet())

        generated = visit_and_get_generated_test(server, "untangle")

        assert generated.startswith(f"{NOT_FROZEN_PREFIX} untangle(...)")

    def test_ordinary_state_still_gets_a_real_test(self, server):
        def add(state: Pet) -> Page:
            return Page(state, ["Hello ", state.name])

        server.add_route("add", add)
        server.state.update(Pet("Ada", Owner("Grace")))

        generated = visit_and_get_generated_test(server, "add")

        assert generated.startswith("assert_equal(")
        assert NOT_FROZEN_PREFIX not in generated
        ast.parse(generated)

    def test_circular_requests_are_forgotten_after_the_visit(self, server):
        def add(state: Pet) -> Page:
            return Page(state, ["Hello ", state.name])

        server.add_route("add", add)
        server.state.update(make_circular_pet())

        visit_and_get_generated_test(server, "add")

        assert server._circular_route_calls == set()
