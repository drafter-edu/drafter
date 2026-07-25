"""Tests for Drafter's jest-like assertion framework (drafter.testing)."""

from dataclasses import dataclass

import pytest

from drafter import (
    Button,
    Div,
    Header,
    Page,
    Text,
)
from drafter.payloads.kinds.fragment import Fragment
from drafter.testing import (
    assert_attribute,
    assert_children,
    assert_content,
    assert_equal,
    assert_has,
    assert_has_regex,
    assert_in,
    assert_in_regex,
    assert_not_has,
    assert_not_in,
    assert_page,
    assert_state,
    assert_style,
    assert_text,
    get_assertion_defaults,
    reporting,
    set_assertion_defaults,
)


@dataclass
class State:
    score: int
    name: str


def save_game(state):
    return Page(state, ["Saved!"])


@pytest.fixture(autouse=True)
def reset_defaults():
    """Restore the global assertion defaults after every test."""
    defaults = get_assertion_defaults()
    original = (
        defaults.precision,
        defaults.exact_strings,
        defaults.strict_styles,
        defaults.report_success,
    )
    yield
    set_assertion_defaults(*original)


@pytest.fixture
def events(monkeypatch):
    """Capture the TestCaseEvents emitted by assertions."""
    captured = []

    def fake_log_record(record, source, **kwargs):
        captured.append(record)
        return record

    monkeypatch.setattr(reporting, "log_record", fake_log_record)
    return captured


def make_page():
    return Page(
        State(5, "Ada"),
        [
            Header("Welcome"),
            "Your score is 5",
            Button("Save Game", save_game),
        ],
    )


# ---------------------------------------------------------------------------
# assert_equal
# ---------------------------------------------------------------------------


def test_assert_equal_passes_and_prints_success(capsys):
    assert assert_equal(5, 5) is True
    output = capsys.readouterr().out
    assert "SUCCESS" in output
    assert "assert_equal" in output


def test_assert_equal_failure_message(capsys):
    assert assert_equal(4, 5) is False
    output = capsys.readouterr().out
    assert "FAILURE" in output
    assert "Expected 5 but got 4" in output


def test_assert_equal_loose_strings_by_default(capsys):
    assert assert_equal("  HELLO ", "hello") is True


def test_assert_equal_exact_strings_flag(capsys):
    assert assert_equal("  HELLO ", "hello", exact_strings=True) is False


def test_assert_equal_float_precision():
    assert assert_equal(0.1 + 0.2, 0.3) is True
    assert assert_equal(0.30000001, 0.3, precision=9) is False


def test_assert_equal_nested_structures(capsys):
    assert assert_equal({"a": [1, 2]}, {"a": [1, 3]}) is False
    output = capsys.readouterr().out
    assert "'a'" in output
    assert "index '1'" in output


def test_assert_equal_whole_pages():
    assert assert_equal(make_page(), make_page()) is True


def test_assert_equal_page_state_difference_names_path(capsys):
    other = Page(State(6, "Ada"), make_page().content)
    assert assert_equal(make_page(), other) is False
    output = capsys.readouterr().out
    assert "Page state" in output
    assert "score" in output


def test_assert_equal_page_vs_fragment_reports_type(capsys):
    page = Page(None, ["Hi"])
    fragment = Fragment(None, ["Hi"])
    assert assert_equal(page, fragment) is False
    output = capsys.readouterr().out
    assert "Fragment" in output
    assert "Page" in output


def test_text_component_equals_plain_string():
    assert assert_equal(Text("Hello"), "Hello") is True
    assert assert_equal("Hello", Text("Hello")) is True


# ---------------------------------------------------------------------------
# Style strictness flags
# ---------------------------------------------------------------------------


def test_styles_ignored_by_default():
    styled = Button("Save", save_game, style_color="red")
    plain = Button("Save", save_game)
    assert assert_equal(styled, plain) is True


def test_strict_styles_per_call():
    styled = Button("Save", save_game, style_color="red")
    plain = Button("Save", save_game)
    assert assert_equal(styled, plain, strict_styles=True) is False


