from dataclasses import dataclass
from typing import List

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
    additional_css: List[str] = None
    additional_header: List[str] = None

    def __post_init__(self):
        if self.additional_css is None:
            self.additional_css = []
        if self.additional_header is None:
            self.additional_header = []

    def render(self) -> str:
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
