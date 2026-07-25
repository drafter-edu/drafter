"""
Utility functions for the Drafter history module.
"""

import html
from dataclasses import fields, is_dataclass
from typing import Any

from PIL import Image as PILImage

from drafter.data.images import Picture, thumbnail_data_url

TOO_LONG_VALUE_THRESHOLD = 256
"""String length above which values are wrapped in an expandable span."""


def make_value_expandable(value):
    """
    Wraps long string values in an expandable span for better display.

    Args:
        value: The value to potentially make expandable

    Returns:
        HTML string with expandable wrapper if needed
    """
    if isinstance(value, str) and len(value) > TOO_LONG_VALUE_THRESHOLD:
        return f"<span class='expandable'>{value}</span>"
    return value


def value_to_html(value):
    """
    Converts a value to an HTML-safe representation.

    Args:
        value: The value to convert

    Returns:
        HTML-escaped string representation
    """
    return make_value_expandable(html.escape(repr(value)))


def is_generator(iterable):
    """
    Checks if an object is a generator (has __iter__ but not __len__).

    Args:
        iterable: The object to check

    Returns:
        True if it's a generator, False otherwise
    """
    return hasattr(iterable, "__iter__") and not hasattr(iterable, "__len__")


def repr_image(value):
    """
    Creates an HTML thumbnail representation of a Picture or PIL Image.

    Always embeds a small data-URL thumbnail (a filename alone is usually
    not a resolvable URL, e.g. for uploaded files), captioned with the
    filename when one is known.

    Args:
        value: A `Picture` or PIL Image object.

    Returns:
        HTML img tag string.
    """
    try:
        if isinstance(value, Picture) and not value.is_loaded():
            # Unloaded URL-backed Picture: show the URL without fetching.
            url = html.escape(value.url or "", quote=True)
            return f"<img src='{url}' alt='{url}' />"
        filename = (
            value.filename
            if isinstance(value, Picture)
            else getattr(value, "filename", None)
        )
        label = html.escape(str(filename), quote=True) if filename else "Image"
        image_src = thumbnail_data_url(value)
        return f"<img src='{image_src}' alt='{label}' title='{label}' />"
    except Exception as e:
        return f"<strong>Error displaying image: {e}</strong>"


def safe_repr(value: Any, handled=None, escape=True):
    """
    Creates a safe HTML representation of a value, handling circular references.

    Args:
        value (Any): The value to represent
        handled (set): Set of already-handled object IDs (for circular reference detection)
        escape (bool): Whether to HTML-escape the representation

    Returns:
        HTML-safe string representation
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

    if isinstance(value, (Picture, PILImage.Image)):
        return repr_image(value)

    # Fallback for other types
    if escape:
        return make_value_expandable(html.escape(repr(value)))
    return make_value_expandable(repr(value))
