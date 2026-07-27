"""Examples of Drafter's student-facing testing assertions.

Run this file to see both successful tests and helpful failure messages.
The failures are intentional: Drafter assertions return False instead of
stopping the program, which lets every example run.
"""

from dataclasses import dataclass

from drafter import Button, Div, Header, Page, Text
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
    set_assertion_defaults,
)


@dataclass
class State:
    """The state used by the example page."""

    name: str
    score: float


def save_game(state: State) -> Page:
    """Return a small confirmation page for the example button."""
    return Page(state, ["Game saved!"])


def dashboard(state: State) -> Page:
    """Build the page tested throughout this file."""
    return Page(
        state,
        [
            Header(f"Welcome, {state.name}!"),
            Div(
                Text(f"Your score is {state.score:.1f}"),
                Button(
                    "Save Game",
                    save_game,
                    id="save-button",
                    style_color="green",
                ),
            ),
        ],
    )


def section(title: str) -> None:
    """Print a heading that makes the example output easier to scan."""
    print(f"\n--- {title} ---")


page = dashboard(State("Ada", 9.5))
details = page.content[1]
save_button = details.content[1]


section("Whole values and pages")

# assert_equal recursively compares ordinary values, collections, dataclasses,
# Drafter components, and Pages. Its failure points to the nested difference.
assert_equal({"scores": [8, 9.5]}, {"scores": [8, 9.50001]})  # Passes
assert_equal({"scores": [8, 9.5]}, {"scores": [8, 10]})  # Fails

assert_page(page, dashboard(State("Ada", 9.5)))  # Passes
assert_page(page, dashboard(State("Grace", 7.0)))  # Fails: state and content


section("State and content")

# These assertions test one half of a Page while ignoring the other half.
assert_state(page, State("Ada", 9.5))  # Passes
assert_state(page, State("Ada", 10.0))  # Fails

same_content_different_state = Page(State("Someone else", 0.0), page.content)
assert_content(page, same_content_different_state)  # Passes
assert_content(page, [Header("A different dashboard")])  # Fails


section("Finding content anywhere in a page")

# Strings can be partial, case-insensitive matches. Components can be nested,
# and their styles are ignored unless strict_styles=True is requested.
assert_has(page, "SCORE IS")  # Passes: partial text in the nested Div
assert_has(page, Button("Save Game", save_game))  # Passes: nested component
assert_has(page, "Game Over")  # Fails and lists the text that was present

# assert_in is the same search with Python's "needle, container" order.
assert_in("Welcome, Ada", page)  # Passes
assert_in("Welcome, Lin", page)  # Fails

assert_not_has(page, "Game Over")  # Passes
assert_not_has(page, "Save Game")  # Fails and shows where it was found

# assert_not_in also uses Python's argument order.
assert_not_in("Delete Game", page)  # Passes
assert_not_in("Your score", page)  # Fails


section("Regular expressions")

# Regex searches inspect every visible piece of text and ignore case by default.
assert_has_regex(page, r"score is \d+\.\d")  # Passes
assert_has_regex(page, r"lives remaining: \d+")  # Fails

# assert_in_regex provides the pattern-first spelling.
assert_in_regex(r"welcome, [a-z]+!", page)  # Passes
assert_in_regex(r"goodbye, [a-z]+!", page)  # Fails


section("Inspecting one component")

# Declared fields, extra HTML settings, and route functions are all supported.
assert_attribute(save_button, "text", "Save Game")  # Passes
assert_attribute(save_button, "url", save_game)  # Passes
assert_attribute(save_button, "id", "wrong-button")  # Fails

# Style names may use CSS hyphens or Python underscores.
assert_style(save_button, "color", "green")  # Passes
assert_style(save_button, "background-color", "green")  # Fails

# A single expected child is automatically treated as a one-item list.
assert_children(details, ["Your score is 9.5", save_button])  # Passes
assert_children(details, "Your score is 9.5")  # Fails: missing the button

# assert_text combines visible text and ignores component structure and
# whitespace. Pass exact_strings=True when capitalization and spacing matter.
assert_text(details, "your score is 9.5 save game")  # Passes
assert_text(details, "Your score is 9.5", exact_strings=True)  # Fails


section("Controlling comparisons")

# Floats match to four decimal places and strings are loose by default.
assert_equal(0.30001, 0.3)  # Passes at the default precision
assert_equal(0.30001, 0.3, precision=5)  # Fails with tighter precision
assert_equal("  HELLO  ", "hello")  # Passes
assert_equal("  HELLO  ", "hello", exact_strings=True)  # Fails

green_button = Button("Save Game", save_game, style_color="green")
blue_button = Button("Save Game", save_game, style_color="blue")
assert_equal(green_button, blue_button)  # Passes because styles are ignored
assert_equal(green_button, blue_button, strict_styles=True)  # Fails

# Defaults affect later assertions, but any individual call can override them.
set_assertion_defaults(precision=2, exact_strings=True, strict_styles=True)
assert_equal(1.004, 1.0)  # Passes with the new precision default
assert_equal("Hello", "hello")  # Fails with exact string matching enabled
assert_equal(green_button, blue_button, strict_styles=False)  # Passes: override

# quiet=True hides only a passing SUCCESS line; failures are always reported.
assert_equal("quiet pass", "quiet pass", quiet=True)

# The same behavior can be the default for a group of tests. Notice that the
# first call prints nothing, while the intentional failure is still visible.
set_assertion_defaults(report_success=False)
assert_equal("hidden success", "hidden success")
assert_equal("visible failure", "different")  # Fails

# Restore Drafter's normal defaults for code that imports this example.
set_assertion_defaults(
    precision=4,
    exact_strings=False,
    strict_styles=False,
    report_success=True,
)
