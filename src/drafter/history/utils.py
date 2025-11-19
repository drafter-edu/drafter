"""
Utility functions for the Drafter history module.
"""

import html
import base64
import io
from dataclasses import fields, is_dataclass
from typing import Any

from drafter.components.utilities.image_support import HAS_PILLOW, PILImage


TOO_LONG_VALUE_THRESHOLD = 256


def make_value_expandable(value):
    """
    Wraps long string values in an expandable span for better display.

    :param value: The value to potentially make expandable
    :return: HTML string with expandable wrapper if needed
    """
    if isinstance(value, str) and len(value) > TOO_LONG_VALUE_THRESHOLD:
        return f"<span class='expandable'>{value}</span>"
    return value


def value_to_html(value):
    """
    Converts a value to an HTML-safe representation.

    :param value: The value to convert
    :return: HTML-escaped string representation
    """
    return make_value_expandable(html.escape(repr(value)))


def is_generator(iterable):
    """
    Checks if an object is a generator (has __iter__ but not __len__).

    :param iterable: The object to check
    :return: True if it's a generator, False otherwise
    """
    return hasattr(iterable, "__iter__") and not hasattr(iterable, "__len__")


def repr_pil_image(value):
    """
    Creates an HTML representation of a PIL Image.

    :param value: A PIL Image object
    :return: HTML img tag string
    """
    filename = value.filename if hasattr(value, "filename") else None
    if not filename:
        # Encode image as base64 data URI
        image_data = io.BytesIO()
        value.save(image_data, format="PNG")
        image_data.seek(0)
        encoded = base64.b64encode(image_data.getvalue()).decode("latin1")
        image_src = f"data:image/png;base64,{encoded}"
        return f"<img src='{image_src}' alt='PIL Image' />"
    else:
        # Reference by filename
        return f"<img src='{filename}' alt='Image.open({filename!r})' />"


def safe_repr(value: Any, handled=None, escape=True):
    """
    Creates a safe HTML representation of a value, handling circular references.

    :param value: The value to represent
    :param handled: Set of already-handled object IDs (for circular reference detection)
    :return: HTML-safe string representation
    """
    obj_id = id(value)
    if handled is None:
        handled = set()
    else:
        handled = set(handled)
    if obj_id in handled:
        return "<strong>Circular Reference</strong>"
    if isinstance(
        value, (int, float, bool, type(None), str, bytes, complex, bytearray)
    ):
        if escape:
            return make_value_expandable(html.escape(repr(value)))
        return make_value_expandable(repr(value))
    if isinstance(value, list):
        handled.add(obj_id)
        return f"[{', '.join(safe_repr(v, handled, escape) for v in value)}]"
    if isinstance(value, dict):
        handled.add(obj_id)
        return f"{{{', '.join(f'{safe_repr(k, handled, escape)}: {safe_repr(v, handled, escape)}' for k, v in value.items())}}}"
    if is_dataclass(value):
        handled.add(obj_id)
        fields_repr = ", ".join(
            f"{f.name}={safe_repr(getattr(value, f.name), handled, escape)}"
            for f in fields(value)
        )
        return f"{value.__class__.__name__}({fields_repr})"  # type: ignore
    if isinstance(value, set):
        handled.add(obj_id)
        return f"{{{', '.join(safe_repr(v, handled, escape) for v in value)}}}"
    if isinstance(value, tuple):
        handled.add(obj_id)
        return f"({', '.join(safe_repr(v, handled, escape) for v in value)})"
    if isinstance(
        value,
        (
            frozenset,
            range,
        ),
    ):
        handled.add(obj_id)
        args_repr = ", ".join(safe_repr(v, handled, escape) for v in value)
        return f"{value.__class__.__name__}({{{args_repr}}})"

    if HAS_PILLOW and isinstance(value, PILImage.Image):
        return repr_pil_image(value)

    # Fallback for other types
    if escape:
        return make_value_expandable(html.escape(repr(value)))
    return make_value_expandable(repr(value))
