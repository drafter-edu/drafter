import pytest
from drafter import *
from drafter.components import plotting as _plotting_components
from tests.components.helpers import eval_drafter_with_source
from drafter.testing.assertions import (
    compare_equal,
    render_difference,
    ComparisonSettings,
    render_path,
    search_content,
)

snippets = {
    "buttons": {
        "blue_button_with_attrs": (
            """Button('Hello World', '/link')""",
            """Button('Hello World', '/link', style_color='blue')""",
            [""],
        ),
        "message_of_button": (
            """Button('Hello World', '/link')""",
            """'Hello World'""",
            ["Button text"],
        ),
        "missing_message_in_button": (
            """Button('Hello World', '/link')""",
            """'Goodbye World'""",
            [],
        ),
        "text_hidden_in_divs": (
            """Div(Div(Div(Button('Click Me', '/link'))))""",
            """'Click Me'""",
            [
                "Div content (item 0) Div content (item 0) Div content (item 0) Button text"
            ],
        ),
        "button_hidden_in_divs": (
            """Div(Div(Div(Button('Click Me', '/link'))))""",
            """Button('Click Me', '/link')""",
            ["Div content (item 0) Div content (item 0) Div content (item 0)"],
        ),
    }
}


@pytest.mark.parametrize(
    "category,name,snippet",
    [
        pytest.param(category, name, snippet, id=f"{category} :: {name}")
        for category, group in snippets.items()
        for name, snippet in group.items()
    ],
)
def test_snippet_equal_to_itself(category, name, snippet):
    actual, expected, expected_differences = snippet
    obj1 = eval_drafter_with_source(actual, "equal_to_itself", category, name)
    diff1 = compare_equal(obj1, obj1, ComparisonSettings(), [])
    diff1_rendered = [render_difference(d) for d in diff1]

    assert diff1 == [], (
        f"{category} / {name} / first: expected no differences when comparing the first snippet to itself.\n"
        f"Actual differences:\n{diff1_rendered}"
    )

    obj2 = eval_drafter_with_source(expected, "equal_to_itself", category, name)
    diff2 = compare_equal(obj2, obj2, ComparisonSettings(), [])
    diff2_rendered = [render_difference(d) for d in diff2]

    assert diff2 == [], (
        f"{category} / {name} / second: expected no differences when comparing the second snippet to itself.\n"
        f"Actual differences:\n{diff2_rendered}"
    )


@pytest.mark.parametrize(
    "category,name,snippet",
    [
        pytest.param(category, name, snippet, id=f"{category} :: {name}")
        for category, group in snippets.items()
        for name, snippet in group.items()
    ],
)
def test_snippet_found_in_target(category, name, snippet):
    actual, needle, paths = snippet
    obj1 = eval_drafter_with_source(actual, "search", category, name)
    obj2 = eval_drafter_with_source(needle, "search", category, name)
    found_paths = search_content(obj1, obj2, ComparisonSettings(), [])
    paths_rendered = [render_path(p) for p in found_paths]
    print("Paths:", found_paths)

    if len(paths) != len(paths_rendered):
        for expected_path in paths:
            assert expected_path in paths_rendered, (
                f"{category} / {name}: expected path not found.\n"
                f"Expected path:\n{expected_path}\n"
                f"Actual paths:\n{paths_rendered}"
            )
        for actual_path in paths_rendered:
            assert actual_path in paths, (
                f"{category} / {name}: unexpected path found.\n"
                f"Expected paths:\n{paths}\n"
                f"Actual path:\n{actual_path}"
            )
    for actual_path, expected_path in zip(paths_rendered, paths):
        assert actual_path == expected_path, (
            f"{category} / {name}: path mismatch.\n"
            f"Expected path:\n{expected_path}\n"
            f"Actual path:\n{actual_path}"
        )
