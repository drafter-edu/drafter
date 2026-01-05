from dataclasses import dataclass
import html
from typing import Any, List
from drafter.components.layout import handle_arguments_compatibility
from drafter.components.page_content import Component, PageContent
from drafter.components.planning.render_plan import RenderPlan


@dataclass(repr=False)
class Pre(Component):
    tag = "pre"

    COLLAPSE_WHITESPACE = True

    def __init__(self, *content: PageContent, **extra_settings):
        self.children, self.extra_settings = handle_arguments_compatibility(
            list(content), extra_settings
        )


PreformattedText = Pre


@dataclass
class Header(Component):
    body: PageContent
    level: int = 1

    POSITIONAL_ARGS = ["level"]
    DEFAULT_ARGS = {"level": 1}

    def __init__(self, body: PageContent, level: int = 1, **extra_settings):
        self.body = body
        self.level = level
        if level < 1 or level > 6:
            raise ValueError("Header level must be between 1 and 6")
        self.extra_settings = extra_settings

    def get_children(self) -> list[PageContent]:
        return [self.body]

    def get_tag(self) -> str:
        return f"h{self.level}"


@dataclass
class Text(Component):
    body: str
    extra_settings: dict

    def __init__(self, body: str, **extra_settings):
        self.body = body
        if "body" in extra_settings:
            self.body = extra_settings.pop("body")
        self.extra_settings = extra_settings

    def __eq__(self, other):
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
        return RenderPlan(
            kind="tag",
            tag_name="span",
            attributes=self.extra_settings,
            children=[html.escape(self.body)],
        )


@dataclass
class RawHTML(Text):
    """
    A component that renders raw HTML without escaping.

    WARNING: Only use with trusted HTML content to avoid XSS vulnerabilities.
    This component bypasses HTML escaping and renders content as-is.

    :param html: The raw HTML string to render
    """

    def __init__(self, html: str, **extra_settings):
        super().__init__(html, **extra_settings)

    def plan(self, context) -> RenderPlan:
        if not self.extra_settings:
            return RenderPlan(
                kind="raw",
                raw_html=self.body,
            )
        return RenderPlan(
            kind="tag",
            tag_name="span",
            attributes=self.extra_settings,
            children=[self.body],
        )

    # TODO: Are we escaping HTML correctly in Text component?
