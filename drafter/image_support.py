from typing import Optional
import typing

try:
    from PIL import Image as PILImage
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False
    PILImage = None # type: ignore

