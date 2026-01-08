from drafter import TextBox, Span, Div, BulletedList, TextArea


def test_textbox_repr():
    just_name = TextBox("some_name")
    assert repr(just_name) == "TextBox('some_name')"

    without_default = TextBox("some_name", kind="password")
    assert repr(without_default) == "TextBox('some_name', kind='password')"

    with_default = TextBox("some_name", "Starting Text")
    assert repr(with_default) == "TextBox('some_name', 'Starting Text')"

    with_kind = TextBox("some_name", "Starting Text", "password")
    assert repr(with_kind) == "TextBox('some_name', 'Starting Text', 'password')"

    with_aria = TextBox(
        "some_name", "Starting Text", kind="password", aria_label="Custom Aria Label"
    )
    assert (
        repr(with_aria)
        == "TextBox('some_name', 'Starting Text', 'password', aria_label='Custom Aria Label')"
    )

    with_keyword_args = TextBox(
        "some_name",
        kind="password",
        default_value="Starting Text",
        aria_label="Custom Aria Label",
    )
    assert (
        repr(with_keyword_args)
        == "TextBox('some_name', 'Starting Text', 'password', aria_label='Custom Aria Label')"
    )

    with_styling = TextBox(
        "some_name", "Starting Text", style_font_size="14px", style_color="red"
    )
    assert (
        repr(with_styling)
        == "TextBox('some_name', 'Starting Text', style_color='red', style_font_size='14px')"
    )


def test_variable_content():
    span = Span("Hello", "World")
    assert repr(span) == "Span('Hello', 'World')"

    span_with_kwargs = Span("Hello", "World", style_color="blue")
    assert repr(span_with_kwargs) == "Span('Hello', 'World', style_color='blue')"


def test_positional_content():
    items = [Span("Item 1"), Span("Item 2"), Span("Item 3")]
    bulleted_list = BulletedList(items)
    assert (
        repr(bulleted_list)
        == "BulletedList([Span('Item 1'), Span('Item 2'), Span('Item 3')])"
    )


def test_keyword_content():
    text_area = TextArea(
        "instructions",
        style_width="100%",
        default_value="This will go inside",
    )
    assert (
        repr(text_area)
        == "TextArea('instructions', 'This will go inside', style_width='100%')"
    )

    text_area_no_default = TextArea(
        "instructions",
        style_width="100%",
    )
    assert repr(text_area_no_default) == "TextArea('instructions', style_width='100%')"


def test_update_attr():
    div = TextBox("name", "Default", kind="number", style_color="red")
    div.update_attr("kind", "password")
    div.update_style("color", "blue")

    assert (
        repr(div) == "TextBox('name', 'Default', kind='password', style_color='blue')"
    )
