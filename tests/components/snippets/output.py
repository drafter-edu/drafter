from drafter import *
from tests.components.snippets._base import TestableComponentSet

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

# ProgressBar tests
tests.progress_half = ProgressBar(0.5, id="progress1")
tests.progress_half = """
<progress id="progress1" max="1" value="0.5">
</progress>
"""

tests.progress_full = ProgressBar(100, max=100, id="progress2")
tests.progress_full = """
<progress id="progress2" max="100" value="100">
</progress>
"""

tests.progress_partial = ProgressBar(25, max=100, id="progress3")
tests.progress_partial = """
<progress id="progress3" max="100" value="25">
</progress>
"""

tests.progress_with_style = ProgressBar(
    0.75, max=1.0, style_width="200px", id="progress4"
)
tests.progress_with_style = """
<progress id="progress4" max="1" style="width: 200px" value="0.75">
</progress>
"""

# Meter tests
tests.meter_simple = Meter(0.5, id="meter1")
tests.meter_simple = """
<meter id="meter1" value="0.5">
</meter>
"""

tests.meter_full_range = Meter(
    70, min=0, max=100, low=30, high=80, optimum=90, id="meter2"
)
tests.meter_full_range = """
<meter high="80" id="meter2" low="30" max="100" min="0" optimum="90" value="70">
</meter>
"""

tests.meter_with_style = Meter(2, max=10, style_width="150px", id="meter3")
tests.meter_with_style = """
<meter id="meter3" max="10" style="width: 150px" value="2">
</meter>
"""

# TimeOutput tests
tests.time_simple = TimeOutput("July 25th")
tests.time_simple = """
<time>
  July 25th
</time>
"""

tests.time_with_datetime = TimeOutput("July 25th", datetime="2026-07-25", id="time1")
tests.time_with_datetime = """
<time datetime="2026-07-25" id="time1">
  July 25th
</time>
"""
