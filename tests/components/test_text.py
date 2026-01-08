from drafter import Text, RawHTML, Span


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
