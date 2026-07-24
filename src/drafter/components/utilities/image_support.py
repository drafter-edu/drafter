"""PIL (Pillow) image support detection.

Checks for PIL availability and provides a compatible interface for image
handling, allowing graceful degradation if PIL is not installed.
"""

try:
    from PIL import Image as PILImage  # type: ignore

    HAS_PILLOW = True
except ImportError as e:
    print("Pillow not installed:", e)
    HAS_PILLOW = False

    class PILImage:  # type: ignore[no-redef]
        """Stand-in for the `PIL.Image` module when Pillow is not installed.

        Lets code reference `PILImage.Image` (in type hints and in
        `isinstance`/`issubclass` checks guarded by `HAS_PILLOW`) without
        raising ImportError at import time.

        Attributes:
            Image: Placeholder for `PIL.Image.Image`; always None.
        """

        Image = None


def refresh_pillow_support() -> bool:
    """Re-attempt the Pillow import if it failed when this module loaded.

    In the browser, drafter is usually imported before packages such as
    Pillow are installed by micropip, freezing `HAS_PILLOW` at False.
    Calling this once packages are in place (`start_server` does) switches
    PIL support on. Callers must read `HAS_PILLOW`/`PILImage` as attributes
    of this module (not import them by value) to observe the change.

    Returns:
        Whether Pillow is available after the attempt.
    """
    global HAS_PILLOW, PILImage
    if HAS_PILLOW:
        return True
    try:
        from PIL import Image as _pil_image
    except ImportError:
        return False
    PILImage = _pil_image  # type: ignore[misc]
    HAS_PILLOW = True
    return True
