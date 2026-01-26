"""Render planning structures for component rendering.

Defines the RenderPlan and AssetBundle classes that describe how components
should be rendered to HTML, CSS, and JavaScript.
"""

from typing import Literal, Optional, Any, Callable
from dataclasses import dataclass


@dataclass
class AssetBundle:
    """Bundles CSS and JavaScript assets for a component.

    Attributes:
        css: Set of CSS strings or URLs to include.
        js: Set of JavaScript strings or URLs to include.
    """

    css: set[str]
    js: set[str]


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
        children: For "tag" kind, child content; for "fragment" kind, items to render.
        self_closing: For "tag" kind, whether tag self-closes (e.g., <br/>).
        collapse_whitespace: For "tag" kind, whether to collapse whitespace.
        known_attributes: For "tag" kind, list of attributes that might appear.
        id: Component identifier.
        emitter: For "emit" kind, function that generates content.
        raw_html: For "raw" kind, the raw HTML string.
    """

    kind: Literal["tag", "fragment", "emit", "raw"]
    # Common
    assets: Optional[AssetBundle] = None

    # "tag" specific
    tag_name: Optional[str] = None
    attributes: Optional[dict[str, Any]] = None
    children: Any = None  #  PageContent | None
    self_closing: bool = False
    collapse_whitespace: bool = False
    # Attributes that might be on this tag, but are not explicitly handled
    known_attributes: Optional[list[str]] = None
    id: Optional[str] = None

    # "fragment" specific
    items: Any = None  # PageContent | None

    # "emit" specific
    emitter: Optional[Callable] = None

    # "raw" specific
    raw_html: Optional[str] = None
