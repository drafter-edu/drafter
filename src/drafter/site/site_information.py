from typing import Union
from dataclasses import dataclass
from drafter.components import PageContent

SiteInformationType = Union[str, list, tuple, PageContent]


@dataclass
class SiteInformation:
    author: SiteInformationType
    description: SiteInformationType
    sources: SiteInformationType
    planning: SiteInformationType
    links: SiteInformationType
