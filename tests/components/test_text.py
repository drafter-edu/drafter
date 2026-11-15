import pytest

from drafter import Header, RawHTML, Span, Text
from drafter.data.errors import StudentFacingError
from drafter.payloads.renderer import render


def test_text_equality():
    text1 = Text("Hello, World!")
    text2 = Text("Hello, World!")
    text3 = Text("Hello, World!", style_color="red")
    text4 = Text("Hello, World!", style_color="red")
    text5 = Text("Hello, World!", style_color="blue")

    assert text1 == text2
    assert text3 == text4
    assert text1 != text3
    assert text3 != text5
    assert text1 == "Hello, World!"
    assert text3 != "Hello, World!"
    assert "Hello, World!" == text1
    assert "Hello, World!" != text3

    assert text1 != Span("Hello, World!")


def test_raw_html():
    html_content = "<div><p>This is raw HTML content.</p></div>"
    assert RawHTML(html_content) == html_content
    assert RawHTML(html_content) == "<div><p>This is raw HTML content.</p></div>"
    assert (
        RawHTML(html_content)
        != "<div><p>This is raw HTML content. But different.</p></div>"
    )
    assert RawHTML(html_content) != RawHTML(html_content + " Extra")
    assert RawHTML(html_content) == RawHTML(html_content)


class TestHeaderLevel:
    @pytest.mark.parametrize("level", [1, 2, 6])
    def test_whole_numbers_from_one_to_six_pick_the_tag(self, level):
        html = render(Header("Title", level)).flatten()
        assert html.startswith(f"<h{level}")

    @pytest.mark.parametrize("level", [0, 7, -1, 2.5, True, "2", None])
    def test_other_levels_get_the_header_level_error(self, level):
        with pytest.raises(StudentFacingError) as raised:
            Header("Title", level)

        assert str(raised.value) == (
            f"Header level must be between 1 and 6, not {level!r}"
        )
        assert raised.value.friendly_message
        # Its own title, not the shared "Unusable Value" of a ValueError.
        assert raised.value.friendly_title == "Header Level Out of Range"

    def test_swapped_arguments_are_pointed_out(self):
        # Header(2, "Title") used to stop with "'<' not supported between
        # instances of 'str' and 'int'".
        with pytest.raises(StudentFacingError) as raised:
            Header(2, "Title")

        assert "Header('Title', 2)" in raised.value.friendly_steps[0]

    def test_a_number_can_still_be_the_header_text(self):
        assert render(Header(2026, 2)).flatten().startswith("<h2")
