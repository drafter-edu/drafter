from dataclasses import dataclass
from typing import Any, List, Dict
from drafter.components.page_content import Component


@dataclass
class LineBreak(Component):
    def __str__(self) -> str:
        return "<br />"


@dataclass
class HorizontalRule(Component):
    def __str__(self) -> str:
        return "<hr />"


@dataclass(repr=False)
class _HtmlGroup(Component):
    content: List[Any]
    extra_settings: Dict
    kind: str

    def __init__(self, *args, **kwargs):
        self.content = list(args)
        if "content" in kwargs:
            self.content.extend(kwargs.pop("content"))
        if "kind" in kwargs:
            self.kind = kwargs.pop("kind")
        if "extra_settings" in kwargs:
            self.extra_settings = kwargs.pop("extra_settings")
            self.extra_settings.update(kwargs)
        else:
            self.extra_settings = kwargs

    def __repr__(self):
        if self.extra_settings:
            return f"{self.kind.capitalize()}({', '.join(repr(item) for item in self.content)}, {self.extra_settings})"
        return f"{self.kind.capitalize()}({', '.join(repr(item) for item in self.content)})"

    def __str__(self) -> str:
        parsed_settings = self.parse_extra_settings(**self.extra_settings)
        return f"<{self.kind} {parsed_settings}>{''.join(str(item) for item in self.content)}</{self.kind}>"


@dataclass(repr=False)
class Span(_HtmlGroup):
    kind = "span"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


@dataclass(repr=False)
class Div(_HtmlGroup):
    kind = "div"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


Division = Div
Box = Div


@dataclass(repr=False)
class Row(Div):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extra_settings["style_display"] = "flex"
        self.extra_settings["style_flex_direction"] = "row"
        self.extra_settings["style_align_items"] = "center"


@dataclass
class _HtmlList(Component):
    items: List[Any]
    kind: str = ""

    def __init__(self, items: List[Any], **kwargs):
        self.items = items
        self.extra_settings = kwargs

    def __str__(self) -> str:
        parsed_settings = self.parse_extra_settings(**self.extra_settings)
        items = "\n".join(f"<li>{item}</li>" for item in self.items)
        return f"<{self.kind} {parsed_settings}>{items}</{self.kind}>"


class NumberedList(_HtmlList):
    kind = "ol"


class BulletedList(_HtmlList):
    kind = "ul"
