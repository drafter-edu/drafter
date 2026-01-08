from dataclasses import dataclass
from typing import Any, List, Dict, Sequence
from drafter.components.page_content import Component, ComponentArgument, PageContent
from drafter.components.planning.render_plan import RenderPlan


@dataclass(repr=False)
class LineBreak(Component):
    tag = "br"
    SELF_CLOSING_TAG = True

    def __init__(self, **kwargs):
        self.extra_settings = kwargs


@dataclass(repr=False)
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

    content: List[PageContent]

    tag = "span"
    ARGUMENTS = [
        ComponentArgument("content", kind="var", is_content=True),
    ]

    def __init__(self, *content: PageContent, **extra_settings):
        self.content, self.extra_settings = handle_arguments_compatibility(
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

    content: List[PageContent]

    tag = "div"
    ARGUMENTS = [
        ComponentArgument("content", kind="var", is_content=True),
    ]

    def __init__(self, *content: PageContent, **extra_settings):
        self.content, self.extra_settings = handle_arguments_compatibility(
            list(content), extra_settings
        )


Division = Div
Box = Div


@dataclass(repr=False)
class Row(Component):
    content: List[PageContent]

    tag = "div"

    DEFAULT_ATTRS = {
        "style_display": "flex",
        "style_flex_direction": "row",
        "style_align_items": "center",
    }
    ARGUMENTS = [
        ComponentArgument("content", kind="var", is_content=True),
    ]

    def __init__(self, *content: PageContent, **extra_settings):
        self.content, self.extra_settings = handle_arguments_compatibility(
            list(content), extra_settings
        )

    def __eq__(self, other):
        if isinstance(other, Row):
            return (
                self.content == other.content
                and self.extra_settings == other.extra_settings
            )
        elif isinstance(other, Div):
            return (
                self.content == other.content
                and self.extra_settings == other.extra_settings
            )
        return NotImplemented


class _HtmlList(Component):
    items: list[PageContent]
    POSITIONAL_ARGS = []

    ARGUMENTS = [ComponentArgument("items", is_content=True)]

    def get_children(self, context) -> list[PageContent | RenderPlan]:
        return [
            RenderPlan(kind="tag", tag_name="li", children=[item])
            for item in self.items
        ]


@dataclass(repr=False)
class NumberedList(_HtmlList):
    tag = "ol"

    def __init__(self, items: Sequence[PageContent], **extra_settings):
        # TODO: Check that the items are a list
        self.items = list(items)
        self.extra_settings = extra_settings


@dataclass(repr=False)
class BulletedList(_HtmlList):
    tag = "ul"

    def __init__(self, items: Sequence[PageContent], **extra_settings):
        self.items = list(items)
        self.extra_settings = extra_settings
