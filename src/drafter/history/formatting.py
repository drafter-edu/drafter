"""
Module for formatting page content as strings.

Relies on a custom PrettyPrinter to handle special types like images.
Patching this is tricky in Skulpt, so we have some curious fallbacks.
"""

from drafter.components.images import HAS_PILLOW, PILImage
from drafter.diffing import get_indent_width
from drafter.history.utils import repr_pil_image, safe_repr
import pprint

try:
    pprint.PrettyPrinter
except:

    class PrettyPrinter:
        def __init__(self, indent, width, *args, **kwargs):
            self.indent = indent
            self.width = width

        def pformat(self, obj):
            return pprint.pformat(obj, indent=self.indent, width=self.width)

    pprint.PrettyPrinter = PrettyPrinter  # type: ignore


class CustomPrettyPrinter(pprint.PrettyPrinter):  # type: ignore
    def format(self, object, context, maxlevels, level):
        if HAS_PILLOW and isinstance(object, PILImage.Image):
            return repr_pil_image(object), True, False
        return pprint.PrettyPrinter.format(self, object, context, maxlevels, level)


def format_page_content(content, width=80, escape=True):
    try:
        custom_pretty_printer = CustomPrettyPrinter(
            indent=get_indent_width(), width=width
        )
        return custom_pretty_printer.pformat(content), True
    except Exception as e:
        return safe_repr(content, escape=escape), False
