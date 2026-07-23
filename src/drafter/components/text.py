"""Text components for displaying written content.

Defines `Text` (plain text in a span), `Header` (headings h1-h6),
`Pre`/`PreformattedText`, `BlockQuote`, `InlineCode`, `RawHTML`
(unescaped HTML, for trusted content only), and the generic `HtmlTag`.
"""

from dataclasses import dataclass
import html
from typing import List, Optional
from drafter.components.layout import handle_arguments_compatibility
from drafter.components.page_content import Component, ComponentArgument, PageContent
from drafter.components.planning.render_plan import RenderPlan, NewlineMode


@dataclass(repr=False)
class Pre(Component):
    """Renders preformatted text with preserved whitespace.

    Attributes:
        content: List of page content items to display with preserved formatting.
        tag: The HTML tag name, always 'pre'.
        COLLAPSE_WHITESPACE: Whether to collapse whitespace in output.
    """

    content: list[PageContent]
    tag = "pre"

    ARGUMENTS = [ComponentArgument("content", kind="var", is_content=True)]

    COLLAPSE_WHITESPACE = True
    NEWLINE_MODE = NewlineMode.RETAIN

    def __init__(self, *content: PageContent, **extra_settings):
        """Initialize preformatted text component.

        Args:
            *content: Variable-length content to display.
            **extra_settings: Additional HTML attributes and styles.
        """
        self.content = list(content)
        self.extra_settings = extra_settings


PreformattedText = Pre
"""Alias for `Pre`."""


@dataclass(repr=False)
class BlockQuote(Component):
    """Renders a blockquote element.

    Attributes:
        cite: The source URL of the blockquote, if any.
        content: List of page content items to display in the blockquote.

        tag: The HTML tag name, always 'blockquote'.
    """

    cite: Optional[str]
    content: list[PageContent]
    tag = "blockquote"

    ARGUMENTS = [
        ComponentArgument("cite", kind="positional", default_value=None),
        ComponentArgument("content", kind="var", is_content=True),
    ]

    def __init__(self, cite: Optional[str], *content: PageContent, **extra_settings):
        """Initialize blockquote component.

        Args:
            cite: The source URL of the blockquote, if any.
            *content: Variable-length content to display in the blockquote.
            **extra_settings: Additional HTML attributes and styles.
        """
        self.cite = cite
        self.content = list(content)
        self.extra_settings = extra_settings


@dataclass(repr=False)
class Header(Component):
    """Renders a heading element (h1-h6).

    Attributes:
        body: The content of the heading.
        level: The heading level (1-6), determines the HTML tag.
    """

    body: PageContent
    level: int = 1

    ARGUMENTS = [
        ComponentArgument("body", is_content=True),
        ComponentArgument("level", kind="keyword", default_value=1),
    ]

    RENAME_ATTRS = {"level": ""}

    def __init__(self, body: PageContent, level: int = 1, **extra_settings):
        """Initialize heading component.

        Args:
            body: The heading content.
            level: The heading level (1-6). Defaults to 1.
            **extra_settings: Additional HTML attributes and styles.

        Raises:
            ValueError: If level is not between 1 and 6.
        """
        self.body = body
        self.level = level
        if level < 1 or level > 6:
            raise ValueError("Header level must be between 1 and 6")
        self.extra_settings = extra_settings

    def get_tag(self, context) -> str:
        """Get the HTML tag name based on heading level.

        Args:
            context: Rendering context.

        Returns:
            The tag name (e.g., 'h1', 'h2').
        """
        return f"h{self.level}"


