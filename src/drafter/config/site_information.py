"""Student-facing site metadata for Drafter applications.

Defines SiteInformation, the metadata students provide about their site
(author, description, sources, planning, links), typically set via
set_site_information and shown in the site's information display.
"""

from dataclasses import dataclass, field
from typing import Union

from drafter.components import PageContent

SiteInformationType = Union[str, list, tuple, PageContent]
"""Type alias for the values a site information field can hold: a string, a
list or tuple of entries, or a PageContent component."""


@dataclass
class SiteInformation:
    """Metadata about a student's site.

    Each field may be a string, a list or tuple of entries, or a PageContent
    component.

    Attributes:
        author: Who created the site.
        description: What the site is about.
        sources: Sources or references used to build the site.
        planning: Planning artifacts for the site (e.g., sketches, notes).
        links: Related links for the site.
    """

    author: SiteInformationType = ""
    description: SiteInformationType = ""
    sources: SiteInformationType = field(default_factory=list)
    planning: SiteInformationType = field(default_factory=list)
    links: SiteInformationType = field(default_factory=list)

    def to_json(self):
        """Serialize the site information to a dictionary.

        Each field value is converted with `repr`, since values may be
        arbitrary objects such as PageContent components.

        Returns:
            A dictionary mapping each field name to the `repr` of its value.
        """
        return {
            "author": repr(self.author),
            "description": repr(self.description),
            "sources": repr(self.sources),
            "planning": repr(self.planning),
            "links": repr(self.links),
        }

    def copy(self) -> "SiteInformation":
        """Create a copy of this site information.

        List and tuple values are shallow-copied into new lists; other values
        are shared with the original.

        Returns:
            A new SiteInformation instance with the same values.
        """
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
        """Iterate over the site information fields as labeled parts.

        Yields:
            Tuples of a display label (e.g., "Author") and the corresponding
            field value, in declaration order.
        """
        yield "Author", self.author
        yield "Description", self.description
        yield "Sources", self.sources
        yield "Planning", self.planning
        yield "Links", self.links
