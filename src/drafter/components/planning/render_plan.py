from typing import Literal, Optional, Any, Callable
from dataclasses import dataclass


@dataclass
class AssetBundle:
    css: set[str]
    js: set[str]


@dataclass
class RenderPlan:
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
