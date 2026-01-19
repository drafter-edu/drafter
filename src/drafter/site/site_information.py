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
