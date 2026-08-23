"""Text components for displaying written content.

Defines `Text` (plain text in a span), `Header` (headings h1-h6),
`Pre`/`PreformattedText`, `BlockQuote`, `InlineCode`, `RawHTML`
(unescaped HTML, for trusted content only), and the generic `HtmlTag`.

Also defines the semantic inline text components: `Strong`, `Emphasis`,
`InlineQuotation`, `DefinitionTerm`, `Abbreviation`, `DeletedText`,
`InsertedText`, `KeyboardInput`, `MarkedText`, `SampleOutput`,
`SmallText`, `Superscript`, `Subscript`, and `InlineVariable`.
"""

import html
from dataclasses import dataclass
from datetime import date, time
from datetime import datetime as datetime_type

from drafter.components.layout import BlockComponent, handle_arguments_compatibility
from drafter.components.page_content import Component, ComponentArgument, PageContent
from drafter.components.planning.render_plan import NewlineMode, RenderPlan
from drafter.data.errors import StudentFacingError


def normalize_datetime(value) -> str | None:
    """Convert a datetime-like value into its ISO string form.

    Args:
        value: A string, None, or a `datetime`/`date`/`time` object.

    Returns:
        The value unchanged if it is a string or None; otherwise its
        `isoformat()` representation (or `str` as a last resort).
    """
    if value is None or isinstance(value, str):
        return value
    if isinstance(value, (datetime_type, date, time)):
        return value.isoformat()
    return str(value)


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

    cite: str | None
    content: list[PageContent]
    tag = "blockquote"

    ARGUMENTS = [
        ComponentArgument("cite", kind="positional", default_value=None),
        ComponentArgument("content", kind="var", is_content=True),
    ]

    def __init__(self, cite: str | None, *content: PageContent, **extra_settings):
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
            StudentFacingError: If level is not between 1 and 6.
        """
        self.body = body
        self.level = level
        if level < 1 or level > 6:
            raise StudentFacingError(
                f"Header level must be between 1 and 6, not {level!r}",
                friendly=(
                    "Headers only come in six sizes, so the level argument "
                    "must be a number from 1 (biggest) to 6 (smallest)."
                ),
                steps=(
                    "Change the level argument of this Header to a number from 1 to 6.",
                ),
            )
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

    def __init__(self, body: str | int | float | bool, **extra_settings):
        """Initialize text component.

        Args:
            body: The text content to display. Numbers and booleans are
                converted to their text form.
            **extra_settings: Additional HTML attributes and styles.
        """
        if "body" in extra_settings:
            body = extra_settings.pop("body")
        if isinstance(body, (int, float, bool)):
            body = str(body)
        self.body = body
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
        elif isinstance(other, (int, float, bool)):
            # Plain values are stringified at construction, so compare the text form
            return self.extra_settings == {} and self.body == str(other)
        return NotImplemented

    def __hash__(self):
        """Hash by body text, plus any extra settings when present."""
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

    content: list[PageContent]

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
        """Compare equal to a RawHTML (or plain string) with the same HTML."""
        if isinstance(other, RawHTML):
            return (
                self.html == other.html and self.extra_settings == other.extra_settings
            )
        elif isinstance(other, str):
            return self.extra_settings == {} and self.html == other
        return NotImplemented

    def __hash__(self):
        """Hash by HTML string, plus any extra settings when present."""
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


class Strong(BlockComponent):
    """Renders strongly important text (strong), typically shown in bold.

    Attributes:
        content: List of page content items to display with strong importance.
        tag: The HTML tag name, always 'strong'.
    """

    tag = "strong"


class Emphasis(BlockComponent):
    """Renders emphasized text (em), typically shown in italics.

    Attributes:
        content: List of page content items to display with emphasis.
        tag: The HTML tag name, always 'em'.
    """

    tag = "em"


class KeyboardInput(BlockComponent):
    """Renders keyboard input text (kbd), typically shown in monospace.

    Attributes:
        content: List of page content items representing keyboard input.
        tag: The HTML tag name, always 'kbd'.
    """

    tag = "kbd"


class MarkedText(BlockComponent):
    """Renders marked/highlighted text (mark).

    Attributes:
        content: List of page content items to highlight.
        tag: The HTML tag name, always 'mark'.
    """

    tag = "mark"


class SampleOutput(BlockComponent):
    """Renders sample program output (samp), typically shown in monospace.

    Attributes:
        content: List of page content items representing sample output.
        tag: The HTML tag name, always 'samp'.
    """

    tag = "samp"


class SmallText(BlockComponent):
    """Renders side-comment text (small), typically shown in a smaller font.

    Attributes:
        content: List of page content items to display in smaller text.
        tag: The HTML tag name, always 'small'.
    """

    tag = "small"


class Superscript(BlockComponent):
    """Renders superscript text (sup), raised above the baseline.

    Attributes:
        content: List of page content items to display as superscript.
        tag: The HTML tag name, always 'sup'.
    """

    tag = "sup"


class Subscript(BlockComponent):
    """Renders subscript text (sub), lowered below the baseline.

    Attributes:
        content: List of page content items to display as subscript.
        tag: The HTML tag name, always 'sub'.
    """

    tag = "sub"


class InlineVariable(BlockComponent):
    """Renders a variable name (var), typically shown in italics.

    Attributes:
        content: List of page content items representing the variable name.
        tag: The HTML tag name, always 'var'.
    """

    tag = "var"


@dataclass(repr=False)
class InlineQuotation(Component):
    """Renders an inline quotation element (q).

    Attributes:
        content: List of page content items to display inside the quotation.
        cite: The source URL of the quotation, if any.
        tag: The HTML tag name, always 'q'.
    """

    content: list[PageContent]
    cite: str | None
    tag = "q"

    KNOWN_ATTRS = ["cite"]
    ARGUMENTS = [
        ComponentArgument("content", kind="var", is_content=True),
        ComponentArgument("cite", kind="keyword", default_value=None),
    ]

    def __init__(
        self, *content: PageContent, cite: str | None = None, **extra_settings
    ):
        """Initialize inline quotation component.

        Args:
            *content: Variable-length content to display inside the quotation.
            cite: The source URL of the quotation, if any.
            **extra_settings: Additional HTML attributes and styles.
        """
        self.content, self.extra_settings = handle_arguments_compatibility(
            list(content), extra_settings
        )
        self.cite = cite


@dataclass(repr=False)
class DefinitionTerm(Component):
    """Renders a definition term element (dfn), marking the term being defined.

    Attributes:
        content: List of page content items containing the term.
        title: The full term being defined, shown as a tooltip, if any.
        tag: The HTML tag name, always 'dfn'.
    """

    content: list[PageContent]
    title: str | None
    tag = "dfn"

    ARGUMENTS = [
        ComponentArgument("content", kind="var", is_content=True),
        ComponentArgument("title", kind="keyword", default_value=None),
    ]

    def __init__(
        self, *content: PageContent, title: str | None = None, **extra_settings
    ):
        """Initialize definition term component.

        Args:
            *content: Variable-length content containing the term.
            title: The full term being defined, shown as a tooltip, if any.
            **extra_settings: Additional HTML attributes and styles.
        """
        self.content, self.extra_settings = handle_arguments_compatibility(
            list(content), extra_settings
        )
        self.title = title


@dataclass(repr=False)
class Abbreviation(Component):
    """Renders an abbreviation element (abbr).

    Attributes:
        content: List of page content items containing the abbreviation.
        title: The expanded form of the abbreviation, shown as a tooltip, if any.
        tag: The HTML tag name, always 'abbr'.
    """

    content: list[PageContent]
    title: str | None
    tag = "abbr"

    ARGUMENTS = [
        ComponentArgument("content", kind="var", is_content=True),
        ComponentArgument("title", kind="keyword", default_value=None),
    ]

    def __init__(
        self, *content: PageContent, title: str | None = None, **extra_settings
    ):
        """Initialize abbreviation component.

        Args:
            *content: Variable-length content containing the abbreviation.
            title: The expanded form of the abbreviation, if any.
            **extra_settings: Additional HTML attributes and styles.
        """
        self.content, self.extra_settings = handle_arguments_compatibility(
            list(content), extra_settings
        )
        self.title = title


@dataclass(repr=False)
class DeletedText(Component):
    """Renders deleted text (del), typically shown with a strikethrough.

    Attributes:
        content: List of page content items that were deleted.
        cite: A URL explaining the change, if any.
        datetime: When the change was made, as an ISO datetime string, if any.
        tag: The HTML tag name, always 'del'.
    """

    content: list[PageContent]
    cite: str | None
    datetime: str | None
    tag = "del"

    KNOWN_ATTRS = ["cite", "datetime"]
    ARGUMENTS = [
        ComponentArgument("content", kind="var", is_content=True),
        ComponentArgument("cite", kind="keyword", default_value=None),
        ComponentArgument("datetime", kind="keyword", default_value=None),
    ]

    def __init__(
        self,
        *content: PageContent,
        cite: str | None = None,
        datetime: str | datetime_type | date | time | None = None,
        **extra_settings,
    ):
        """Initialize deleted text component.

        Args:
            *content: Variable-length content that was deleted.
            cite: A URL explaining the change, if any.
            datetime: When the change was made; datetime/date/time objects
                are converted to their ISO string form.
            **extra_settings: Additional HTML attributes and styles.
        """
        self.content, self.extra_settings = handle_arguments_compatibility(
            list(content), extra_settings
        )
        self.cite = cite
        self.datetime = normalize_datetime(datetime)


@dataclass(repr=False)
class InsertedText(Component):
    """Renders inserted text (ins), typically shown with an underline.

    Attributes:
        content: List of page content items that were inserted.
        cite: A URL explaining the change, if any.
        datetime: When the change was made, as an ISO datetime string, if any.
        tag: The HTML tag name, always 'ins'.
    """

    content: list[PageContent]
    cite: str | None
    datetime: str | None
    tag = "ins"

    KNOWN_ATTRS = ["cite", "datetime"]
    ARGUMENTS = [
        ComponentArgument("content", kind="var", is_content=True),
        ComponentArgument("cite", kind="keyword", default_value=None),
        ComponentArgument("datetime", kind="keyword", default_value=None),
    ]

    def __init__(
        self,
        *content: PageContent,
        cite: str | None = None,
        datetime: str | datetime_type | date | time | None = None,
        **extra_settings,
    ):
        """Initialize inserted text component.

        Args:
            *content: Variable-length content that was inserted.
            cite: A URL explaining the change, if any.
            datetime: When the change was made; datetime/date/time objects
                are converted to their ISO string form.
            **extra_settings: Additional HTML attributes and styles.
        """
        self.content, self.extra_settings = handle_arguments_compatibility(
            list(content), extra_settings
        )
        self.cite = cite
        self.datetime = normalize_datetime(datetime)


@dataclass(repr=False)
class HtmlTag(Component):
    """Renders a generic HTML tag with content.

    Attributes:
        tag: The HTML tag name.
        content: List of page content items to wrap in the tag.
    """

    tag: str
    content: list[PageContent]

    ARGUMENTS = [
        ComponentArgument("tag", kind="positional"),
        ComponentArgument("content", kind="var", is_content=True),
    ]
    # The tag argument names the element itself; without this rename
    # suppression it would leak into the rendered output as an inline
    # style (the unknown-attribute fallback).
    RENAME_ATTRS = {"tag": ""}

    def __init__(self, tag: str, *content: PageContent, **extra_settings):
        self.tag = tag
        self.content, self.extra_settings = handle_arguments_compatibility(
            list(content), extra_settings
        )
