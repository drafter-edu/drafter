"""Tests for the checks Drafter runs on what a route returns."""

import warnings

import pytest

from drafter import Button, Fragment, Link, Page
from drafter.client_server import commands
from drafter.client_server.client_server import ClientServer
from drafter.client_server.commands import set_main_server
from drafter.data.errors import StudentFacingError, with_article
from drafter.data.request import Request
from drafter.payloads.verification import (
    verify_page_state_history,
    verify_response_payload_type,
)
from drafter.router.routes import Router

REQUEST = Request(action="link", url="index", kwargs={}, event={})


class TestWithArticle:
    @pytest.mark.parametrize(
        "noun, expected",
        [
            ("int", "an int"),
            ("str", "a str"),
            ("list", "a list"),
            ("Image", "an Image"),
            ("Button", "a Button"),
            ("", "a "),
        ],
    )
    def test_chooses_by_first_letter(self, noun, expected):
        assert with_article(noun) == expected


class TestReturnedValueMessages:
    def test_an_int_is_named_with_an(self):
        failure = verify_response_payload_type(REQUEST, 5)

        assert failure is not None
        assert "returned an int instead of a Page" in failure.friendly_message

    def test_a_dict_is_named_with_a(self):
        failure = verify_response_payload_type(REQUEST, {"a": 1})

        assert failure is not None
        assert "returned a dict instead of a Page" in failure.friendly_message

    def test_state_type_change_names_both_types(self):
        failure = verify_page_state_history(REQUEST, 5, ["five"])

        assert failure is not None
        assert "is an int" in failure.friendly_message
        assert "was a str" in failure.friendly_message

    def test_same_type_is_accepted(self):
        assert verify_page_state_history(REQUEST, 6, [5]) is None

    def test_no_history_means_nothing_to_compare(self):
        assert verify_page_state_history(REQUEST, 6, []) is None


class TestStateTypeIsExact:
    """Both checks of the state's type use the exact type.

    `isinstance` depends on direction: `True` passed for an `int` state
    and a subclass passed for its parent, each only one way round, and the
    history then logged a warning for a page that had been accepted.
    """

    def test_bool_is_not_an_int_state(self):
        failure = verify_page_state_history(REQUEST, True, [5])

        assert failure is not None
        assert failure.friendly_title == "State Changed Type"
        assert "is a bool" in failure.friendly_message
        assert "was an int" in failure.friendly_message

    def test_int_is_not_a_bool_state(self):
        assert verify_page_state_history(REQUEST, 5, [True]) is not None

    def test_subclass_is_a_different_type(self):
        class State:
            pass

        class SpecialState(State):
            pass

        assert verify_page_state_history(REQUEST, SpecialState(), [State()]) is not None
        assert verify_page_state_history(REQUEST, State(), [SpecialState()]) is not None

    @pytest.mark.parametrize(
        "previous, updated",
        [(5, True), (True, 5), (5, 6), ("a", "b"), (5, "five"), (None, None)],
    )
    def test_history_warns_for_exactly_the_same_cases(self, previous, updated):
        """What verification accepts never reaches the history's warning."""
        saved = commands.MAIN_SERVER
        server = ClientServer("STATE_TYPE_TEST")
        set_main_server(server)
        try:
            server.state.update(previous)
            server.state.update(updated)
        finally:
            commands.MAIN_SERVER = saved
        warned = any(
            event.kind == "state.type_change"
            for event in server.event_bus.unprocessed_events
        )

        rejected = verify_page_state_history(REQUEST, updated, [previous])

        assert (rejected is not None) is warned


class TestAsyncRoute:
    def test_async_route_is_explained(self):
        async def index():
            return Page(None, ["Hello"])

        with warnings.catch_warnings():
            # A coroutine left open would warn that it was never awaited.
            warnings.simplefilter("error")
            failure = verify_response_payload_type(REQUEST, index())

        assert failure is not None
        assert failure.friendly_title == "Route Did Not Return a Page"
        assert "async def" in failure.message
        assert "async def" in failure.friendly_message
        assert any("`def`" in step for step in failure.friendly_steps)


