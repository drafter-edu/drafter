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


def has_circular_reference(value: Any) -> bool:
    """Check whether a value contains itself somewhere inside it.

    Follows the same containers that `safe_repr` writes out (dataclass
    fields, lists, tuples, sets, frozensets, and dictionary keys and
    values). A value that is merely used twice is not circular; only a
    value reachable from itself is.

    Args:
        value: The value to inspect, typically a state or a route argument.

    Returns:
        True if following the value's contents leads back to a container
        that is still being followed, False otherwise.

    Example:
        ```python
        items = [1, 2]
        has_circular_reference(items)  # False
        items.append(items)
        has_circular_reference(items)  # True
        ```
    """
    return _leads_back_to_itself(value, set(), set())


def _leads_back_to_itself(value: Any, active: set[int], finished: set[int]) -> bool:
    """Depth-first search for a container that contains one of its ancestors.

    Args:
        value: The value being followed.
        active: Ids of the containers on the path from the root to `value`.
        finished: Ids of containers already followed completely without
            finding a cycle, so shared values are only followed once.

    Returns:
        True if `value` or anything inside it refers back to a container in
        `active`.
    """
    if is_dataclass(value) and not isinstance(value, type):
        children = [getattr(value, f.name, None) for f in fields(value)]
    elif isinstance(value, dict):
        children = [*value.keys(), *value.values()]
    elif isinstance(value, (list, tuple, set, frozenset)):
        children = list(value)
    else:
        return False
    obj_id = id(value)
    if obj_id in active:
        return True
    if obj_id in finished:
        return False
    active.add(obj_id)
    found = any(_leads_back_to_itself(child, active, finished) for child in children)
    active.discard(obj_id)
    finished.add(obj_id)
    return found


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
