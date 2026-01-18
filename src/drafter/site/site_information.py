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
