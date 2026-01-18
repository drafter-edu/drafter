from dataclasses import dataclass, field
from typing import List, Optional

from drafter.config.client_server import ClientServerConfiguration
from drafter.styling.themes import get_theme_system
from drafter.site.initial_site_data import InitialSiteData
from drafter.site.site_information import SiteInformation

GLOBAL_DRAFTER_CSS_PATHS = {
    True: "assets/css/drafter_debug.css",
    False: "assets/css/drafter_deploy.css",
}

BUILT_IN_ADDITIONAL_CSS_PATHS = ["assets/css/diff2html.min.css"]

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
    _configuration: Optional[ClientServerConfiguration] = None

    def set_configuration(self, configuration: ClientServerConfiguration):
        self._configuration = configuration

    def get_configuration(self) -> ClientServerConfiguration:
        if self._configuration is None:
            # TODO: SiteNotConfiguredError
            raise ValueError("Site configuration has not been set.")
        return self._configuration.copy()

    def update_configuration(self, key: str, value):
        if self._configuration is None:
            # TODO: SiteNotConfiguredError
            raise ValueError("Site configuration has not been set.")
        self._configuration.update_configuration(key, value)

    def reset(self):
        self._configuration = None

    def _get_theme_headers(self, configuration) -> tuple[list[str], list[str]]:
        theme_system = get_theme_system()
        if not theme_system.is_valid_theme(configuration.theme):
            raise ValueError(theme_system.suggest_mistake(configuration.theme))
        theme = theme_system.get_theme(configuration.theme)
        return list(theme.css_paths), list(theme.js_paths)

    def render(self) -> InitialSiteData:
        """
        Renders the site HTML structure.
        """
        site_html = SITE_HTML_TEMPLATE
        configuration = self.get_configuration()

        additional_css, additional_js = self._get_theme_headers(configuration)
        additional_css.insert(0, GLOBAL_DRAFTER_CSS_PATHS[configuration.in_debug_mode])
        additional_css.extend(BUILT_IN_ADDITIONAL_CSS_PATHS)
        additional_headers, additional_styles, additional_scripts = [], [], []

        # Add CSS if present
        if configuration.additional_css_content:
            additional_css.extend(configuration.additional_css_content)
        # Add raw style content if present
        if configuration.additional_style_content:
            additional_styles.extend(configuration.additional_style_content)

        # Add header content if present
        if configuration.additional_header_content:
            additional_headers.extend(configuration.additional_header_content)

        # Add JavaScript if present
        if configuration.additional_js_content:
            additional_js.extend(configuration.additional_js_content)

        if configuration.additional_script_content:
            additional_scripts.extend(configuration.additional_script_content)

        return InitialSiteData(
            site_html=site_html,
            site_title=configuration.site_title,
            additional_css=additional_css,
            additional_js=additional_js,
            additional_header=additional_headers,
            additional_style=additional_styles,
            additional_scripts=additional_scripts,
        )