def test_strict_styles_global_default_and_override():
    styled = Button("Save", save_game, style_color="red")
    plain = Button("Save", save_game)
    set_assertion_defaults(strict_styles=True)
    assert assert_equal(styled, plain) is False
    # A per-call flag can loosen a single check again
    assert assert_equal(styled, plain, strict_styles=False) is True


def test_strict_styles_matching_styles_still_pass():
    one = Button("Save", save_game, style_color="red")
    two = Button("Save", save_game, style_color="red")
    assert assert_equal(one, two, strict_styles=True) is True


# ---------------------------------------------------------------------------
# assert_state
# ---------------------------------------------------------------------------


def test_assert_state_unwraps_page():
    assert assert_state(make_page(), State(5, "Ada")) is True


def test_assert_state_accepts_two_pages():
    assert assert_state(make_page(), Page(State(5, "Ada"), [])) is True


def test_assert_state_failure_names_field(capsys):
    assert assert_state(make_page(), State(6, "Ada")) is False
    output = capsys.readouterr().out
    assert "state was different" in output
    assert "State score" in output
    assert "Expected 6 but got 5" in output


def test_assert_state_type_mismatch(capsys):
    assert assert_state(make_page(), 5) is False
    output = capsys.readouterr().out
    assert "FAILURE" in output


# ---------------------------------------------------------------------------
# assert_content
# ---------------------------------------------------------------------------


def test_assert_content_ignores_state():
    changed_state = Page(State(999, "Bob"), make_page().content)
    assert assert_content(changed_state, make_page()) is True


def test_assert_content_accepts_lists_and_strings():
    page = Page(None, ["Hello World"])
    assert assert_content(page, ["Hello World"]) is True
    assert assert_content(page, "hello world") is True
    assert assert_content(page, Text("Hello World")) is True


def test_assert_content_failure_shows_location(capsys):
    page = Page(None, [Button("Submit", save_game)])
    assert assert_content(page, [Button("Save", save_game)]) is False
    output = capsys.readouterr().out
    assert "content was different" in output
    assert "Button" in output


def test_assert_content_rejects_non_content(capsys):
    assert assert_content(42, ["Hello"]) is False
    output = capsys.readouterr().out
    assert "could not be understood as page content" in output


def test_assert_content_length_mismatch(capsys):
    assert assert_content(Page(None, ["a", "b"]), ["a"]) is False
    output = capsys.readouterr().out
    assert "Too many items" in output


# ---------------------------------------------------------------------------
# assert_page
# ---------------------------------------------------------------------------


def test_assert_page_passes_for_matching_pages():
    assert assert_page(make_page(), make_page()) is True


def test_assert_page_requires_pages(capsys):
    assert assert_page("not a page", make_page()) is False
    output = capsys.readouterr().out
    assert "was not a Page" in output
    assert "call your route function" in output


def test_assert_page_reports_state_and_content_differences(capsys):
    other = Page(State(6, "Ada"), ["Different"])
    assert assert_page(make_page(), other) is False
    output = capsys.readouterr().out
    assert "Page state" in output
    assert "Page content" in output


# ---------------------------------------------------------------------------
# assert_has / assert_in and negations
# ---------------------------------------------------------------------------


def test_assert_has_finds_component_anywhere():
    assert assert_has(make_page(), Button("Save Game", save_game)) is True


def test_assert_has_finds_component_despite_styles():
    page = Page(None, [Button("Save", save_game, style_color="red")])
    assert assert_has(page, Button("Save", save_game)) is True


def test_assert_has_finds_nested_content():
    page = Page(None, [Div(Div(Text("deep text")))])
    assert assert_has(page, "deep text") is True


def test_assert_has_string_substring_fallback():
    # "score" only appears inside the longer text chunk
    assert assert_has(make_page(), "score is") is True


def test_assert_has_is_case_insensitive_by_default():
    assert assert_has(make_page(), "WELCOME") is True


def test_assert_has_exact_strings():
    assert assert_has(make_page(), "WELCOME", exact_strings=True) is False
    assert assert_has(make_page(), "Welcome", exact_strings=True) is True


