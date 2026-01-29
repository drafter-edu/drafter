from typing import Union
from dataclasses import dataclass, field
from drafter.components import PageContent

SiteInformationType = Union[str, list, tuple, PageContent]


@dataclass
class SiteInformation:
    author: SiteInformationType = ""
    description: SiteInformationType = ""
    sources: SiteInformationType = field(default_factory=list)
    planning: SiteInformationType = field(default_factory=list)
    links: SiteInformationType = field(default_factory=list)

    def to_json(self):
        return {
            "author": repr(self.author),
            "description": repr(self.description),
            "sources": repr(self.sources),
            "planning": repr(self.planning),
            "links": repr(self.links),
        }

    def copy(self) -> "SiteInformation":
        return SiteInformation(
            author=self.author,
            description=self.description,
            sources=list(self.sources)
            if isinstance(self.sources, (list, tuple))
            else self.sources,
            planning=list(self.planning)
            if isinstance(self.planning, (list, tuple))
            else self.planning,
            links=list(self.links)
            if isinstance(self.links, (list, tuple))
            else self.links,
        )

    def get_parts(self):
        yield "Author", self.author
        yield "Description", self.description
        yield "Sources", self.sources
        yield "Planning", self.planning
        yield "Links", self.links