@dataclass(repr=False)
class Text(Component):
    """Renders simple text content wrapped in a span element.

    Attributes:
        tag: The HTML tag name, always 'span'.
        body: The text content to display.
        extra_settings: Additional HTML attributes and styles.
    """

    tag = "span"
    body: str
    extra_settings: dict

    ARGUMENTS = [
        ComponentArgument("body", is_content=True),
    ]

    def __init__(self, body: str, **extra_settings):
        """Initialize text component.

        Args:
            body: The text content to display.
            **extra_settings: Additional HTML attributes and styles.
        """
        self.body = body
        if "body" in extra_settings:
            self.body = extra_settings.pop("body")
        self.extra_settings = extra_settings

    def __eq__(self, other):
        """Compare text components for equality.

        Args:
            other: The object to compare with.

        Returns:
            True if components have identical body and extra_settings.
        """
        if isinstance(other, Text):
            return (
                self.body == other.body and self.extra_settings == other.extra_settings
            )
        elif isinstance(other, str):
            return self.extra_settings == {} and self.body == other
        return NotImplemented

    def __hash__(self):
        if self.extra_settings:
            items = tuple(sorted(self.extra_settings.items()))
            return hash((self.body, items))
        else:
            return hash(self.body)

    def plan(self, context) -> RenderPlan:
        """Plan the text for rendering.

        Args:
            context: Rendering context.

        Returns:
            A raw RenderPlan with the HTML-escaped body when there are no
            extra settings; otherwise a full span tag RenderPlan.
        """
        if not self.extra_settings:
            return RenderPlan(
                kind="raw",
                raw_html=html.escape(self.body),
            )
        return self._plan_tag(context=context)


@dataclass(repr=False)
class InlineCode(Component):
    """Renders an inline code element.

    Attributes:
        content: List of page content items to wrap in the code element.
        tag: The HTML tag name, always 'code'.
    """

    content: List[PageContent]

    tag = "code"
    ARGUMENTS = [
        ComponentArgument("content", kind="var", is_content=True),
    ]

    def __init__(self, *content: PageContent, **extra_settings):
        """Initialize code component.

        Args:
            *content: Variable-length content to wrap in the code element.
            **extra_settings: Additional HTML attributes and styles.
        """
        self.content, self.extra_settings = handle_arguments_compatibility(
            list(content), extra_settings
        )


@dataclass(repr=False)
class RawHTML(Component):
    """
    A component that renders raw HTML without escaping.

    WARNING: Only use with trusted HTML content to avoid XSS vulnerabilities.
    This component bypasses HTML escaping and renders content as-is.

    Attributes:
        html: The raw HTML string to render.
        tag: The HTML tag name, always 'div'.
    """

    html: str
    tag = "div"
    ARGUMENTS = [
        ComponentArgument("html", is_content=True),
    ]

    def __init__(self, html: str, **extra_settings):
        self.html = html
        if "html" in extra_settings:
            self.html = extra_settings.pop("html")
        self.extra_settings = extra_settings

    def __eq__(self, other):
        if isinstance(other, RawHTML):
            return (
                self.html == other.html and self.extra_settings == other.extra_settings
            )
        elif isinstance(other, str):
            return self.extra_settings == {} and self.html == other
        return NotImplemented

    def __hash__(self):
        if self.extra_settings:
            items = tuple(sorted(self.extra_settings.items()))
            return hash((self.html, items))
        else:
            return hash(self.html)

    def plan(self, context) -> RenderPlan:
        """Plan the raw HTML for rendering, without escaping.

        Args:
            context: Rendering context.

        Returns:
            A raw RenderPlan with the HTML as-is when there are no extra
            settings; otherwise a div tag RenderPlan wrapping the raw HTML.
        """
        if not self.extra_settings:
            return RenderPlan(
                kind="raw",
                raw_html=self.html,
            )
        return self._plan_tag(
            context=context, children=[RenderPlan(kind="raw", raw_html=self.html)]
        )

    # TODO: Are we escaping HTML correctly in Text component?


@dataclass(repr=False)
class HtmlTag(Component):
    """Renders a generic HTML tag with content.

    Attributes:
        tag: The HTML tag name.
        content: List of page content items to wrap in the tag.
    """

    tag: str
    content: List[PageContent]

    ARGUMENTS = [
        ComponentArgument("tag", kind="positional"),
        ComponentArgument("content", kind="var", is_content=True),
    ]

    def __init__(self, tag: str, *content: PageContent, **extra_settings):
        self.tag = tag
        self.content, self.extra_settings = handle_arguments_compatibility(
            list(content), extra_settings
        )
