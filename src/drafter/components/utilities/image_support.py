"""PIL (Pillow) image support detection.

Checks for PIL availability and provides a compatible interface for image
handling, allowing graceful degradation if PIL is not installed.
"""

try:
    from PIL import Image as PILImage

    HAS_PILLOW = True
except ImportError as e:
    print("Pillow not installed:", e)
    HAS_PILLOW = False

    class PILImage:
        Image = None
