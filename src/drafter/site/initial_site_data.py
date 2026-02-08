from dataclasses import dataclass, field


@dataclass
class InitialSiteData:
    """Metadata and HTML for the initial page sent to the browser.

    Attributes:
        site_html: HTML markup for the site frame structure.
        site_title: Page title for the browser tab and SEO.
        additional_js: List of JavaScript file URLs to load.
        additional_scripts: List of inline JavaScript code strings.
        additional_css: List of CSSLink objects (URL + classes) to load.
        additional_style: List of inline CSS code strings.
        additional_header: List of additional HTML header elements.
        use_shadow_dom: Whether to use Shadow DOM for style isolation.
        error: Whether an error occurred during initialization.
    """

    site_html: str
    site_title: str
    additional_js: list = field(default_factory=list)
    additional_scripts: list[str] = field(default_factory=list)
    additional_css: list = field(default_factory=list)  # List of CSSLink objects
    additional_style: list[str] = field(default_factory=list)
    additional_header: list[str] = field(default_factory=list)
    use_shadow_dom: bool = True
    error: bool = False

