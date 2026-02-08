from dataclasses import dataclass, field
from typing import List, Optional, Union

from drafter.config.client_server import ClientServerConfiguration
from drafter.config.urls import determine_assets_url
from drafter.styling.themes import get_theme_system
from drafter.site.initial_site_data import InitialSiteData
from drafter.config.site_information import SiteInformation


@dataclass
class CSSLink:
    """Represents a CSS link with optional classes.

    Attributes:
        url: The URL or path to the CSS file.
        classes: Optional list of CSS classes to attach to the link element.
    """

    url: str
    classes: set[str] = field(default_factory=set)

    def __repr__(self):
        return f"CSSLink(url='{self.url}', classes={self.classes})"


GLOBAL_DRAFTER_CSS_PATHS = {
    True: CSSLink(url="css/drafter_debug.css", classes={"drafter-debug-css--"}),
    False: CSSLink(url="css/drafter_deploy.css", classes={"drafter-non-debug-css--"}),
}

BUILT_IN_ADDITIONAL_CSS_PATHS = [CSSLink(url="css/diff2html.min.css")]
DRAFTER_TAG_IDS = {
    "ROOT": "drafter-root--",
    "SHADOW_HOST": "drafter-shadow-host--",
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
    "DEBUG_CSS": "drafter-debug-css--",
    "NON_DEBUG_CSS": "drafter-non-debug-css--",
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

SITE_HTML_SHADOW_DOM_TEMPLATE = f'<div id="{DRAFTER_TAG_IDS["SHADOW_HOST"]}"></div>'


@dataclass
class Site:
    """Manage the site HTML frame structure and configuration.

    Attributes:
        _configuration: Current server configuration instance.
    """

    _configuration: Optional[ClientServerConfiguration] = None

    def set_configuration(self, configuration: ClientServerConfiguration):
        """Set the site's active configuration.

        Args:
            configuration: ClientServerConfiguration to use.
        """
        self._configuration = configuration

    def get_configuration(self) -> ClientServerConfiguration:
        """Retrieve a copy of the current configuration.

        Returns:
            ClientServerConfiguration: Copy of the active configuration.

        Raises:
            ValueError: If configuration has not been set.
        """
        if self._configuration is None:
            # TODO: SiteNotConfiguredError
            raise ValueError("Site configuration has not been set.")
        return self._configuration.copy()

    def update_configuration(self, key: str, value):
        """Update a single configuration key.

        Args:
            key: Configuration property name.
            value: New value for the property.

        Raises:
            ValueError: If configuration has not been set.
        """
        if self._configuration is None:
            # TODO: SiteNotConfiguredError
            raise ValueError("Site configuration has not been set.")
        self._configuration.update_configuration(key, value)

    def reset(self):
        """Clear the site configuration."""
        self._configuration = None

    def _get_theme_headers(self, configuration) -> tuple[list[CSSLink], list[str]]:
        """Retrieve CSS and JS paths for the active theme.

        Args:
            configuration: Server configuration with theme setting.

        Returns:
            Tuple of (css_paths list of CSSLink, js_paths list of strings).

        Raises:
            ValueError: If theme is not recognized.
        """
        theme_system = get_theme_system()
        if not theme_system.is_valid_theme(configuration.theme):
            raise ValueError(theme_system.suggest_mistake(configuration.theme))
        theme = theme_system.get_theme(configuration.theme)
        css_links = [CSSLink(url=path) for path in theme.css_paths]
        return css_links, list(theme.js_paths)

    def remap_urls_to_assets(self, *urls, configuration):
        """Prefixes the individual asset URLs with the appropriate
        path part.

        Args:
            urls: Individual asset URLs to remap.
            configuration: The current ClientServerConfiguration.

        Returns:
            list[str]: List of remapped asset URLs.
        """
        return [
            f"{determine_assets_url(configuration.override_asset_url)}/{url}"
            for url in urls
        ]

    def render(self) -> InitialSiteData:
        """Render the site HTML structure with assets and configuration.

        Returns:
            InitialSiteData: HTML frame, title, and asset references.
        """
        configuration = self.get_configuration()

        site_html = SITE_HTML_TEMPLATE

        additional_css, additional_js = self._get_theme_headers(configuration)
        
        # Add global CSS with appropriate classes
        global_css_link = GLOBAL_DRAFTER_CSS_PATHS[configuration.in_debug_mode]
        additional_css.insert(0, global_css_link)
        
        # Add built-in CSS
        additional_css.extend(BUILT_IN_ADDITIONAL_CSS_PATHS)
        
        # Remap URLs for CSS links
        additional_css = [
            CSSLink(url=self.remap_urls_to_assets(css.url, configuration=configuration)[0], classes=css.classes)
            for css in additional_css
        ]
        
        additional_js = self.remap_urls_to_assets(
            *additional_js, configuration=configuration
        )

        additional_headers, additional_styles, additional_scripts = [], [], []

        # Add CSS if present (and remap URLs)
        if configuration.additional_css_content:
            remapped_additional_css = self.remap_urls_to_assets(
                *configuration.additional_css_content, configuration=configuration
            )
            additional_css.extend([CSSLink(url=url) for url in remapped_additional_css])
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
            use_shadow_dom=configuration.use_shadow_dom,
        )
