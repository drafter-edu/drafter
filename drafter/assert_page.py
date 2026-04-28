"""
assert_page examples
====================
This module contains a collection of example tests that demonstrate the
:func:`assert_page` function, which compares two
:class:`~drafter.page.Page` objects recursively while ignoring style
differences.

Run this file directly to execute all examples::

    python -m drafter.assert_page

Each section is labelled so you can see which scenario is being tested.
Passing tests print ``TEST PASSED`` and failing ones print ``FAILURE``.
"""

from dataclasses import dataclass
from drafter import Page, assert_page, assert_in_page
from drafter.components import (
    Div, Span, Header, Text, Button, Link,
    BulletedList, NumberedList, TextBox, CheckBox, Table,
)
from drafter.styling import italic, bold, underline, change_color


# ---------------------------------------------------------------------------
# Minimal state dataclass used throughout the examples
# ---------------------------------------------------------------------------

@dataclass
class State:
    value: str = ""


# ---------------------------------------------------------------------------
# Helper pages
# ---------------------------------------------------------------------------

def simple_page(state: State) -> Page:
    return Page(state, ["Hello, world!"])


def nested_page(state: State) -> Page:
    return Page(state, [
        Div(
            Div(
                Div(
                    italic("Hello world!"))))
    ])


def styled_text_page(state: State) -> Page:
    return Page(state, [
        bold("Bold text"),
        underline("Underlined text"),
        change_color(Text("Red text"), "red"),
    ])


def mixed_content_page(state: State) -> Page:
    return Page(state, [
        Header("Welcome", level=1),
        "Some plain text",
        Div(
            Text("Inside a div"),
            BulletedList(["item one", "item two", "item three"]),
        ),
        Button("Click me", "index"),
    ])


def stateful_page(state: State) -> Page:
    return Page(state, [
        f"Current value: {state.value}",
        TextBox("value", state.value),
        Button("Submit", "index"),
    ])


# ===========================================================================
# Example tests
# ===========================================================================

