"""
Module for formatting page content as strings.

Relies on a custom PrettyPrinter to handle special types like images.
Patching this is tricky in Skulpt, so we have some curious fallbacks.
"""

from dataclasses import fields, is_dataclass
from drafter.components.images import HAS_PILLOW, PILImage
from drafter.diffing import get_indent_width
from drafter.history.utils import repr_pil_image, safe_repr
import pprint

# try:
#     pprint.PrettyPrinter
# except:

#     class PrettyPrinter:
#         def __init__(self, indent, width, *args, **kwargs):
#             self.indent = indent
#             self.width = width

#         def pformat(self, obj):
#             return pprint.pformat(obj, indent=self.indent, width=self.width)

#     pprint.PrettyPrinter = PrettyPrinter  # type: ignore


# class CustomPrettyPrinter(pprint.PrettyPrinter):  # type: ignore
#     def format(self, object, context, maxlevels, level):
#         if HAS_PILLOW and isinstance(object, PILImage.Image):
#             return repr_pil_image(object), True, False

#         # Let pprint handle non-dataclasses
#         if not is_dataclass(object):
#             return super().format(object, context, maxlevels, level)

#         # Avoid infinite recursion
#         if id(object) in context:
#             return (f"<Recursion {type(object).__name__}>", True, False)
#         context = context.copy()
#         context[id(object)] = 1

#         cls = type(object)
#         # Convention: dataclass may define __positional_fields__ like before
#         positional_names = set(getattr(cls, "__positional_fields__", ()))

#         pos_parts = []
#         kw_parts = []
#         for f in fields(cls):
#             val = getattr(object, f.name)
#             if f.name in positional_names:
#                 pos_parts.append(self._repr(val, context, level))
#             else:
#                 kw_parts.append(f"{f.name}={self._repr(val, context, level)}")

#         args_str = ", ".join(pos_parts + kw_parts)
#         s = f"{cls.__name__}({args_str})"
#         # second element = isreadable, third = isrecursive
#         return (s, True, False)

#         # return pprint.PrettyPrinter.format(self, object, context, maxlevels, level)

#     def _repr(self, value, context, level):
#         # delegate to PrettyPrinter's internal machinery
#         rep, _, _ = super().format(value, context, self._depth, level)
#         return rep


class CustomPrettyPrinter(pprint.PrettyPrinter):  # type: ignore
    def format(self, object, context, maxlevels, level):
        if HAS_PILLOW and isinstance(object, PILImage.Image):
            return repr_pil_image(object), True, False
        return pprint.PrettyPrinter.format(self, object, context, maxlevels, level)


def format_page_content(content, width=80, escape=True):
    custom_pretty_printer = CustomPrettyPrinter(indent=get_indent_width(), width=width)
    formatted = custom_pretty_printer.pformat(content)
    return formatted
    # try:
    #     custom_pretty_printer = CustomPrettyPrinter(
    #         indent=get_indent_width(), width=width
    #     )
    #     formatted = custom_pretty_printer.pformat(content)
    #     return formatted, True
    # except Exception as e:
    #     return safe_repr(content, escape=escape), False