def test_assert_has_failure_lists_page_text(capsys):
    assert assert_has(make_page(), "Game Over") is False
    output = capsys.readouterr().out
    assert "Could not find" in output
    assert "The page's text was" in output
    assert "'Welcome'" in output


def test_assert_in_flipped_arguments():
    assert assert_in("Welcome", make_page()) is True
    assert assert_in("Game Over", make_page()) is False


def test_assert_not_has():
    assert assert_not_has(make_page(), "Game Over") is True
    assert assert_not_has(make_page(), "Welcome") is False


def test_assert_not_has_failure_explains(capsys):
    assert assert_not_has(make_page(), "Welcome") is False
    output = capsys.readouterr().out
    assert "expected it to be absent" in output


def test_assert_not_in_flipped_arguments():
    assert assert_not_in("Game Over", make_page()) is True
    assert assert_not_in("Welcome", make_page()) is False


def test_assert_has_rejects_unsearchable_page(capsys):
    assert assert_has(42, "anything") is False
    output = capsys.readouterr().out
    assert "could not be searched" in output


# ---------------------------------------------------------------------------
# Regex assertions
# ---------------------------------------------------------------------------


def test_assert_has_regex_matches_text():
    assert assert_has_regex(make_page(), r"score is \d+") is True


def test_assert_has_regex_case_insensitive_by_default():
    assert assert_has_regex(make_page(), r"WELCOME") is True


def test_assert_has_regex_exact_strings_is_case_sensitive():
    assert assert_has_regex(make_page(), r"WELCOME", exact_strings=True) is False


def test_assert_has_regex_failure_lists_text(capsys):
    assert assert_has_regex(make_page(), r"lives: \d+") is False
    output = capsys.readouterr().out
    assert "No text in the page matched" in output
    assert "The page's text was" in output


def test_assert_has_regex_invalid_pattern(capsys):
    assert assert_has_regex(make_page(), r"[unclosed") is False
    output = capsys.readouterr().out
    assert "not a valid regular expression" in output


def test_assert_in_regex_flipped_arguments():
    assert assert_in_regex(r"score is \d+", make_page()) is True
    assert assert_in_regex(r"lives: \d+", make_page()) is False


# ---------------------------------------------------------------------------
# assert_attribute
# ---------------------------------------------------------------------------


def test_assert_attribute_field():
    button = Button("Save", save_game)
    assert assert_attribute(button, "text", "Save") is True
    assert assert_attribute(button, "text", "Load") is False


def test_assert_attribute_url_accepts_function():
    button = Button("Save", save_game)
    assert assert_attribute(button, "url", save_game) is True
    assert assert_attribute(button, "url", "save_game") is True


def test_assert_attribute_extra_settings():
    box = Text("hi", id="greeting")
    assert assert_attribute(box, "id", "greeting") is True


def test_assert_attribute_missing_lists_available(capsys):
    button = Button("Save", save_game)
    assert assert_attribute(button, "label", "Save") is False
    output = capsys.readouterr().out
    assert "does not have an attribute named 'label'" in output
    assert "text" in output
    assert "url" in output


def test_assert_attribute_requires_component(capsys):
    assert assert_attribute(make_page(), "text", "Save") is False
    output = capsys.readouterr().out
    assert "was not a component" in output
    assert "page.content[0]" in output


# ---------------------------------------------------------------------------
# assert_style
# ---------------------------------------------------------------------------


def test_assert_style_keyword_setting():
    button = Button("Save", save_game, style_color="red")
    assert assert_style(button, "color", "red") is True
    assert assert_style(button, "color", "blue") is False


def test_assert_style_loose_value_matching():
    button = Button("Save", save_game, style_color="RED ")
    assert assert_style(button, "color", "red") is True
    assert assert_style(button, "color", "red", exact_strings=True) is False


def test_assert_style_update_style_helper():
    text = Text("hi").update_style("background-color", "green")
    assert assert_style(text, "background_color", "green") is True
    assert assert_style(text, "background-color", "green") is True


