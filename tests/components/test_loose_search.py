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
    },
    "links": {
        "link_found_in_nav": (
            """Nav(Link('Home', '/'), Link('About', '/about'))""",
            """Link('Home', '/')""",
            ["Nav content (item 0)"],
        ),
        "link_text_in_nav": (
            """Nav(Link('Home', '/'), Link('About', '/about'))""",
            """'Home'""",
            ["Nav content (item 0) Link text"],
        ),
        "missing_link_text_in_nav": (
            """Nav(Link('Home', '/'), Link('About', '/about'))""",
            """'Contact'""",
            [],
        ),
    },
    "headers": {
        "text_in_header": (
            """Header('Welcome to the Site')""",
            """'Welcome to the Site'""",
            ["Header body"],
        ),
        "missing_text_in_header": (
            """Header('Welcome to the Site')""",
            """'Goodbye'""",
            [],
        ),
        "header_in_article": (
            """Article(Header('Title'), Paragraph('Body'))""",
            """Header('Title')""",
            ["Article content (item 0)"],
        ),
    },
    "paragraphs_and_sections": {
        "text_in_paragraph": (
            """Section(Paragraph('Some content here'))""",
            """'Some content here'""",
            ["Section content (item 0) Paragraph content (item 0)"],
        ),
        "button_deep_in_section": (
            """Section(Article(Div(Button('Click', '/link'))))""",
            """Button('Click', '/link')""",
            ["Section content (item 0) Article content (item 0) Div content (item 0)"],
        ),
        "text_four_levels_deep": (
            """Section(Article(Div(Paragraph('Deep text'))))""",
            """'Deep text'""",
            [
                "Section content (item 0) Article content (item 0) Div content (item 0) Paragraph content (item 0)"
            ],
        ),
        "span_text_in_section": (
            """Section(Span('Highlighted text'))""",
            """'Highlighted text'""",
            ["Section content (item 0) Span content (item 0)"],
        ),
        "text_five_levels_deep": (
            """Section(Article(Div(Paragraph(Span('Very deep text')))))""",
            """'Very deep text'""",
            [
                "Section content (item 0) Article content (item 0) Div content (item 0) Paragraph content (item 0) Span content (item 0)"
            ],
        ),
    },
    "multiple_matches": {
        "same_text_appears_twice": (
            """Div('Hello', 'World', 'Hello')""",
            """'Hello'""",
            ["Div content (item 0)", "Div content (item 2)"],
        ),
        "link_text_in_mixed_container": (
            """Div(Link('About Us', '/about'), Link('Contact', '/contact'))""",
            """'About Us'""",
            ["Div content (item 0) Link text"],
        ),
    },
    "forms": {
        "textbox_in_div": (
            """Div(TextBox('username', default_value='alice'))""",
            """TextBox('username', default_value='alice')""",
            ["Div content (item 0)"],
        ),
        "textbox_missing": (
            """Div(TextBox('username', default_value='alice'))""",
            """TextBox('username', default_value='bob')""",
            [],
        ),
    },
    "images": {
        "image_in_div": (
            """Div(Image('https://example.com/img.png'))""",
            """Image('https://example.com/img.png')""",
            ["Div content (item 0)"],
        ),
        "missing_image": (
            """Div(Image('https://example.com/img.png'))""",
            """Image('https://example.com/other.png')""",
            [],
        ),
    },
    "page_and_fragment": {
        # Page: link found inside HeaderContent > Nav
        "page_link_in_header_nav": (
            """Page(None, [
    HeaderContent(
        Nav(Link('Home', '/'), Link('About', '/about'), Link('Contact', '/contact'))
    ),
    Main(
        Section(
            Header('Welcome', level=1),
            Paragraph('This is the home page.'),
            Button('Get Started', '/start'),
        )
    ),
    FooterContent('2024 My Site')
])""",
            """Link('Contact', '/contact')""",
            ["index '0' HeaderContent content (item 0) Nav content (item 2)"],
        ),
        # Page: text found deep inside Main > Section > Header
        "page_text_in_nested_section": (
            """Page(None, [
    HeaderContent(
        Nav(Link('Home', '/'), Link('About', '/about'), Link('Contact', '/contact'))
    ),
    Main(
        Section(
            Header('Welcome', level=1),
            Paragraph('This is the home page.'),
            Button('Get Started', '/start'),
        )
    ),
    FooterContent('2024 My Site')
])""",
            """'Welcome'""",
            ["index '1' Main content (item 0) Section content (item 0) Header body"],
        ),
        # Page: Paragraph found in Main > Section
        "page_paragraph_in_main": (
            """Page(None, [
    HeaderContent(
        Nav(Link('Home', '/'), Link('About', '/about'), Link('Contact', '/contact'))
    ),
    Main(
        Section(
            Header('Welcome', level=1),
            Paragraph('This is the home page.'),
            Button('Get Started', '/start'),
        )
    ),
    FooterContent('2024 My Site')
])""",
            """Paragraph('This is the home page.')""",
            ["index '1' Main content (item 0) Section content (item 1)"],
        ),
        # Page: Button found in Main > Section
        "page_button_in_section": (
            """Page(None, [
    HeaderContent(
        Nav(Link('Home', '/'), Link('About', '/about'), Link('Contact', '/contact'))
    ),
    Main(
        Section(
            Header('Welcome', level=1),
            Paragraph('This is the home page.'),
            Button('Get Started', '/start'),
        )
    ),
    FooterContent('2024 My Site')
])""",
            """Button('Get Started', '/start')""",
            ["index '1' Main content (item 0) Section content (item 2)"],
        ),
        # Page: FooterContent found at top-level content list (index 2)
        "page_footer_at_top_level": (
            """Page(None, [
    HeaderContent(
        Nav(Link('Home', '/'), Link('About', '/about'), Link('Contact', '/contact'))
    ),
    Main(
        Section(
            Header('Welcome', level=1),
            Paragraph('This is the home page.'),
            Button('Get Started', '/start'),
        )
    ),
    FooterContent('2024 My Site')
])""",
            """FooterContent('2024 My Site')""",
            ["index '2'"],
        ),
        # Page: missing element returns empty list
        "page_missing_link": (
            """Page(None, [
    HeaderContent(
        Nav(Link('Home', '/'), Link('About', '/about'), Link('Contact', '/contact'))
    ),
    Main(
        Section(
            Header('Welcome', level=1),
            Paragraph('This is the home page.'),
            Button('Get Started', '/start'),
        )
    ),
    FooterContent('2024 My Site')
])""",
            """Link('Shop', '/shop')""",
            [],
        ),
        # Page: same button text appears three times, each found via a distinct path
        "page_multiple_button_text_matches": (
            """Page(None, [
    Section(
        Article(Header('Post 1'), Button('Read More', '/post/1')),
        Article(Header('Post 2'), Button('Read More', '/post/2')),
        Article(Header('Post 3'), Button('Read More', '/post/3')),
    )
])""",
            """'Read More'""",
            [
                "index '0' Section content (item 0) Article content (item 1) Button text",
                "index '0' Section content (item 1) Article content (item 1) Button text",
                "index '0' Section content (item 2) Article content (item 1) Button text",
            ],
        ),
        # Page: one specific button among many similar ones
        "page_specific_button_among_many": (
            """Page(None, [
    Section(
        Article(Header('Post 1'), Button('Read More', '/post/1')),
        Article(Header('Post 2'), Button('Read More', '/post/2')),
        Article(Header('Post 3'), Button('Read More', '/post/3')),
    )
])""",
            """Button('Read More', '/post/2')""",
            ["index '0' Section content (item 1) Article content (item 1)"],
        ),
        # Fragment: Header found at the top of the Fragment content list
        "fragment_header_at_top": (
            """Fragment(None, [
    Header('Edit Profile', level=2),
    TextBox('username', default_value='alice'),
    SelectBox('theme', ['light', 'dark', 'auto']),
    Button('Save', '/save'),
])""",
            """Header('Edit Profile', level=2)""",
            ["index '0'"],
        ),
        # Fragment: SelectBox found by component equality
        "fragment_selectbox": (
            """Fragment(None, [
    Header('Edit Profile', level=2),
    TextBox('username', default_value='alice'),
    SelectBox('theme', ['light', 'dark', 'auto']),
    Button('Save', '/save'),
])""",
            """SelectBox('theme', ['light', 'dark', 'auto'])""",
            ["index '2'"],
        ),
        # Fragment: Button found by component equality
        "fragment_save_button": (
            """Fragment(None, [
    Header('Edit Profile', level=2),
    TextBox('username', default_value='alice'),
    SelectBox('theme', ['light', 'dark', 'auto']),
    Button('Save', '/save'),
])""",
            """Button('Save', '/save')""",
            ["index '3'"],
        ),
        # Fragment: nested Div with link
        "fragment_link_in_div": (
            """Fragment(None, [
    Div(
        Paragraph('Click below to continue:'),
        Link('Continue', '/next'),
    )
])""",
            """Link('Continue', '/next')""",
            ["index '0' Div content (item 1)"],
        ),
        # Fragment: missing element returns empty list
        "fragment_missing_button": (
            """Fragment(None, [
    Header('Edit Profile', level=2),
    TextBox('username', default_value='alice'),
    Button('Save', '/save'),
])""",
            """Button('Delete', '/delete')""",
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
