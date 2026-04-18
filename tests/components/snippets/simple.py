from tests.components.snippets._base import TestableComponentSet
from drafter import *


tests = TestableComponentSet("simple")
tests.br = LineBreak()
tests.br = """
<br>
"""

tests.textarea = TextArea("comments", rows=5, cols=40)
tests.textarea = """
<textarea aria-label="comments" cols="40" id="comments" name="comments" rows="5"></textarea>
"""

tests.span = Span("highlight")
tests.span = """
<span>
  highlight
</span>
"""

tests.nested_span = Span(Span("Nested span content"))
tests.nested_span = """
<span>
  <span>
    Nested span content
  </span>
</span>
"""

tests.nested_span_with_text = Span("Outer text", Span("Inner text"), "More outer text")
tests.nested_span_with_text = """
<span>
  Outer text
  <span>
    Inner text
  </span>
  More outer text
</span>
"""

tests.nested_span_times_two = Span(
    "First level", Span("Second level"), Span("Another second level"), "Ending Text"
)
tests.nested_span_times_two = """
<span>
  First level
  <span>
    Second level
  </span>
  <span>
    Another second level
  </span>
  Ending Text
</span>
"""

tests.multi_item_span = Span("Item 1", "Item 2", "Item 3")
tests.multi_item_span = """
<span>
  Item 1
  Item 2
  Item 3
</span>
"""

tests.line_break = LineBreak()
tests.line_break = """<br>"""

tests.multiple_line_breaks_in_span = Span(
    "Line 1", LineBreak(), "Line 2", LineBreak(), "Line 3"
)
tests.multiple_line_breaks_in_span = """
<span>
  Line 1
  <br>
  Line 2
  <br>
  Line 3
</span>
"""

tests.boolean_attributes_in_span = Span(
    "Can you see me?", hidden=True, draggable=True, id="test-span"
)
tests.boolean_attributes_in_span = """
<span draggable="true" hidden id="test-span">
  Can you see me?
</span>
"""

tests.escaping = Span("This & that < those > these")
tests.escaping = """<span>
  This &amp; that &lt; those &gt; these
</span>
"""

tests.escaping_textbox = TextBox("name", default_value="This & that < those > these")
tests.escaping_textbox = """<input aria-label="name" id="name" name="name" type="text" value="This &amp; that &lt; those &gt; these">"""

tests.string_escaping = Span("Hello' and \" Goodbye.")
tests.string_escaping = """<span>
  Hello&#x27; and &quot; Goodbye.
</span>
"""

tests.header_1 = Header("Welcome to My Page", level=1, id="main-header")
tests.header_1 = """<h1 id="main-header">
  Welcome to My Page
</h1>"""

tests.header_2 = Header("Section Title", level=2, id="section-title")
tests.header_2 = """<h2 id="section-title">
  Section Title
</h2>"""

tests.div_with_headers = Div(
    Header("Main Title", level=1, id="main-title"),
    Header("Subsection", level=2, id="subsection"),
)
tests.div_with_headers = """<div>
  <h1 id="main-title">
    Main Title
  </h1>
  <h2 id="subsection">
    Subsection
  </h2>
</div>
"""

tests.pre_collapse = Pre("Line 1\n  Line 2\n    Line 3")
tests.pre_collapse = """<pre>Line 1
  Line 2
    Line 3</pre>
"""

tests.newline_in_span = Span("Line 1\nLine 2\nLine 3")
tests.newline_in_span = """
<span>
  Line 1
  <br>
  Line 2
  <br>
  Line 3
</span>
"""

tests.newline_in_bare_string = "Hello\nWorld"
tests.newline_in_bare_string = """Hello
<br>
World"""

tests.empty_text = Text("Hello world!")
tests.empty_text = """Hello world!"""

tests.styled_text = Text(
    "Styled Text", style_color="red", style_font_size="20px", id="styled-text"
)
tests.styled_text = """<span id="styled-text" style="color: red; font-size: 20px">
  Styled Text
</span>"""

tests.non_empty_raw_html = RawHTML("<div><p>This is raw HTML content.</p></div>")
tests.non_empty_raw_html = """<div><p>This is raw HTML content.</p></div>"""

tests.nested_raw_html = Div(
    RawHTML("<p>Paragraph 1</p>"), RawHTML("<p>Paragraph 2</p>")
)
tests.nested_raw_html = """<div>
  <p>Paragraph 1</p>
  <p>Paragraph 2</p>
</div>
"""

tests.styled_raw_html = RawHTML(
    "<p>Styled Raw HTML</p>",
    style_color="blue",
    style_font_size="18px",
    id="styled-raw-html",
)
tests.styled_raw_html = """<div id="styled-raw-html" style="color: blue; font-size: 18px">
  <p>Styled Raw HTML</p>
</div>"""