def test_assert_style_raw_style_string():
    text = Text("hi", style="font-size: 14px; color: blue")
    assert assert_style(text, "font-size", "14px") is True
    assert assert_style(text, "color", "blue") is True


def test_assert_style_missing_lists_styles(capsys):
    button = Button("Save", save_game, style_color="red")
    assert assert_style(button, "border", "1px") is False
    output = capsys.readouterr().out
    assert "does not have a 'border' style" in output
    assert "color" in output


def test_assert_style_no_styles_hint(capsys):
    assert assert_style(Text("hi"), "color", "red") is False
    output = capsys.readouterr().out
    assert "No styles are set directly on this component" in output


# ---------------------------------------------------------------------------
# assert_children
# ---------------------------------------------------------------------------


def test_assert_children_matches_content():
    box = Div("first", Text("second"))
    assert assert_children(box, ["first", "second"]) is True


def test_assert_children_single_expected_child():
    box = Div(Text("only"))
    assert assert_children(box, "only") is True


def test_assert_children_failure_names_component(capsys):
    box = Div("first", "second")
    assert assert_children(box, ["first"]) is False
    output = capsys.readouterr().out
    assert "Div children" in output


def test_assert_children_requires_component(capsys):
    assert assert_children(["a"], ["a"]) is False
    output = capsys.readouterr().out
    assert "was not a component" in output


# ---------------------------------------------------------------------------
# assert_text
# ---------------------------------------------------------------------------


def test_assert_text_collapses_structure_and_whitespace():
    assert assert_text(make_page(), "welcome your score is 5 save game") is True


def test_assert_text_exact_strings():
    page = Page(None, ["Hello"])
    assert assert_text(page, "Hello", exact_strings=True) is True
    assert assert_text(page, "hello", exact_strings=True) is False


def test_assert_text_failure_shows_both_texts(capsys):
    assert assert_text(make_page(), "goodbye") is False
    output = capsys.readouterr().out
    assert "text was different" in output
    assert "goodbye" in output


def test_assert_text_on_single_component():
    assert assert_text(Header("Welcome"), "Welcome") is True


# ---------------------------------------------------------------------------
# Reporting: printing flags and debug panel events
# ---------------------------------------------------------------------------


def test_quiet_suppresses_success_output(capsys):
    assert assert_equal(5, 5, quiet=True) is True
    assert capsys.readouterr().out == ""


def test_report_success_default_flag(capsys):
    set_assertion_defaults(report_success=False)
    assert assert_equal(5, 5) is True
    assert capsys.readouterr().out == ""
    # Failures are still printed
    assert assert_equal(4, 5) is False
    assert "FAILURE" in capsys.readouterr().out


def test_failed_assertion_logs_event_with_diff(events, capsys):
    assert_equal(make_page(), Page(State(6, "Ada"), ["Different"]))
    assert len(events) == 1
    event = events[0]
    assert event.passed is False
    assert event.assertion_kind == "assert_equal"
    assert event.diff_html != ""
    assert "Actually Returned" in event.diff_html
    assert "Test Expected" in event.diff_html
    assert event.message != ""
    assert "different" in event.message


def test_passed_assertion_logs_event(events, capsys):
    assert_state(make_page(), State(5, "Ada"))
    assert len(events) == 1
    event = events[0]
    assert event.passed is True
    assert event.assertion_kind == "assert_state"
    assert event.diff_html == ""
    assert event.message == ""


def test_search_assertions_log_events(events, capsys):
    assert_has(make_page(), "Game Over")
    assert len(events) == 1
    assert events[0].assertion_kind == "assert_has"
    assert events[0].passed is False


def test_event_logging_failure_does_not_break_assertions(monkeypatch, capsys):
    def broken_log_record(record, source, **kwargs):
        raise RuntimeError("no server running")

    monkeypatch.setattr(reporting, "log_record", broken_log_record)
    assert assert_equal(5, 5) is True


def test_many_differences_are_capped(capsys):
    actual = list(range(20))
    expected = [value + 1 for value in actual]
    assert assert_equal(actual, expected) is False
    output = capsys.readouterr().out
    assert "more difference" in output
