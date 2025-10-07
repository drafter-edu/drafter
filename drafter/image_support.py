try:
    from PIL import Image as PILImage  # type: ignore
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False
    PILImage = None  # type: ignore

