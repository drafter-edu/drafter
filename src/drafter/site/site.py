from dataclasses import dataclass, field
from typing import List, Optional

from drafter.site.site_information import SiteInformation

DRAFTER_TAG_IDS = {
    "ROOT": "drafter-root--",
    "SITE": "drafter-site--",
    "FRAME": "drafter-frame--",
    "HEADER": "drafter-header--",
    "BODY": "drafter-body--",
    "FOOTER": "drafter-footer--",
    "FORM": "drafter-form--",
    "DEBUG": "drafter-debug--",
}

SITE_HTML_TEMPLATE = f"""
<div id="{DRAFTER_TAG_IDS["SITE"]}">
  <form id="{DRAFTER_TAG_IDS["FORM"]}">
    <div id="{DRAFTER_TAG_IDS["FRAME"]}">
        <div id="{DRAFTER_TAG_IDS["HEADER"]}"></div>
        <div id="{DRAFTER_TAG_IDS["BODY"]}">
        Loading
        </div>
        <div id="{DRAFTER_TAG_IDS["FOOTER"]}"></div>
    </div>
    <div id="{DRAFTER_TAG_IDS["DEBUG"]}"></div>
  </form>
</div>
"""


@dataclass
class Site:
    title: str = "Drafter Application"
    information: Optional[SiteInformation] = None
    additional_css: List[str] = field(default_factory=list)
    additional_header: List[str] = field(default_factory=list)

    def reset(self):
        self.information = None
        self.additional_css.clear()
        self.additional_header.clear()

    def render(self) -> str:
        """
        Renders the site HTML structure.

        Note: In Skulpt mode, this HTML is injected into the drafter-root div.
        The CSS and header content will be placed in the document body, which is
        valid HTML5. For production builds, CSS should ideally be passed to the
        HTML template's <head> section (see app/templating.py).
        """
        site_html = SITE_HTML_TEMPLATE

        # Add CSS if present
        if self.additional_css:
            css_content = "\n".join(self.additional_css)
            css_tag = f"<style>\n{css_content}\n</style>"
            site_html = css_tag + site_html

        # Add header content if present
        if self.additional_header:
            header_content = "\n".join(self.additional_header)
            site_html = header_content + site_html

        return site_html

    def update_information(
        self,
        author: str,
        description: str,
        sources: List[str],
        planning: List[str],
        links: List[str],
    ):
        if self.information is None:
            self.information = SiteInformation(
                author=author,
                description=description,
                sources=sources,
                planning=planning,
                links=links,
            )
        else:
            self.information.author = author
            self.information.description = description
            self.information.sources = sources
            self.information.planning = planning
            self.information.links = links
