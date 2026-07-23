"""
Module for formatting page content as strings.

Relies on a custom PrettyPrinter to handle special types like Pillow images.
"""

from drafter.components.images import HAS_PILLOW, PILImage
from drafter.helpers.diffing import get_indent_width
from drafter.history.utils import repr_pil_image
import pprint


class CustomPrettyPrinter(pprint.PrettyPrinter):  # type: ignore
    def format(self, object, context, maxlevels, level):
        if HAS_PILLOW and isinstance(object, PILImage.Image):
            return repr_pil_image(object), True, False
        return pprint.PrettyPrinter.format(self, object, context, maxlevels, level)


def format_page_content(content, width=80, escape=True):
    custom_pretty_printer = CustomPrettyPrinter(indent=get_indent_width(), width=width)
    formatted = custom_pretty_printer.pformat(content)
    return formatted
