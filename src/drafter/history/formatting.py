"""
Module for formatting page content as strings.

Relies on a custom PrettyPrinter to handle special types like images.
"""

import pprint

from PIL import Image as PILImage

from drafter.data.images import Picture
from drafter.helpers.diffing import get_indent_width
from drafter.history.utils import repr_image

NOT_FROZEN_PREFIX = "# Not frozen:"
"""How a visit's generated test starts when no test could be written for it.

The text after the prefix says why. The line is a Python comment, so the
debug panel's Copy and Download output stays valid Python. Mirrored in
js/src/debug/panels/testing.tsx, which keeps these lines among the tests."""


def describe_unfrozen_circular_visit(route_call: str) -> str:
    """Write the comment that stands in for a test with a circular state.

    A value that contains itself cannot be written as a Python literal, so
    a visit whose arguments or resulting state are circular gets this
    one-line comment instead of an `assert_equal(...)` test that could not
    be pasted and run.

    Args:
        route_call: The visit's route call, such as `add(State(count=1))`.
            Only the function name in front of the parenthesis is used.

    Returns:
        A one-line Python comment naming the route.

    Example:
        ```python
        describe_unfrozen_circular_visit("add(Pet(name='Ada', owner=...))")
        # "# Not frozen: add(...) has a state with a circular reference,
        #  which cannot be written as a test."
        ```
    """
    function_name = route_call.split("(", 1)[0].strip() or "this route"
    return (
        f"{NOT_FROZEN_PREFIX} {function_name}(...) has a state with a circular "
        "reference, which cannot be written as a test."
    )


class CustomPrettyPrinter(pprint.PrettyPrinter):  # type: ignore
    """PrettyPrinter subclass that renders images as HTML img tags."""

    def format(self, object, context, maxlevels, level):
        """Format one object, special-casing Pictures and PIL images.

        Overrides pprint.PrettyPrinter.format: `Picture` values and PIL
        images are rendered via `repr_image` as an HTML img thumbnail;
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
        if isinstance(object, (Picture, PILImage.Image)):
            return repr_image(object), True, False
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
