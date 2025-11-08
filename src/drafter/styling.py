"""
TODO:
- [ ] indent
- [ ] center
- [ ] Superscript, subscript
- [ ] border/margin/padding (all sides)
"""

from typing import Union
from drafter.components import PageContent, Text, PageContent
from drafter.components.layout import Div


def update_style(component: PageContent, style: str, value: str) -> PageContent:
    """
    Updates the style of a component, returning the component (allowing you to chain calls).
    The ``style`` property should match the CSS property name.
    Remember to include units in the ``value`` if they are expected!

    Example style properties include:
    - color
    - background-color
    - font-size

    :param component: The component to update
    :param style: The name of the style property to change
    :param value: The value to set the style property to (should be a string).
    :return: Returns the original component (updates its values)
    """
    if isinstance(component, str):
        component = Text(component)
    # TODO: Consider this approach
    if isinstance(component, list):
        modified = []
        for i in range(len(component)):
            modified.append(update_style(component[i], style, value))
        return modified
    return component.update_style(style, value)


def update_attr(component: PageContent, attr: str, value: str) -> PageContent:
    """
    Updates the attribute of a component, returning the component (allowing you to chain calls).
    The ``attr`` property should match the HTML attribute name.

    Example attributes include:
    - id
    - class
    - title

    :param component: The component to update
    :param attr: The name of the attribute to change
    :param value: The value to set the attribute to (should be a string).
    :return: Returns the original component (updates its values)
    """
    if isinstance(component, str):
        component = Text(component)
    if isinstance(component, list):
        modified = []
        for i in range(len(component)):
            modified.append(update_attr(component[i], attr, value))
        return modified
    return component.update_attr(attr, value)


def float_right(component: PageContent) -> PageContent:
    """
    Floats the component to the right.

    :param component: The component to float right
    :return: Returns the original component (updated)
    """
    return update_style(component, "float", "right")


def float_left(component: PageContent) -> PageContent:
    """
    Floats the component to the left.

    :param component: The component to float left
    :return: Returns the original component (updated)
    """
    return update_style(component, "float", "left")


def bold(component: PageContent) -> PageContent:
    return update_style(component, "font-weight", "bold")


def italic(component: PageContent) -> PageContent:
    return update_style(component, "font-style", "italic")


def underline(component: PageContent) -> PageContent:
    return update_style(component, "text-decoration", "underline")


def strikethrough(component: PageContent) -> PageContent:
    return update_style(component, "text-decoration", "line-through")


def monospace(component: PageContent) -> PageContent:
    return update_style(component, "font-family", "monospace")


def small_font(component: PageContent) -> PageContent:
    return update_style(component, "font-size", "small")


def large_font(component: PageContent) -> PageContent:
    return update_style(component, "font-size", "large")


def change_color(component: PageContent, c: str) -> PageContent:
    return update_style(component, "color", c)


def change_background_color(component: PageContent, color: str) -> PageContent:
    return update_style(component, "background-color", color)


def change_text_size(component: PageContent, size: Union[str, int]) -> PageContent:
    if isinstance(size, int):
        size = f"{size}px"
    return update_style(component, "font-size", size)


def change_text_font(component: PageContent, font: str) -> PageContent:
    return update_style(component, "font-family", font)


def change_text_align(component: PageContent, align: str) -> PageContent:
    return update_style(component, "text-align", align)


def change_text_decoration(component: PageContent, decoration: str) -> PageContent:
    return update_style(component, "text-decoration", decoration)


def change_text_transform(component: PageContent, transform: str) -> PageContent:
    return update_style(component, "text-transform", transform)


def change_height(component: PageContent, height: str) -> PageContent:
    return update_style(component, "height", height)


def change_width(component: PageContent, width: str) -> PageContent:
    return update_style(component, "width", width)


def change_border(component: PageContent, border: str) -> PageContent:
    return update_style(component, "border", border)


def change_margin(component: PageContent, margin: str) -> PageContent:
    return update_style(component, "margin", margin)


def change_padding(component: PageContent, padding: str) -> PageContent:
    return update_style(component, "padding", padding)
