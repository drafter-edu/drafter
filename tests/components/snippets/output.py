from tests.components.snippets._base import TestableComponentSet
from drafter import *


tests = TestableComponentSet("output")

# Output tests
tests.output_simple = Output("result", "Processing complete")
tests.output_simple = """
<output aria-label="result" id="result" name="result">
  Processing complete
</output>
"""

tests.output_with_for = Output("output1", "Result: 42", for_id="calc_result")
tests.output_with_for = """
<output aria-label="output1" for="calc_result" id="output1" name="output1">
  Result: 42
</output>
"""

tests.output_with_special_chars = Output("output2", "Price: $19.99 & free shipping")
tests.output_with_special_chars = """
<output aria-label="output2" id="output2" name="output2">
  Price: $19.99 &amp; free shipping
</output>
"""

# Progress tests
tests.progress_half = Progress(0.5, id="progress1")
tests.progress_half = """
<progress id="progress1" max="1" value="0.5">
</progress>
"""

tests.progress_full = Progress(100, max=100, id="progress2")
tests.progress_full = """
<progress id="progress2" max="100" value="100">
</progress>
"""

tests.progress_partial = Progress(25, max=100, id="progress3")
tests.progress_partial = """
<progress id="progress3" max="100" value="25">
</progress>
"""

tests.progress_with_style = Progress(0.75, max=1.0, style_width="200px", id="progress4")
tests.progress_with_style = """
<progress id="progress4" max="1" style="width: 200px" value="0.75">
</progress>
"""
