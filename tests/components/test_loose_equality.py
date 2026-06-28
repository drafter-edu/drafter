import pytest
from drafter import *
from drafter.components import plotting as _plotting_components
from tests.components.helpers import eval_drafter_with_source
from drafter.testing.assertions import (
    compare_equal,
    render_difference,
    ComparisonSettings,
)

snippets = {
    "buttons": {
        "blue_button_with_attrs": (
            """Button('Hello World', '/link')""",
            """Button('Hello World', '/link', style_color='blue')""",
            [],
        ),
        "classy_button_with_normalized_link": (
            """Button('Hello World', '/link')""",
            """Button('Hello World', 'link', classes=['classy'])""",
            [],
        ),
        "blue_button_with_different_label": (
            """Button('Hello World', '/link')""",
            """Button('Goodbye World', '/link', style_color='blue')""",
            ["In Button text: Expected 'Goodbye World' but got 'Hello World'"],
        ),
        "blue_button_with_different_link": (
            """Button('Hello World', '/link')""",
            """Button('Hello World', 'different-link', style_color='blue')""",
            ["In Button url: Expected 'different-link' but got 'link'"],
        ),
        "buttons_are_not_text": (
            """'Hello World'""",
            """Button('Hello World', '/link')""",
            ["Expected type Button but got type str"],
        ),
        "text_is_not_buttons": (
            """Button('Hello World', '/link')""",
            """'Hello World'""",
            ["Expected type str but got type Button"],
        ),
    },
    "div": {
        "simple_div": (
            """Div('Hello World')""",
            """Div('Hello World', style_color='blue')""",
            [],
        ),
        "div_with_different_content": (
            """Div('Hello World')""",
            """Div('Goodbye World', style_color='blue')""",
            ["In Div content (item 0): Expected 'Goodbye World' but got 'Hello World'"],
        ),
        "div_with_more_content": (
            """Div('Hello World')""",
            """Div('Hello World', 'Additional Content', style_color='blue')""",
            ["In Div: Expected values missing in content (item 1)"],
        ),
        "div_with_much_extra_content": (
            """Div('Hello World')""",
            """Div('Hello World', 'Additional Content', 'More Content', style_color='blue')""",
            [
                "In Div: Expected values missing in content (item 1), content (item 2)",
            ],
        ),
        "div_with_missing_content": (
            """Div('Hello World', 'Additional Content', style_color='blue')""",
            """Div('Hello World')""",
            ["In Div: Unexpected extra values found in content (item 1)"],
        ),
    },
    "nested_divs": {
        "simple_nested_div": (
            """Div(Div('Hello World'))""",
            """Div(Div('Hello World', style_color='blue'))""",
            [],
        ),
        "nested_div_with_button_inside": (
            """Div(Div('Hello World', Button('Click Me', 'link', style_color='red')))""",
            """Div(Div('Hello World', Button('Click Me', 'link', style_color='blue')))""",
            [],
        ),
        "nested_div_with_different_button_inside": (
            """Div(Div('Hello World', Button('Click Me', 'link', style_color='red')))""",
            """Div(Div('Hello World', Button('Do NOT Click Me', 'link', style_color='blue')))""",
            [
                "In Div content (item 0) Div content (item 1) Button text: Expected 'Do NOT Click Me' but got 'Click Me'"
            ],
        ),
        "nested_div_with_different_content": (
            """Div(Div('Hello World'))""",
            """Div(Div('Goodbye World', style_color='blue'))""",
            [
                "In Div content (item 0) Div content (item 0): Expected 'Goodbye World' but got 'Hello World'"
            ],
        ),
    },
    "text_directly_comparable": {
        "simple_text_equality": (
            """'Hello World'""",
            """'Hello World'""",
            [],
        ),
        "string_inequality_detected": (
            """'Hello World'""",
            """'Goodbye World'""",
            ["Expected 'Goodbye World' but got 'Hello World'"],
        ),
        "component_equal_to_text": (
            """Text("Hello world!")""",
            """'Hello World!'""",
            [],
        ),
        "text_equal_to_component": (
            """'Hello World!'""",
            """Text("Hello world!")""",
            [],
        ),
        "component_unequal_to_text": (
            """Text("Hello world!")""",
            """'Goodbye World!'""",
            ["In text body: Expected 'Goodbye World!' but got 'Hello world!'"],
        ),
        "text_unequal_to_component": (
            """'Goodbye World!'""",
            """Text("Hello world!")""",
            ["In text body: Expected 'Hello world!' but got 'Goodbye World!'"],
        ),
        "ignore_styled_text": (
            """bold('Bolded action')""",
            """'Bolded action'""",
            [],
        ),
        "ignore_styled_text_reverse": (
            """'Bolded action'""",
            """bold('Bolded action')""",
            [],
        ),
    },
    "very_different_things": {
        "completely_different": (
            """Div('Hello World')""",
            """Button('Click Me', 'link', style_color='red')""",
            ["Expected type Button but got type Div"],
        ),
        "div_with_slightly_changed_middle": (
            """Div('Hello World', 'Middle Content', 'Additional Content', style_color='blue')""",
            """Div('Hello World', 'Changed Middle Content', 'Additional Content', style_color='blue')""",
            [
                "In Div content (item 1): Expected 'Changed Middle Content' but got 'Middle Content'"
            ],
        ),
    },
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
def test_snippet_equal_to_target(category, name, snippet):
    actual, expected, expected_differences = snippet
    obj1 = eval_drafter_with_source(actual, "equal", category, name)
    obj2 = eval_drafter_with_source(expected, "equal", category, name)
    differences = compare_equal(obj1, obj2, ComparisonSettings(), [])
    print("Differences:", differences)
    differences_rendered = [render_difference(d) for d in differences]

    if len(differences) != len(expected_differences):
        for expected_diff in expected_differences:
            assert expected_diff in differences_rendered, (
                f"{category} / {name}: expected difference not found.\n"
                f"Expected difference:\n{expected_diff}\n"
                f"Actual differences:\n{differences_rendered}"
            )
        for actual_diff in differences_rendered:
            assert actual_diff in expected_differences, (
                f"{category} / {name}: unexpected difference found.\n"
                f"Expected differences:\n{expected_differences}\n"
                f"Actual difference:\n{actual_diff}"
            )
    for actual_diff, expected_diff in zip(differences_rendered, expected_differences):
        assert actual_diff == expected_diff, (
            f"{category} / {name}: difference mismatch.\n"
            f"Expected difference:\n{expected_diff}\n"
            f"Actual difference:\n{actual_diff}"
        )
