from dataclasses import dataclass

from drafter import *
from tests.components.snippets._base import TestableComponentSet

tests = TestableComponentSet("semantics")

# Simple inline text components
tests.strong = Strong("important")
tests.strong = """
<strong>
  important
</strong>
"""

tests.emphasis = Emphasis("emphasized")
tests.emphasis = """
<em>
  emphasized
</em>
"""

tests.keyboard_input = KeyboardInput("Ctrl", "+", "C")
tests.keyboard_input = """
<kbd>
  Ctrl
  +
  C
</kbd>
"""

tests.marked_text = MarkedText("highlighted")
tests.marked_text = """
<mark>
  highlighted
</mark>
"""

tests.sample_output = SampleOutput("Error: file not found")
tests.sample_output = """
<samp>
  Error: file not found
</samp>
"""

tests.small_text = SmallText("fine print")
tests.small_text = """
<small>
  fine print
</small>
"""

tests.superscript = Superscript("2")
tests.superscript = """
<sup>
  2
</sup>
"""

tests.subscript = Subscript("i")
tests.subscript = """
<sub>
  i
</sub>
"""

tests.inline_variable = InlineVariable("x")
tests.inline_variable = """
<var>
  x
</var>
"""

tests.nested_inline = Paragraph("E = m", InlineVariable("c"), Superscript("2"))
tests.nested_inline = """
<p>
  E = m
  <var>
    c
  </var>
  <sup>
    2
  </sup>
</p>
"""

tests.styled_strong = Strong("Loud", style_color="red", id="strong1")
tests.styled_strong = """
<strong id="strong1" style="color: red">
  Loud
</strong>
"""

# Inline quotation
tests.inline_quotation = InlineQuotation("Be yourself")
tests.inline_quotation = """
<q>
  Be yourself
</q>
"""

tests.inline_quotation_with_cite = InlineQuotation(
    "Be yourself", cite="https://example.com", id="q1"
)
tests.inline_quotation_with_cite = """
<q cite="https://example.com" id="q1">
  Be yourself
</q>
"""

# Definition term and abbreviation
tests.definition_term = DefinitionTerm(
    "HTML", title="HyperText Markup Language", id="dfn1"
)
tests.definition_term = """
<dfn id="dfn1" title="HyperText Markup Language">
  HTML
</dfn>
"""

tests.abbreviation = Abbreviation("WWW", title="World Wide Web", id="abbr1")
tests.abbreviation = """
<abbr id="abbr1" title="World Wide Web">
  WWW
</abbr>
"""

# Deleted and inserted text
tests.deleted_text = DeletedText(
    "old price", cite="https://example.com/why", datetime="2026-07-25", id="del1"
)
tests.deleted_text = """
<del cite="https://example.com/why" datetime="2026-07-25" id="del1">
  old price
</del>
"""

tests.inserted_text = InsertedText(
    "new price", datetime="2026-07-25T10:30:00", id="ins1"
)
tests.inserted_text = """
<ins datetime="2026-07-25T10:30:00" id="ins1">
  new price
</ins>
"""

tests.plain_deleted_text = DeletedText("removed")
tests.plain_deleted_text = """
<del>
  removed
</del>
"""

# Figures
tests.figure_with_caption = Figure(FigureCaption("Monthly sales"), "Chart goes here")
tests.figure_with_caption = """
<figure>
  <figcaption>
    Monthly sales
  </figcaption>
  Chart goes here
</figure>
"""

# Details
tests.details_simple = Details("Click to expand", "Hidden content")
tests.details_simple = """
<details>
  <summary>
    Click to expand
  </summary>
  Hidden content
</details>
"""

tests.details_open_grouped = Details(
    "Question 1", "Answer 1", open=True, group="faq", id="details1"
)
tests.details_open_grouped = """
<details id="details1" name="faq" open>
  <summary>
    Question 1
  </summary>
  Answer 1
</details>
"""

tests.details_with_components = Details(
    Strong("Hint"), Paragraph("Check the loop condition.")
)
tests.details_with_components = """
<details>
  <summary>
    <strong>
      Hint
    </strong>
  </summary>
  <p>
    Check the loop condition.
  </p>
</details>
"""

# Definition lists
tests.definition_list_dict = DefinitionList(
    {"HTML": "A markup language", "CSS": "A styling language"}
)
tests.definition_list_dict = """
<dl>
  <dt>
    HTML
  </dt>
  <dd>
    A markup language
  </dd>
  <dt>
    CSS
  </dt>
  <dd>
    A styling language
  </dd>
</dl>
"""

tests.definition_list_pairs = DefinitionList([("a", 1), ("b", 2)])
tests.definition_list_pairs = """
<dl>
  <dt>
    a
  </dt>
  <dd>
    1
  </dd>
  <dt>
    b
  </dt>
  <dd>
    2
  </dd>
</dl>
"""


@dataclass
class _Pet:
    name: str = "Rex"
    age: int = 3


tests.definition_list_dataclass = DefinitionList(_Pet())
tests.definition_list_dataclass = """
<dl>
  <dt>
    name
  </dt>
  <dd>
    Rex
  </dd>
  <dt>
    age
  </dt>
  <dd>
    3
  </dd>
</dl>
"""

tests.definition_list_with_components = DefinitionList([("Term", Emphasis("Meaning"))])
tests.definition_list_with_components = """
<dl>
  <dt>
    Term
  </dt>
  <dd>
    <em>
      Meaning
    </em>
  </dd>
</dl>
"""
