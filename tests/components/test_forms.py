from drafter import TextBox


def test_textbox_repr():
    just_name = TextBox("some_name")
    assert repr(just_name) == "TextBox('some_name')"

    with_default = TextBox("some_name", "Starting Text")
    assert repr(with_default) == "TextBox('some_name', 'Starting Text')"

    with_kind = TextBox("some_name", "Starting Text", "password")
    assert repr(with_kind) == "TextBox('some_name', 'Starting Text', 'password')"

    with_aria = TextBox(
        "some_name", "Starting Text", "password", aria_label="Custom Aria Label"
    )
    assert (
        repr(with_aria)
        == "TextBox('some_name', 'Starting Text', 'password', aria_label='Custom Aria Label')"
    )

    with_styling = TextBox(
        "some_name", "Starting Text", style_font_size="14px", style_color="red"
    )
    assert (
        repr(with_styling)
        == "TextBox('some_name', 'Starting Text', style_font_size='14px', style_color='red')"
    )
