from tests.components.snippets._base import TestableComponentSet
from drafter import *


tests = TestableComponentSet("images")

# Image tests
tests.image_simple = Image("path/to/image.png", id="img1")
tests.image_simple = """
<img id="img1" src="/__images/path/to/image.png">
"""

tests.image_with_width = Image("photo.jpg", width=400, id="img2")
tests.image_with_width = """
<img id="img2" src="/__images/photo.jpg" width="400">
"""

tests.image_with_dimensions = Image("pic.png", width=300, height=200, id="img3")
tests.image_with_dimensions = """
<img height="200" id="img3" src="/__images/pic.png" width="300">
"""

tests.image_with_alt = Image("logo.svg", alt="Company Logo", id="img4")
tests.image_with_alt = """
<img alt="Company Logo" id="img4" src="/__images/logo.svg">
"""

# Tests with external URLs
tests.image_external = Image("https://example.com/image.png", id="img5")
tests.image_external = """
<img id="img5" src="https://example.com/image.png">
"""

tests.image_external_with_dimensions = Image(
    "https://example.com/photo.jpg", width=500, height=400, id="img6"
)
tests.image_external_with_dimensions = """
<img height="400" id="img6" src="https://example.com/photo.jpg" width="500">
"""
