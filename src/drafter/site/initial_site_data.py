from dataclasses import dataclass, field


@dataclass
class InitialSiteData:
    site_html: str
    site_title: str
    additional_js: list[str] = field(default_factory=list)
    additional_css: list[str] = field(default_factory=list)
    additional_header: list[str] = field(default_factory=list)
    error: bool = False
