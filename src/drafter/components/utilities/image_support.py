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
        """Stand-in for the `PIL.Image` module when Pillow is not installed.

        Lets code reference `PILImage.Image` (in type hints and in
        `isinstance`/`issubclass` checks guarded by `HAS_PILLOW`) without
        raising ImportError at import time.

        Attributes:
            Image: Placeholder for `PIL.Image.Image`; always None.
        """

        Image = None
