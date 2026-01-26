"""HTML escaping utilities for safe content rendering.

Provides functions to escape and HTML-encode values for safe insertion into
HTML documents, preventing injection attacks.
"""

import html
import json


def make_safe_json_argument(value):
    """Convert value to HTML-safe JSON string.

    Serializes value to JSON and escapes HTML special characters to prevent
    injection attacks.

    Args:
        value: Any JSON-serializable value.

    Returns:
        HTML-escaped JSON string representation.
    """
    return html.escape(json.dumps(value), True)


def make_safe_argument(value):
    """Convert value to HTML-safe JSON string.

    Serializes value to JSON and escapes HTML special characters. This function
    is an alias for make_safe_json_argument() for use in scenarios where you need
    to safely include arguments in HTML attributes.

    Args:
        value: Any JSON-serializable value.

    Returns:
        HTML-escaped JSON string representation.
    """
    return html.escape(json.dumps(value), True)


def make_safe_name(value):
    """HTML-escape string value.

    Converts value to string and escapes HTML special characters to prevent
    injection attacks.

    Args:
        value: Value to escape (converted to string if needed).

    Returns:
        HTML-escaped string representation.
    """
    return html.escape(str(value))
