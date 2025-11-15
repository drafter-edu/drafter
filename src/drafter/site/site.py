from dataclasses import dataclass, field
from typing import List, Optional

from drafter.styling.themes import get_theme_system
from drafter.site.initial_site_data import InitialSiteData
from drafter.site.site_information import SiteInformation

GLOBAL_DRAFTER_CSS_PATHS = {
    True: "assets/css/drafter_debug.css",
    False: "assets/css/drafter_deploy.css",
}

DRAFTER_TAG_IDS = {
    "ROOT": "drafter-root--",
    "SITE": "drafter-site--",
    "FRAME": "drafter-frame--",
    "HEADER": "drafter-header--",
    "BODY": "drafter-body--",
    "FOOTER": "drafter-footer--",
    "FORM": "drafter-form--",
    "DEBUG": "drafter-debug--",
    "PADDING_V": "drafter-padding-v--",
    "PADDING_H": "drafter-padding-h--",
}

DRAFTER_TAG_CLASSES = {
    "THEME": "drafter-theme--",
}

SITE_HTML_TEMPLATE = f"""
<div id="{DRAFTER_TAG_IDS["SITE"]}" class="{DRAFTER_TAG_IDS["SITE"]}">
    <div class="{DRAFTER_TAG_IDS["PADDING_H"]}"></div>
  <form id="{DRAFTER_TAG_IDS["FORM"]}" class="{DRAFTER_TAG_IDS["FORM"]}">
    <div class="{DRAFTER_TAG_IDS["PADDING_V"]}"></div>
    <div id="{DRAFTER_TAG_IDS["FRAME"]}" class="{DRAFTER_TAG_IDS["FRAME"]}">
        <div id="{DRAFTER_TAG_IDS["HEADER"]}" class="{DRAFTER_TAG_IDS["HEADER"]}"></div>
        <div id="{DRAFTER_TAG_IDS["BODY"]}" class="{DRAFTER_TAG_IDS["BODY"]}">
        Loading
        </div>
        <div id="{DRAFTER_TAG_IDS["FOOTER"]}" class="{DRAFTER_TAG_IDS["FOOTER"]}"></div>
    </div>
    <div class="{DRAFTER_TAG_IDS["PADDING_V"]}"></div>
  </form>
  <div class="{DRAFTER_TAG_IDS["PADDING_H"]}"></div>
  <div id="{DRAFTER_TAG_IDS["DEBUG"]}" class="{DRAFTER_TAG_IDS["DEBUG"]}"></div>
</div>
"""


@dataclass
class Site:
    title: str = "Drafter Application"
    information: Optional[SiteInformation] = None
    theme: str = "default"
    in_debug_mode: bool = True
    # Additional linked CSS
    additional_css: List[str] = field(default_factory=list)
    # Additional raw style content
    additional_style: List[str] = field(default_factory=list)
    # Additional linked JavaScript
    additional_js: List[str] = field(default_factory=list)
    # Additional raw header content
    additional_header: List[str] = field(default_factory=list)

    def reset(self):
        self.information = None
        self.additional_css.clear()
        self.additional_style.clear()
        self.additional_js.clear()
        self.additional_header.clear()

    def _get_theme_headers(self) -> tuple[list[str], list[str]]:
        theme_system = get_theme_system()
        if not theme_system.is_valid_theme(self.theme):
            raise ValueError(theme_system.suggest_mistake(self.theme))
        theme = theme_system.get_theme(self.theme)
        return list(theme.css_paths), list(theme.js_paths)

    def render(self) -> InitialSiteData:
        """
        Renders the site HTML structure.
        """
        site_html = SITE_HTML_TEMPLATE

        additional_css, additional_js = self._get_theme_headers()
        additional_css.insert(0, GLOBAL_DRAFTER_CSS_PATHS[self.in_debug_mode])
        
        # Add debug panel CSS when in debug mode
        if self.in_debug_mode:
            additional_css.append("assets/css/debug-panel.css")
        
        additional_headers, additional_styles = [], []

        # Add CSS if present
        if self.additional_css:
            additional_css.extend(self.additional_css)

        # Add raw style content if present
        if self.additional_style:
            additional_styles.extend(self.additional_style)

        # Add header content if present
        if self.additional_header:
            additional_headers.extend(self.additional_header)

        # Add JavaScript if present
        if self.additional_js:
            additional_js.extend(self.additional_js)

        return InitialSiteData(
            site_html=site_html,
            site_title=self.title,
            additional_css=additional_css,
            additional_js=additional_js,
            additional_header=additional_headers,
            additional_style=additional_styles,
        )

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
