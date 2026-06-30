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
    "links": {
        "simple_link_equal": (
            """Link('Hello World', '/link')""",
            """Link('Hello World', '/link', style_color='blue')""",
            [],
        ),
        "link_with_different_text": (
            """Link('Hello World', '/link')""",
            """Link('Goodbye World', '/link')""",
            ["In Link text: Expected 'Goodbye World' but got 'Hello World'"],
        ),
        "link_with_different_url": (
            """Link('Hello World', '/link')""",
            """Link('Hello World', '/other-link')""",
            ["In Link url: Expected 'other-link' but got 'link'"],
        ),
        "link_is_not_button": (
            """Link('Hello World', '/link')""",
            """Button('Hello World', '/link')""",
            ["Expected type Button but got type Link"],
        ),
    },
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
    "headers": {
        "simple_header_equal": (
            """Header('Hello World')""",
            """Header('Hello World', style_color='blue')""",
            [],
        ),
        "header_with_different_body": (
            """Header('Hello World')""",
            """Header('Goodbye World')""",
            ["In Header body: Expected 'Goodbye World' but got 'Hello World'"],
        ),
        "header_level_mismatch": (
            """Header('Hello World', level=1)""",
            """Header('Hello World', level=2)""",
            ["In Header: Expected values missing in level (item 0)"],
        ),
        "h1_equal_to_itself": (
            """Header('Title', level=1)""",
            """Header('Title', level=1)""",
            [],
        ),
        "header_different_levels_and_text": (
            """Header('Welcome', level=1)""",
            """Header('Goodbye', level=3)""",
            [
                "In Header body: Expected 'Goodbye' but got 'Welcome'",
                "In Header: Expected values missing in level (item 0)",
            ],
        ),
    },
    "paragraphs": {
        "simple_paragraph_equal": (
            """Paragraph('Hello World')""",
            """Paragraph('Hello World', style_color='red')""",
            [],
        ),
        "paragraph_with_different_content": (
            """Paragraph('Hello World')""",
            """Paragraph('Goodbye World')""",
            ["In Paragraph content (item 0): Expected 'Goodbye World' but got 'Hello World'"],
        ),
        "paragraph_with_extra_content": (
            """Paragraph('Hello World')""",
            """Paragraph('Hello World', 'More Text')""",
            ["In Paragraph: Expected values missing in content (item 1)"],
        ),
        "paragraph_is_not_div": (
            """Div('Hello World')""",
            """Paragraph('Hello World')""",
            ["Expected type Paragraph but got type Div"],
        ),
    },
    "spans": {
        "simple_span_equal": (
            """Span('Hello World')""",
            """Span('Hello World', style_color='blue')""",
            [],
        ),
        "span_with_different_content": (
            """Span('Hello World')""",
            """Span('Goodbye World')""",
            ["In Span content (item 0): Expected 'Goodbye World' but got 'Hello World'"],
        ),
        "span_with_nested_button": (
            """Span(Button('Click', '/link'))""",
            """Span(Button('Click', '/link', style_color='green'))""",
            [],
        ),
        "span_with_different_nested_button": (
            """Span(Button('Click', '/link'))""",
            """Span(Button('Do Not Click', '/link'))""",
            ["In Span content (item 0) Button text: Expected 'Do Not Click' but got 'Click'"],
        ),
    },
    "lists": {
        "bulleted_list_equal": (
            """BulletedList(['Apple', 'Banana', 'Cherry'])""",
            """BulletedList(['Apple', 'Banana', 'Cherry'])""",
            [],
        ),
        "numbered_list_equal": (
            """NumberedList(['First', 'Second', 'Third'])""",
            """NumberedList(['First', 'Second', 'Third'])""",
            [],
        ),
        "bulleted_list_is_not_numbered_list": (
            """BulletedList(['Apple', 'Banana'])""",
            """NumberedList(['Apple', 'Banana'])""",
            ["Expected type NumberedList but got type BulletedList"],
        ),
    },
    "form_inputs": {
        "textbox_equal": (
            """TextBox('username')""",
            """TextBox('username')""",
            [],
        ),
        "textbox_different_default_value": (
            """TextBox('username', default_value='alice')""",
            """TextBox('username', default_value='bob')""",
            ["In TextBox default_value (item 0): Expected 'bob' but got 'alice'"],
        ),
        "checkbox_equal": (
            """CheckBox('agree')""",
            """CheckBox('agree')""",
            [],
        ),
        "checkbox_different_default": (
            """CheckBox('agree', default_value=False)""",
            """CheckBox('agree', default_value=True)""",
            ["In CheckBox: Expected values missing in default_value (item 0)"],
        ),
        "selectbox_equal": (
            """SelectBox('color', ['red', 'green', 'blue'])""",
            """SelectBox('color', ['red', 'green', 'blue'])""",
            [],
        ),
        "selectbox_different_options": (
            """SelectBox('color', ['red', 'green', 'blue'])""",
            """SelectBox('color', ['red', 'yellow', 'blue'])""",
            ["In SelectBox options index '1': Expected 'yellow' but got 'green'"],
        ),
    },
    "images": {
        "image_equal": (
            """Image('https://example.com/image.png')""",
            """Image('https://example.com/image.png')""",
            [],
        ),
        "image_with_style_equal": (
            """Image('https://example.com/image.png')""",
            """Image('https://example.com/image.png', style_border='1px solid')""",
            [],
        ),
        "image_different_url": (
            """Image('https://example.com/image.png')""",
            """Image('https://example.com/other.png')""",
            ["In Image url: Expected 'https://example.com/other.png' but got 'https://example.com/image.png'"],
        ),
        "image_different_width": (
            """Image('https://example.com/image.png', width=100)""",
            """Image('https://example.com/image.png', width=200)""",
            ["In Image width (item 0): Expected 200 but got 100"],
        ),
    },
    "semantic_containers": {
        "section_equal": (
            """Section('Hello World')""",
            """Section('Hello World', style_color='blue')""",
            [],
        ),
        "section_different_content": (
            """Section('Hello World')""",
            """Section('Goodbye World')""",
            ["In Section content (item 0): Expected 'Goodbye World' but got 'Hello World'"],
        ),
        "article_equal": (
            """Article(Header('Title'), Paragraph('Body text'))""",
            """Article(Header('Title'), Paragraph('Body text'))""",
            [],
        ),
        "article_different_header": (
            """Article(Header('Title'), Paragraph('Body text'))""",
            """Article(Header('Other Title'), Paragraph('Body text'))""",
            ["In Article content (item 0) Header body: Expected 'Other Title' but got 'Title'"],
        ),
        "section_is_not_div": (
            """Div('Hello World')""",
            """Section('Hello World')""",
            ["Expected type Section but got type Div"],
        ),
        "aside_equal": (
            """Aside('Sidebar content')""",
            """Aside('Sidebar content')""",
            [],
        ),
        "nav_with_links_equal": (
            """Nav(Link('Home', '/'), Link('About', '/about'))""",
            """Nav(Link('Home', '/'), Link('About', '/about'))""",
            [],
        ),
        "nav_with_different_link_text": (
            """Nav(Link('Home', '/'), Link('About', '/about'))""",
            """Nav(Link('Home', '/'), Link('Contact', '/about'))""",
            ["In Nav content (item 1) Link text: Expected 'Contact' but got 'About'"],
        ),
        "nav_with_different_link_url": (
            """Nav(Link('Home', '/'), Link('About', '/about'))""",
            """Nav(Link('Home', '/'), Link('About', '/contact'))""",
            ["In Nav content (item 1) Link url: Expected 'contact' but got 'about'"],
        ),
    },
    "deeply_nested": {
        "three_levels_equal": (
            """Section(Article(Div('Deep content')))""",
            """Section(Article(Div('Deep content', style_color='red')))""",
            [],
        ),
        "three_levels_different_content": (
            """Section(Article(Div('Deep content')))""",
            """Section(Article(Div('Changed content')))""",
            [
                "In Section content (item 0) Article content (item 0) Div content (item 0): Expected 'Changed content' but got 'Deep content'"
            ],
        ),
        "four_levels_equal": (
            """Div(Section(Article(Paragraph('Very deep'))))""",
            """Div(Section(Article(Paragraph('Very deep'))))""",
            [],
        ),
        "four_levels_different": (
            """Div(Section(Article(Paragraph('Very deep'))))""",
            """Div(Section(Article(Paragraph('Changed'))))""",
            [
                "In Div content (item 0) Section content (item 0) Article content (item 0) Paragraph content (item 0): Expected 'Changed' but got 'Very deep'"
            ],
        ),
        "deep_form_in_div": (
            """Div(Div(TextBox('username')))""",
            """Div(Div(TextBox('username')))""",
            [],
        ),
        "deep_form_different_value": (
            """Div(Div(TextBox('username', default_value='alice')))""",
            """Div(Div(TextBox('username', default_value='bob')))""",
            [
                "In Div content (item 0) Div content (item 0) TextBox default_value (item 0): Expected 'bob' but got 'alice'"
            ],
        ),
        "deep_button_in_nav": (
            """Nav(Div(Span(Button('Click', '/link'))))""",
            """Nav(Div(Span(Button('Do Not Click', '/link'))))""",
            [
                "In Nav content (item 0) Div content (item 0) Span content (item 0) Button text: Expected 'Do Not Click' but got 'Click'"
            ],
        ),
        "five_levels_different": (
            """Section(Article(Div(Paragraph(Span('Very very deep')))))""",
            """Section(Article(Div(Paragraph(Span('Changed deep')))))""",
            [
                "In Section content (item 0) Article content (item 0) Div content (item 0) Paragraph content (item 0) Span content (item 0): Expected 'Changed deep' but got 'Very very deep'"
            ],
        ),
    },
    "mixed_siblings": {
        "header_and_paragraph": (
            """Div(Header('Title'), Paragraph('Body'))""",
            """Div(Header('Title'), Paragraph('Body'))""",
            [],
        ),
        "header_and_paragraph_different_body": (
            """Div(Header('Title'), Paragraph('Body'))""",
            """Div(Header('Title'), Paragraph('Different Body'))""",
            [
                "In Div content (item 1) Paragraph content (item 0): Expected 'Different Body' but got 'Body'"
            ],
        ),
        "list_inside_section": (
            """Section(BulletedList(['A', 'B', 'C']))""",
            """Section(BulletedList(['A', 'B', 'C']))""",
            [],
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
