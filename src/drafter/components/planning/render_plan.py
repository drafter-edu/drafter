"""Render planning structures for component rendering.

Defines the RenderPlan and AssetBundle classes that describe how components
should be rendered to HTML, CSS, and JavaScript.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class AssetBundle:
    """Bundles CSS and JavaScript assets for a component.

    Attributes:
        css: Set of CSS strings or URLs to include.
        js: Set of JavaScript strings or URLs to include.
    """

    css: set[str]
    js: set[str]


# Newline Mode Stack Type Enumeration
class NewlineMode:
    """Enumeration for newline handling modes during rendering."""

    RETAIN = "retain"  # Leave newlines alone
    CONVERT_TO_BR = "convert_to_br"  # Convert newlines to <br> tags


@dataclass
class RenderPlan:
    """Describes how to render a component.

    Supports multiple render kinds:
    - "tag": HTML tag with attributes, children, and optional self-closing/whitespace handling
    - "fragment": Multiple child items without a wrapper tag
    - "emit": Call an emitter function to generate content
    - "raw": Raw HTML string (use cautiously)

    Attributes:
        kind: The render kind ("tag", "fragment", "emit", or "raw").
        assets: Optional CSS/JS bundles to load.
        tag_name: For "tag" kind, the HTML tag name (e.g., "div").
        attributes: For "tag" kind, dict of HTML attributes.
        children: For "tag" kind, child content rendered inside the tag.
        self_closing: For "tag" kind, whether tag self-closes (e.g., <br/>).
        collapse_whitespace: For "tag" kind, whether to collapse whitespace.
        newline_mode: For "tag" kind, how newlines in text content are
            handled: `NewlineMode.RETAIN` leaves them alone,
            `NewlineMode.CONVERT_TO_BR` (the default) converts them to
            <br> tags.
        known_attributes: For "tag" kind, list of attributes that might appear.
        id: Component identifier.
        items: For "fragment" kind, the items to render without a wrapper tag.
        emitter: For "emit" kind, function that generates content.
        raw_html: For "raw" kind, the raw HTML string.
    """

    kind: Literal["tag", "fragment", "emit", "raw"]
    # Common
    assets: AssetBundle | None = None

    # "tag" specific
    tag_name: str | None = None
    attributes: dict[str, Any] | None = None
    children: Any = None  #  PageContent | None
    self_closing: bool = False
    collapse_whitespace: bool = False
    newline_mode: str = NewlineMode.CONVERT_TO_BR
    # Attributes that might be on this tag, but are not explicitly handled
    known_attributes: list[str] | None = None
    id: str | None = None

    # "fragment" specific
    items: Any = None  # PageContent | None

    # "emit" specific
    emitter: Callable | None = None

    # "raw" specific
    raw_html: str | None = None
