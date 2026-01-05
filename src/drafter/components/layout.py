from dataclasses import dataclass
from typing import Any, List, Dict
from drafter.components.page_content import Component, PageContent
from drafter.components.planning.render_plan import RenderPlan


@dataclass
class LineBreak(Component):
    tag = "br"
    SELF_CLOSING_TAG = True

    def __init__(self, **kwargs):
        self.extra_settings = kwargs


@dataclass
class HorizontalRule(Component):
    tag = "hr"
    SELF_CLOSING_TAG = True

    def __init__(self, **kwargs):
        self.extra_settings = kwargs


def handle_arguments_compatibility(args, kwargs):
    """
    A function that handles classic Drafter functionality for
    previously incorrectly rendered components that used the explicit
    content and extra_settings kwargs. We should actively consider
    whether we want to retain this functionality long-term.

    Args:
        args (list): Positional arguments
        kwargs (kwargs): Keyword arguments

    Returns:
        tuple: Updated args and kwargs
    """
    if "content" in kwargs:
        args.extend(kwargs.pop("content"))
    if "extra_settings" in kwargs:
        kwargs = kwargs.pop("extra_settings")
        kwargs.update(kwargs)
    return args, kwargs


@dataclass(repr=False)
class Span(Component):
    """
    A span element for inline grouping of content.

    Args:
        *content: The content to be wrapped in the span.
        **extra_settings: Additional HTML attributes and style properties for the span.
    """

    tag = "span"

    def __init__(self, *content: PageContent, **extra_settings):
        self.children, self.extra_settings = handle_arguments_compatibility(
            list(content), extra_settings
        )


@dataclass(repr=False)
class Div(Component):
    """
    A div element for block-level grouping of content.

    Args:
        *content: The content to be wrapped in the div.
        **extra_settings: Additional HTML attributes and style properties for the div.
    """

    tag = "div"

    def __init__(self, *content: PageContent, **extra_settings):
        self.children, self.extra_settings = handle_arguments_compatibility(
            list(content), extra_settings
        )


Division = Div
Box = Div


@dataclass(repr=False)
class Row(Component):
    tag = "div"

    def __init__(self, *content: PageContent, **extra_settings):
        self.children, self.extra_settings = handle_arguments_compatibility(
            list(content), extra_settings
        )
        self.extra_settings.setdefault("style_display", "flex")
        self.extra_settings.setdefault("style_flex_direction", "row")
        self.extra_settings.setdefault("style_align_items", "center")

    def __eq__(self, other):
        if isinstance(other, Row):
            return (
                self.children == other.children
                and self.extra_settings == other.extra_settings
            )
        elif isinstance(other, Div):
            return (
                self.children == other.children
                and self.extra_settings == other.extra_settings
            )
        return NotImplemented


class _HtmlList(Component):
    items: List[PageContent]
    POSITIONAL_ARGS = []

    def get_children(self) -> List[PageContent | RenderPlan]:
        return [
            RenderPlan(kind="tag", tag_name="li", children=[item])
            for item in self.items
        ]


@dataclass(repr=False)
class NumberedList(_HtmlList):
    tag = "ol"

    def __init__(self, items: list[PageContent], **extra_settings):
        # TODO: Check that the items are a list
        self.items = items
        self.extra_settings = extra_settings


@dataclass(repr=False)
class BulletedList(_HtmlList):
    tag = "ul"

    def __init__(self, items: list[PageContent], **extra_settings):
        self.items = items
        self.extra_settings = extra_settings
