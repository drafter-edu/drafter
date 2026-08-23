"""Helper functions for styling PageContent components.

Provides the general-purpose `update_style` and `update_attr` primitives that the
other helpers are built on.

Each helper also accepts a plain value (a string, number, or boolean, which
is wrapped in a new Text component) or a list of components (each element is
updated).
"""

from collections.abc import Sequence
from typing import TypeVar, overload

from drafter.components import Component, PageContent, Text
from drafter.components.page_content import PLAIN_CONTENT_TYPES, Content

ComponentT = TypeVar("ComponentT", bound=Component)
ContentT = TypeVar("ContentT", bound=Content)


@overload
def update_style(
    component: ComponentT,
    style: str,
    value: str,
) -> ComponentT: ...


@overload
def update_style(
    component: str | int | float | bool,
    style: str,
    value: str,
) -> Text: ...


@overload
def update_style(
    component: list[ContentT],
    style: str,
    value: str,
) -> list[Component]: ...


@overload
def update_style(
    component: tuple[ContentT, ...],
    style: str,
    value: str,
) -> list[Component]: ...


@overload
def update_style(
    component: Sequence[Content],
    style: str,
    value: str,
) -> Component | list[Component]: ...


def update_style(
    component: PageContent,
    style: str,
    value: str,
) -> Component | list[Component]:
    """
    Updates the style of a component, returning the component (allowing you to chain calls).
    The `style` property should match the CSS property name.
    Remember to include units in the `value` if they are expected!

    Example style properties include:
    - color
    - background-color
    - font-size

    Args:
        component: The component to update. May also be a plain value (a
            string, number, or boolean, which is wrapped in a new Text
            component) or a list of components (each element is updated).
        style: The name of the style property to change
        value: The value to set the style property to (should be a string).

    Returns:
        The updated component. If a component was given, the original
        component is updated in place and returned. If a plain value was
        given, a new Text component wrapping it is returned. If a list was
        given, a new list of the updated elements is returned.
    """
    if isinstance(component, (Component, *PLAIN_CONTENT_TYPES)):
        return _update_style_item(component, style, value)

    return [_update_style_item(item, style, value) for item in component]


def _update_style_item(component: Content, style: str, value: str) -> Component:
    if isinstance(component, Component):
        result = component
    elif isinstance(component, PLAIN_CONTENT_TYPES):
        result = Text(component)
    else:
        raise TypeError(
            f"Invalid PageContent item: expected Component, str, int, float, or bool, but got {type(component).__name__}."
        )
    result.update_style(style, value)
    return result


@overload
def update_attr(
    component: ComponentT,
    attr: str,
    value: str,
) -> ComponentT: ...


@overload
def update_attr(
    component: str | int | float | bool,
    attr: str,
    value: str,
) -> Text: ...


@overload
def update_attr(
    component: list[ContentT],
    attr: str,
    value: str,
) -> list[Component]: ...


@overload
def update_attr(
    component: tuple[ContentT, ...],
    attr: str,
    value: str,
) -> list[Component]: ...


@overload
def update_attr(
    component: Sequence[Content],
    attr: str,
    value: str,
) -> Component | list[Component]: ...


def update_attr(
    component: PageContent, attr: str, value: str
) -> Component | list[Component]:
    """
    Updates the attribute of a component, returning the component (allowing you to chain calls).
    The `attr` property should match the HTML attribute name.

    Example attributes include:
    - id
    - class
    - title

    Args:
        component: The component to update. May also be a plain value (a
            string, number, or boolean, which is wrapped in a new Text
            component) or a list of components (each element is updated).
        attr: The name of the attribute to change
        value: The value to set the attribute to (should be a string).

    Returns:
        The updated component. If a component was given, the original
        component is updated in place and returned. If a plain value was
        given, a new Text component wrapping it is returned. If a list was
        given, a new list of the updated elements is returned.
    """
    if isinstance(component, (Component, *PLAIN_CONTENT_TYPES)):
        return _update_attr_item(component, attr, value)

    return [_update_attr_item(item, attr, value) for item in component]


def _update_attr_item(component: Content, attr: str, value: str) -> Component:
    if isinstance(component, Component):
        result = component
    elif isinstance(component, PLAIN_CONTENT_TYPES):
        result = Text(component)
    else:
        raise TypeError(
            f"Invalid PageContent item: expected Component, str, int, float, or bool, but got {type(component).__name__}."
        )
    result.update_attr(attr, value)
    return result
