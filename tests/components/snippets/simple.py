from tests.components.snippets._base import TestableComponentSet
from drafter import *


tests = TestableComponentSet("simple")
tests.br = LineBreak()
tests.br = """
<br>
"""

tests.textarea = TextArea("comments", rows=5, cols=40)
tests.textarea = """
<textarea aria-label="comments" cols="40" id="comments" name="comments" rows="5">
  
</textarea>
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

tests.multi_item_span = Span("Item 1", "Item 2", "Item 3")
tests.multi_item_span = """
<span>
  Item 1
  Item 2
  Item 3
</span>
"""

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
