from dataclasses import dataclass
from typing import Any, List, Dict, Sequence
from drafter.components.page_content import Component, ComponentArgument, PageContent
from drafter.components.planning.render_plan import RenderPlan


@dataclass(repr=False)
class LineBreak(Component):
    """Renders a line break element (br).

    Attributes:
        tag: The HTML tag name, always 'br'.
        SELF_CLOSING_TAG: Indicates this is a self-closing tag.
    """

    tag = "br"
    SELF_CLOSING_TAG = True

    def __init__(self, **kwargs):
        """Initialize line break component.

        Args:
            **kwargs: Additional HTML attributes.
        """
        self.extra_settings = kwargs


@dataclass(repr=False)
class HorizontalRule(Component):
    """Renders a horizontal rule element (hr).

    Attributes:
        tag: The HTML tag name, always 'hr'.
        SELF_CLOSING_TAG: Indicates this is a self-closing tag.
    """

    tag = "hr"
    SELF_CLOSING_TAG = True

    def __init__(self, **kwargs):
        """Initialize horizontal rule component.

        Args:
            **kwargs: Additional HTML attributes.
        """
        self.extra_settings = kwargs


def handle_arguments_compatibility(args, kwargs):
    """Handle legacy Drafter functionality for backward compatibility.

    Supports previously incorrectly rendered components that passed explicit
    'content' and 'extra_settings' keyword arguments. If present, the items
    of the 'content' kwarg are appended to the positional arguments, and the
    entries of the 'extra_settings' kwarg are merged into the remaining
    keyword arguments (overriding any same-named keys). This functionality
    may be deprecated in future versions.

    Args:
        args: List of positional arguments (modified in place).
        kwargs: Dictionary of keyword arguments (modified in place).

    Returns:
        Tuple of (updated_args, updated_kwargs).
    """
    if "content" in kwargs:
        args.extend(kwargs.pop("content"))
    if "extra_settings" in kwargs:
        extra_settings = kwargs.pop("extra_settings")
        kwargs.update(extra_settings)
    return args, kwargs


@dataclass(repr=False)
class BlockComponent(Component):
    """
    An abstract component that renders an element for grouping content.
    Parent class of things like Div and Paragraph.

    Attributes:
        content: List of page content items to wrap in the block.
        tag: The HTML tag name.
    """

    content: List[PageContent]
    ARGUMENTS = [
        ComponentArgument("content", kind="var", is_content=True),
    ]

    def __init__(self, *content: PageContent, **extra_settings):
        """Initialize block component.

        Args:
            *content: Variable-length content to wrap in the block.
            **extra_settings: Additional HTML attributes and styles.
        """
        self.content, self.extra_settings = handle_arguments_compatibility(
            list(content), extra_settings
        )


class Span(BlockComponent):
    """Renders an inline span element for grouping content.

    Attributes:
        content: List of page content items to wrap in the span.
        tag: The HTML tag name, always 'span'.
    """

    tag = "span"


class Div(BlockComponent):
    """
    A div element for block-level grouping of content.

    Attributes:
        content: List of page content items to wrap in the div.
        tag: The HTML tag name, always 'div'.
    """

    tag = "div"


class Paragraph(BlockComponent):
    """Renders a paragraph element (p).

    Attributes:
        content: List of page content items to display in the paragraph.
        tag: The HTML tag name, always 'p'.
    """

    tag = "p"


class Section(BlockComponent):
    """Renders a section element (section).

    Attributes:
        content: List of page content items to display in the section.
        tag: The HTML tag name, always 'section'.
    """

    tag = "section"


class Article(BlockComponent):
    """Renders an article element (article).

    Attributes:
        content: List of page content items to display in the article.
        tag: The HTML tag name, always 'article'.
    """

    tag = "article"


class Aside(BlockComponent):
    """Renders an aside element (aside).

    Attributes:
        content: List of page content items to display in the aside.
        tag: The HTML tag name, always 'aside'.
    """

    tag = "aside"


class Main(BlockComponent):
    """Renders a main element (main).

    Attributes:
        content: List of page content items to display in the main section.
        tag: The HTML tag name, always 'main'.
    """

    tag = "main"


class Nav(BlockComponent):
    """Renders a navigation element (nav).

    Attributes:
        content: List of page content items to display in the navigation.
        tag: The HTML tag name, always 'nav'.
    """

    tag = "nav"


class HeaderContent(BlockComponent):
    """Renders a header element (header).

    Attributes:
        content: List of page content items to display in the header.
        tag: The HTML tag name, always 'header'.
    """

    tag = "header"


class FooterContent(BlockComponent):
    """Renders a footer element (footer).

    Attributes:
        content: List of page content items to display in the footer.
        tag: The HTML tag name, always 'footer'.
    """

    tag = "footer"


Division = Div
Box = Div

P = Paragraph


class Row(BlockComponent):
    tag = "div"

    DEFAULT_ATTRS = {
        "style_display": "flex",
        "style_flex_direction": "row",
        "style_align_items": "center",
    }

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
