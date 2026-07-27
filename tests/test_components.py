import pytest
from drafter import *

snippets = {
    "button": {
        "regular": "Button('Hello World', 'index')",
        "external_link": "Button('External Link', 'http://example.com')",
        "with_arguments": """Button('With Args', 'next_page', arguments=[
    Argument('first', 'first_value'),
    Argument('second', 'second_value'),
])""",
        "with_style": """Button("Red", "next", style_font_color="red")""",
        "with_attributes": """Button("Attrs", "next", id="mybutton", style_background_color="#00FF00")""",
        "with_mystery_attr": """Button("Mystery Attr", "next", mystery_attr="mystery_value")""",
        "with_classes": """Button("Classy", "next", classes=["class1", "class2"])""",
        "with_class": """Button("Single Class", "next", classes=["single_class"])""",
    },
    "argument": {
        "simple": """Argument('param', 'value')""",
        "with_style": """Argument('styled_param', 'styled_value', style_font_weight="bold")""",
        "with_attributes": """Argument('attr_param', 'attr_value', id="arg1", style_font_style="italic")""",
    },

    "span": {
        "simple": """Span('Hello world!')""",
        "with_style": """Span('Styled text', style_font_size="20px", style_color="#333333")""",
        "with_attributes": """Span('Attributed text', id="myspan", style_text_decoration="underline")""",

    },
    "ol": {
        "simple": """NumberedList(['First item', 'Second item', 'Third item'])""",
        "with_style": """NumberedList(['Styled item'], style_margin_left="20px", style_color="#555555")""",
    },
    "ul": {
        "simple": """BulletedList(['First item', 'Second item', 'Third item'])""",
        "with_style": """BulletedList(['Styled item'], style_margin_left="20px", style_color="#555555")""",
    },
    "header": {
        "h1": """Header('This is a level 1 header', level=1)""",
        "h2": """Header('This is a level 2 header', level=2)""",
        "h3": """Header('This is a level 3 header', level=3)""",
        "with_style": """Header('Styled Header', level=2, style_text_align="center", style_color="#0000FF")""",
    },

    "text": {
        "simple": """Text('This is a simple text component.')""",
        "with_style": """Text('Styled text component.', style_font_family='Arial', style_font_size='16px')""",
    },

    "row": {
        "simple": """Row(['Hello world!', 'This is a row.'])""",
        "with_style": """Row(['Styled row'], style_background_color="#DDDDDD", style_padding="10px")""",
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
def test_snippet_consistent(category, name, snippet):
    obj1 = eval(snippet)
    obj2 = eval(snippet)

    # These assertion messages will show up in test failures and
    # make it obvious *which* snippet failed and why.
    assert obj1 == obj2, (
        f"{category} / {name}: evaluating the snippet twice "
        f"should produce equal objects.\nSnippet:\n{snippet}"
    )

@pytest.mark.parametrize(
    "category,name,snippet",
    [
        pytest.param(category, name, snippet, id=f"{category} :: {name}")
        for category, group in snippets.items()
        for name, snippet in group.items()
    ],
)
def test_snippet_repr(category, name, snippet):
    obj1 = eval(snippet)
    obj2 = eval(repr(obj1))

    assert obj1 == obj2, (
        f"{category} / {name}: repr(obj) did not match the snippet.\n\n"
        f"Snippet:\n{snippet}\n\nrepr(obj):\n{repr(obj1)}"
    )
