"""
Module for formatting page content as strings.

Relies on a custom PrettyPrinter to handle special types like Pillow images.
"""

from drafter.components.images import HAS_PILLOW, PILImage
from drafter.helpers.diffing import get_indent_width
from drafter.history.utils import repr_pil_image
import pprint


class CustomPrettyPrinter(pprint.PrettyPrinter):  # type: ignore
    """PrettyPrinter subclass that renders Pillow images as HTML img tags."""

    def format(self, object, context, maxlevels, level):
        """Format one object, special-casing PIL images.

        Overrides pprint.PrettyPrinter.format: PIL images (when Pillow is
        available) are rendered via `repr_pil_image` as an HTML img tag;
        everything else uses the standard pprint formatting.

        Args:
            object: The value to format.
            context: Dict of ids of containers currently being presented,
                used by pprint to detect recursion.
            maxlevels: Maximum nesting depth to present.
            level: Current nesting level.

        Returns:
            Tuple of (formatted string, whether it is readable by eval,
            whether recursion was detected), per the pprint contract.
        """
        if HAS_PILLOW and isinstance(object, PILImage.Image):
            return repr_pil_image(object), True, False
        return pprint.PrettyPrinter.format(self, object, context, maxlevels, level)


def format_page_content(content, width=80, escape=True):
    """Pretty-print page content with image-aware formatting.

    Args:
        content: The page content value to format.
        width: Maximum line width for the pretty printer.
        escape: Accepted for API compatibility but currently unused; the
            output is not HTML-escaped regardless of its value.

    Returns:
        The pretty-printed string representation of the content.
    """
    custom_pretty_printer = CustomPrettyPrinter(indent=get_indent_width(), width=width)
    formatted = custom_pretty_printer.pformat(content)
    return formatted
