"""Layout components for structuring and grouping page content.

Defines block-level grouping elements (`Div`, `Span`, `Paragraph`, and
semantic sections such as `Article`, `Nav`, `HeaderContent`), the flexbox
`Row` helper, list components (`NumberedList`, `BulletedList`,
`DefinitionList`), figures (`Figure`, `FigureCaption`), the collapsible
`Details` element, and the `LineBreak` and `HorizontalRule` spacing
elements. The aliases `Division`, `Box`, and `P` are also provided.
"""

from collections.abc import Sequence
from dataclasses import dataclass, fields, is_dataclass
from typing import Any

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

    content: list[PageContent]
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


class Figure(BlockComponent):
    """Renders a figure element for self-contained content like images or diagrams.

    Usually contains a `FigureCaption` alongside the main content.

    Attributes:
        content: List of page content items to display in the figure.
        tag: The HTML tag name, always 'figure'.

    Example:
        ```python
        Figure(Image("chart.png"), FigureCaption("Monthly sales"))
        ```
    """

    tag = "figure"


class FigureCaption(BlockComponent):
    """Renders a caption for a `Figure` (figcaption).

    Attributes:
        content: List of page content items to display in the caption.
        tag: The HTML tag name, always 'figcaption'.
    """

    tag = "figcaption"


@dataclass(repr=False)
class Details(Component):
    """Renders a collapsible disclosure element (details) with a summary.

    Attributes:
        summary: Content shown in the always-visible summary line.
        content: List of page content items revealed when expanded.
        open: Whether the details start expanded.
        group: Optional group name relating multiple Details; only one
            Details in a group can be open at a time (accordion-style).
        tag: The HTML tag name, always 'details'.

    Example:
        ```python
        Details("Hint", "Try checking the loop condition.", group="hints")
        ```
    """

    summary: PageContent
    content: list[PageContent]
    open: bool
    group: str | None
    tag = "details"

    KNOWN_ATTRS = ["open", "name"]
    RENAME_ATTRS = {"group": "name"}

    ARGUMENTS = [
        ComponentArgument("summary", is_content=True),
        ComponentArgument("content", kind="var", is_content=True),
        ComponentArgument("open", kind="keyword", default_value=False),
        ComponentArgument("group", kind="keyword", default_value=None),
    ]

    def __init__(
        self,
        summary: PageContent,
        *content: PageContent,
        open: bool = False,
        group: str | None = None,
        **extra_settings,
    ):
        """Initialize details component.

        Args:
            summary: Content shown in the always-visible summary line.
            *content: Variable-length content revealed when expanded.
            open: Whether the details start expanded. Defaults to False.
            group: Optional group name relating multiple Details
                accordion-style (rendered as the HTML `name` attribute).
            **extra_settings: Additional HTML attributes and styles.
        """
        self.summary = summary
        self.content, self.extra_settings = handle_arguments_compatibility(
            list(content), extra_settings
        )
        self.open = open
        self.group = group

    def get_children(self, context) -> list[PageContent | RenderPlan]:
        """Build the summary element followed by the collapsible content.

        Args:
            context: Rendering context.

        Returns:
            A list starting with a summary tag RenderPlan wrapping the
            summary content, followed by the remaining content items.
        """
        return [
            RenderPlan(kind="tag", tag_name="summary", children=[self.summary]),
            *self.content,
        ]


