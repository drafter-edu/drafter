from drafter import *
from tests.components.snippets._base import TestableComponentSet

tests = TestableComponentSet("links")

# Image tests
tests.simple_button = Button("Click Me!", "next_page", id="target-button")
tests.simple_button = """
<button data-nav="next_page" formaction="#" id="target-button" name="--submit-button" type="submit" value="&amp;quot;Click Me!#target-button&amp;quot;">
  Click Me!
</button>
"""
