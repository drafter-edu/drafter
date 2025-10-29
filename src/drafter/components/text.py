from dataclasses import dataclass
from typing import Any, List
from drafter.components.layout import _HtmlGroup
from drafter.components.page_content import PageContent


@dataclass(repr=False)
class Pre(_HtmlGroup):
    content: List[Any]
    kind = "pre"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


PreformattedText = Pre


@dataclass
class Header(PageContent):
    body: str
    level: int = 1

    def __str__(self):
        return f"<h{self.level}>{self.body}</h{self.level}>"


@dataclass
class Text(PageContent):
    body: str
    extra_settings: dict

    def __init__(self, body: str, **kwargs):
        self.body = body
        if "body" in kwargs:
            self.body = kwargs.pop("content")
        if "extra_settings" in kwargs:
            self.extra_settings = kwargs.pop("extra_settings")
            self.extra_settings.update(kwargs)
        else:
            self.extra_settings = kwargs

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

    def __repr__(self):
        if self.extra_settings:
            return f"Text({self.body!r}, {self.extra_settings})"
        return f"Text({self.body!r})"

    def __str__(self):
        parsed_settings = self.parse_extra_settings(**self.extra_settings)
        if not parsed_settings:
            return self.body
        return f"<span {parsed_settings}>{self.body}</span>"