class TestMissingRouteNamesTheComponent:
    """A Button used to be reported as a "Link"."""

    def test_button_is_called_a_button(self):
        with pytest.raises(StudentFacingError) as raised:
            Button("+10", "ad_ten").verify(Router(), None, None, REQUEST)

        assert str(raised.value) == "Button `+10` points to non-existent page `ad_ten`."
        assert "The button labeled '+10'" in raised.value.friendly_message
        assert "Link" not in " ".join(raised.value.friendly_steps)
        assert raised.value.friendly_title == "Button Points to a Missing Page"

    def test_steps_do_not_suggest_passing_the_function(self):
        """A function name used above its `def` raises `NameError`."""
        with pytest.raises(StudentFacingError) as raised:
            Button("+10", "ad_ten").verify(Router(), None, None, REQUEST)

        assert "function itself" not in " ".join(raised.value.friendly_steps)

    def test_bad_web_address_gets_the_same_title(self):
        with pytest.raises(StudentFacingError) as raised:
            Link("Docs", "file://notes.html").verify(Router(), None, None, REQUEST)

        assert raised.value.friendly_title == "Link Points to a Missing Page"
        assert "Link('Home', 'index')" in " ".join(raised.value.friendly_steps)

    def test_bad_content_has_the_page_content_title(self):
        with pytest.raises(StudentFacingError) as raised:
            Page(None, [{"a": 1}])

        assert raised.value.friendly_title == "Page Content Problem"

    def test_link_is_called_a_link(self):
        with pytest.raises(StudentFacingError) as raised:
            Link("Next", "sumary").verify(Router(), None, None, REQUEST)

        assert str(raised.value) == "Link `Next` points to non-existent page `sumary`."
        assert "The link labeled 'Next'" in raised.value.friendly_message
        assert raised.value.friendly_title == "Link Points to a Missing Page"


class TestForgottenBrackets:
    """A `Page` takes nothing by position after its content."""

    def test_component_after_the_content_explains_the_brackets(self):
        with pytest.raises(StudentFacingError) as raised:
            Page(None, "Hello", Button("Next", "next"))

        assert "must be given as one list" in str(raised.value)
        assert raised.value.friendly_title == "Page Content Problem"
        assert "a Button" in raised.value.friendly_message
        assert "Page(state, ['Hello', Button(...)])" in raised.value.friendly_steps[0]

    def test_second_string_is_not_read_as_css(self):
        """`Page(state, "Hello", "there")` used to put "there" in the CSS."""
        with pytest.raises(StudentFacingError) as raised:
            Page(None, "Hello", "there")

        assert "a str" in raised.value.friendly_message
        assert "Page(state, ['Hello', 'there'])" in raised.value.friendly_steps[0]
        assert "css='...'" in raised.value.friendly_steps[1]

    def test_values_after_a_list_join_the_list_in_the_corrected_call(self):
        with pytest.raises(StudentFacingError) as raised:
            Page(None, ["Hello", 5], "x" * 40, True)

        corrected = raised.value.friendly_steps[0]
        assert f"['Hello', 5, '{'x' * 30}...', True]" in corrected

    def test_css_and_js_are_given_by_name(self):
        page = Page(None, ["Hello"], css="p { color: red }", js="go()")

        assert page.css == "p { color: red }"
        assert page.js == "go()"

    def test_non_text_js_is_rejected(self):
        with pytest.raises(StudentFacingError, match="The js of a Page"):
            Page(None, ["Hello"], js=5)

    def test_list_with_a_component_is_rejected(self):
        with pytest.raises(StudentFacingError, match="The css of a Page"):
            Page(None, ["Hello"], css=[Button("Next", "next")])

    def test_fragment_names_itself(self):
        with pytest.raises(StudentFacingError, match="The css of a Fragment"):
            Fragment(None, ["Hello"], css=5)

    @pytest.mark.parametrize("css", [None, "p { color: red }", ["p {}", "b {}"], []])
    def test_text_css_is_still_accepted(self, css):
        assert Page(None, ["Hello"], css=css, js=css).css == css

    def test_content_replaced_after_construction_is_still_caught(self):
        page = Page(None, ["Hello"])
        page.content = "Hello"

        failure = page.verify(Router(), None, None, REQUEST)

        assert failure is not None
        assert "content that is a str instead of a list" in failure.friendly_message
