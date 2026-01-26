from dataclasses import dataclass
import html
from typing import Any, List
from drafter.components.layout import handle_arguments_compatibility
from drafter.components.page_content import Component, ComponentArgument, PageContent
from drafter.components.planning.render_plan import RenderPlan


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

    def __init__(self, *content: PageContent, **extra_settings):
        """Initialize preformatted text component.

        Args:
            *content: Variable-length content to display.
            **extra_settings: Additional HTML attributes and styles.
        """
        self.content = list(content)
        self.extra_settings = extra_settings


PreformattedText = Pre


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

    CONTENT_ARGS = ["body"]
    DEFAULT_ARGS = {"level": 1}
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
        if not self.extra_settings:
            return RenderPlan(
                kind="raw",
                raw_html=html.escape(self.body),
            )
        return self._plan_tag(context=context)


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
        if not self.extra_settings:
            return RenderPlan(
                kind="raw",
                raw_html=self.html,
            )
        return self._plan_tag(
            context=context, children=[RenderPlan(kind="raw", raw_html=self.html)]
        )

    # TODO: Are we escaping HTML correctly in Text component?