if __name__ == '__main__':

    # -----------------------------------------------------------------------
    # 1. Simplest case: single string in content
    # -----------------------------------------------------------------------
    print("=== 1. Simple string content ===")
    assert_page(
        simple_page(State()),
        Page(State(), ["Hello, world!"])
    )

    # -----------------------------------------------------------------------
    # 2. String compared to Text object (styles ignored)
    # -----------------------------------------------------------------------
    print("\n=== 2. String vs Text (style ignored) ===")
    assert_page(
        Page(State(), [Text("Hello, world!")]),
        Page(State(), ["Hello, world!"])
    )

    # -----------------------------------------------------------------------
    # 3. Deeply nested Div with italic styling ignored
    # -----------------------------------------------------------------------
    print("\n=== 3. Nested Divs – italic style ignored ===")
    assert_page(
        nested_page(State()),
        Page(State(), [
            Div(Div(Div("Hello world!")))
        ])
    )

    # -----------------------------------------------------------------------
    # 4. Multiple styled texts – styles ignored on all of them
    # -----------------------------------------------------------------------
    print("\n=== 4. Multiple styled Text objects (styles ignored) ===")
    assert_page(
        styled_text_page(State()),
        Page(State(), [
            "Bold text",
            "Underlined text",
            "Red text",
        ])
    )

    # -----------------------------------------------------------------------
    # 5. Mixed content: Header, plain string, Div with nested list, Button
    # -----------------------------------------------------------------------
    print("\n=== 5. Mixed content (Header, str, Div, BulletedList, Button) ===")
    assert_page(
        mixed_content_page(State()),
        Page(State(), [
            Header("Welcome", level=1),
            "Some plain text",
            Div(
                Text("Inside a div"),
                BulletedList(["item one", "item two", "item three"]),
            ),
            Button("Click me", "index"),
        ])
    )

    # -----------------------------------------------------------------------
    # 6. State comparison – state must still match
    # -----------------------------------------------------------------------
    print("\n=== 6. State with value ===")
    assert_page(
        stateful_page(State("hello")),
        Page(State("hello"), [
            "Current value: hello",
            TextBox("value", "hello"),
            Button("Submit", "index"),
        ])
    )

    # -----------------------------------------------------------------------
    # 7. Div with extra non-style attributes – those must still match
    # -----------------------------------------------------------------------
    print("\n=== 7. Div with matching non-style attributes ===")
    assert_page(
        Page(State(), [Div("content", id="main", style_color="red")]),
        Page(State(), [Div("content", id="main", style_color="blue")])
    )

    # -----------------------------------------------------------------------
    # 8. Span with style – style ignored, body compared
    # -----------------------------------------------------------------------
    print("\n=== 8. Span with style vs plain Span ===")
    assert_page(
        Page(State(), [Span("hello", style_font_size="20px")]),
        Page(State(), [Span("hello")])
    )

    # -----------------------------------------------------------------------
    # 9. Demonstrate failure: wrong string content
    # -----------------------------------------------------------------------
    print("\n=== 9. EXPECTED FAILURE – wrong string ===")
    assert_page(
        Page(State(), ["Actual text"]),
        Page(State(), ["Expected text"])
    )

    # -----------------------------------------------------------------------
    # 10. Demonstrate failure: wrong state
    # -----------------------------------------------------------------------
    print("\n=== 10. EXPECTED FAILURE – wrong state ===")
    assert_page(
        Page(State("actual"), ["some content"]),
        Page(State("expected"), ["some content"])
    )

    # -----------------------------------------------------------------------
    # 11. Demonstrate failure: different content lengths
    # -----------------------------------------------------------------------
    print("\n=== 11. EXPECTED FAILURE – different content list lengths ===")
    assert_page(
        Page(State(), ["one", "two"]),
        Page(State(), ["one", "two", "three"])
    )

    # -----------------------------------------------------------------------
    # 12. Demonstrate failure: wrong component type
    # -----------------------------------------------------------------------
    print("\n=== 12. EXPECTED FAILURE – Header vs Div ===")
    assert_page(
        Page(State(), [Header("Hello")]),
        Page(State(), [Div("Hello")])
    )

    # -----------------------------------------------------------------------
    # 13. Link component
    # -----------------------------------------------------------------------
    print("\n=== 13. Link component ===")
    assert_page(
        Page(State(), [Link("Visit", "http://example.com")]),
        Page(State(), [Link("Visit", "http://example.com")])
    )

    # -----------------------------------------------------------------------
    # 14. NumberedList
    # -----------------------------------------------------------------------
    print("\n=== 14. NumberedList (styles ignored) ===")
    assert_page(
        Page(State(), [NumberedList(["a", "b", "c"], style_color="green")]),
        Page(State(), [NumberedList(["a", "b", "c"])])
    )

    # -----------------------------------------------------------------------
    # 15. Nested styled content inside a Div
    # -----------------------------------------------------------------------
    print("\n=== 15. Nested styled Text inside Div (styles ignored) ===")
    assert_page(
        Page(State(), [Div(bold("Title"), italic("Subtitle"))]),
        Page(State(), [Div("Title", "Subtitle")])
    )

    # ===========================================================================
    # assert_in_page examples
    # ===========================================================================

    # -----------------------------------------------------------------------
    # 16. Plain string at the top level of page content
    # -----------------------------------------------------------------------
    print("\n=== 16. assert_in_page – plain string at top level ===")
    assert_in_page(
        Page(State(), ["Hello, world!", "Another line"]),
        "Hello, world!"
    )

    # -----------------------------------------------------------------------
    # 17. String needle matches a styled Text (styles ignored)
    # -----------------------------------------------------------------------
    print("\n=== 17. assert_in_page – string matches italic Text ===")
    assert_in_page(
        Page(State(), [italic("Deep thought")]),
        "Deep thought"
    )

    # -----------------------------------------------------------------------
    # 18. Needle deeply nested inside Divs
    # -----------------------------------------------------------------------
    print("\n=== 18. assert_in_page – needle inside nested Divs ===")
    assert_in_page(
        nested_page(State()),
        "Hello world!"
    )

    # -----------------------------------------------------------------------
    # 19. PageContent needle (Header) found at top level
    # -----------------------------------------------------------------------
    print("\n=== 19. assert_in_page – Header component ===")
    assert_in_page(
        mixed_content_page(State()),
        Header("Welcome", level=1)
    )

    # -----------------------------------------------------------------------
    # 20. Button needle found inside page
    # -----------------------------------------------------------------------
    print("\n=== 20. assert_in_page – Button found ===")
    assert_in_page(
        mixed_content_page(State()),
        Button("Click me", "index")
    )

    # -----------------------------------------------------------------------
    # 21. Text needle inside a BulletedList inside a Div
    # -----------------------------------------------------------------------
    print("\n=== 21. assert_in_page – string inside BulletedList inside Div ===")
    assert_in_page(
        mixed_content_page(State()),
        "item two"
    )

    # -----------------------------------------------------------------------
    # 22. Styled Text needle – styles on needle are ignored
    # -----------------------------------------------------------------------
    print("\n=== 22. assert_in_page – styled Text needle, styles ignored ===")
    assert_in_page(
        Page(State(), [Div(bold("Important"), "other")]),
        bold("Important")   # style on needle should not matter
    )

    # -----------------------------------------------------------------------
    # 23. Needle is a Div that appears nested inside another Div
    # -----------------------------------------------------------------------
    print("\n=== 23. assert_in_page – Div needle inside Div ===")
    assert_in_page(
        Page(State(), [Div(Div("inner"))]),
        Div("inner")
    )

    # -----------------------------------------------------------------------
    # 24. EXPECTED FAILURE – needle not present anywhere in the page
    # -----------------------------------------------------------------------
    print("\n=== 24. EXPECTED FAILURE – needle not in page ===")
    assert_in_page(
        Page(State(), ["Hello", Div("world")]),
        "missing"
    )

    # -----------------------------------------------------------------------
    # 25. EXPECTED FAILURE – correct text but wrong component type
    # -----------------------------------------------------------------------
    print("\n=== 25. EXPECTED FAILURE – right text, wrong component type ===")
    assert_in_page(
        Page(State(), [Span("content")]),
        Div("content")
    )

    # -----------------------------------------------------------------------
    # 26. NumberedList item found inside the page
    # -----------------------------------------------------------------------
    print("\n=== 26. assert_in_page – NumberedList with style ===")
    assert_in_page(
        Page(State(), [NumberedList(["a", "b", "c"], style_color="blue")]),
        NumberedList(["a", "b", "c"])   # style on haystack ignored
    )

    # -----------------------------------------------------------------------
    # 27. TextBox found inside stateful page
    # -----------------------------------------------------------------------
    print("\n=== 27. assert_in_page – TextBox ===")
    assert_in_page(
        stateful_page(State("hello")),
        TextBox("value", "hello")
    )