@dataclass(repr=False)
class DefinitionList(Component):
    """Renders a definition list (dl) of term/definition pairs.

    Accepts a dictionary (keys become terms), a dataclass instance (field
    names become terms), or a list of (term, definition) pairs. Each term
    is rendered as a dt element and each definition as a dd element.

    Attributes:
        items: The dictionary, dataclass instance, or list of pairs.
        tag: The HTML tag name, always 'dl'.

    Example:
        ```python
        DefinitionList({"HTML": "A markup language", "CSS": "A styling language"})
        DefinitionList([("Term", "Definition"), ("Other", "Meaning")])
        ```
    """

    items: Any
    tag = "dl"

    ARGUMENTS = [ComponentArgument("items", is_content=True)]

    def __init__(self, items, **extra_settings):
        """Initialize definition list component.

        Args:
            items: A dictionary, a dataclass instance, or a list of
                (term, definition) pairs.
            **extra_settings: Additional HTML attributes and styles.

        Raises:
            ValueError: If items is not one of the supported formats.
        """
        self.items = items
        self.extra_settings = extra_settings
        # Validate eagerly so students see errors where they made them
        self._get_pairs()

    def _get_pairs(self) -> list[tuple[Any, Any]]:
        if isinstance(self.items, dict):
            return list(self.items.items())
        if is_dataclass(self.items) and not isinstance(self.items, type):
            return [
                (field.name, getattr(self.items, field.name))
                for field in fields(self.items)
            ]
        if isinstance(self.items, Sequence) and not isinstance(self.items, str):
            pairs = []
            for index, item in enumerate(self.items):
                if (
                    isinstance(item, Sequence)
                    and not isinstance(item, str)
                    and len(item) == 2
                ):
                    pairs.append((item[0], item[1]))
                else:
                    raise ValueError(
                        f"DefinitionList items must be (term, definition) pairs, "
                        f"but the item at index {index} was {item!r}."
                    )
            return pairs
        raise ValueError(
            "DefinitionList expects a dictionary, a dataclass instance, or a "
            f"list of (term, definition) pairs, but got {type(self.items).__name__}."
        )

    def get_children(self, context) -> list[PageContent | RenderPlan]:
        """Build alternating dt/dd elements from the term/definition pairs.

        Args:
            context: Rendering context.

        Returns:
            A list of dt and dd tag RenderPlans, one pair per entry.
        """

        def as_content(value):
            if isinstance(value, (Component, str, list)):
                return value
            return str(value)

        children: list[PageContent | RenderPlan] = []
        for term, definition in self._get_pairs():
            children.append(
                RenderPlan(kind="tag", tag_name="dt", children=[as_content(term)])
            )
            children.append(
                RenderPlan(kind="tag", tag_name="dd", children=[as_content(definition)])
            )
        return children


Division = Div
"""Alias for `Div`."""

Box = Div
"""Alias for `Div`."""

P = Paragraph
"""Alias for `Paragraph`."""


class Row(BlockComponent):
    """A `Div` that lays out its content horizontally using flexbox.

    Renders a `div` styled with `display: flex`, `flex-direction: row`,
    and vertically centered items. Its custom `__eq__` treats a `Row` as
    equal to a plain `Div` with the same content and settings.

    Attributes:
        content: List of page content items to arrange in a row.
        tag: The HTML tag name, always 'div'.

    Example:
        ```python
        Row("Name:", TextBox("name"))
        ```
    """

    tag = "div"

    DEFAULT_ATTRS = {
        "style_display": "flex",
        "style_flex_direction": "row",
        "style_align_items": "center",
    }

    def __eq__(self, other):
        """Compare equal to any Row or Div with the same content and settings."""
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
    """Renders a numbered (ordered) list with one list item per entry.

    Attributes:
        items: List of page content items, each rendered as a list item.
        tag: The HTML tag name, always 'ol'.

    Example:
        ```python
        NumberedList(["First", "Second", "Third"])
        ```
    """

    tag = "ol"

    def __init__(self, items: Sequence[PageContent], **extra_settings):
        # TODO: Check that the items are a list
        self.items = list(items)
        self.extra_settings = extra_settings


@dataclass(repr=False)
class BulletedList(_HtmlList):
    """Renders a bulleted (unordered) list with one list item per entry.

    Attributes:
        items: List of page content items, each rendered as a list item.
        tag: The HTML tag name, always 'ul'.

    Example:
        ```python
        BulletedList(["Apples", "Bananas", "Cherries"])
        ```
    """

    tag = "ul"

    def __init__(self, items: Sequence[PageContent], **extra_settings):
        self.items = list(items)
        self.extra_settings = extra_settings
