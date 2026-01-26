"""Configuration for the Drafter ClientServer.

Defines ClientServerConfiguration dataclass for controlling client-side
rendering, UI theme, debugging, and asset serving.
"""

from dataclasses import dataclass, field
from typing import Optional, Callable, Union, Literal

from drafter.config.site_information import SiteInformation


@dataclass
class ClientServerConfiguration:
    """Configuration options for the ClientServer component.

    Controls how the server renders pages to the client, including theming,
    debugging, asset serving, and additional content/styling/scripts.

    Attributes:
        server_name: Internal server identifier.
        in_debug_mode: Enable debug mode with debug panel.
        enable_audit_logging: Enable audit logging of requests/responses.
        site_title: Title displayed in the UI.
        information: Optional SiteInformation object with site metadata.
        framed: Whether to frame the application.
        theme: Theme name (e.g., "default").
        deploy_image_path: Path for deployment images.
        override_asset_url: Custom asset URL (False to use defaults).
        additional_header_content: List of HTML strings for <head> section.
        additional_style_content: List of inline CSS strings.
        additional_css_content: List of external CSS URLs.
        additional_js_content: List of inline JavaScript strings.
        additional_script_content: List of external JS URLs.
        use_shadow_dom: Wrap app in Shadow DOM to prevent CSS conflicts.
        root_element_id: ID prefix for root element.
        system_routes: Dict mapping route names to handler callables.
    """

    server_name: str = "MAIN_SERVER"
    in_debug_mode: bool = True
    enable_audit_logging: bool = True
    site_title: str = "Drafter Application"
    information: Optional[SiteInformation] = None
    framed: bool = True
    theme: str = "default"
    deploy_image_path: str = ""

    override_asset_url: Union[bool, str] = False
    # Literal HTML content
    additional_header_content: list[str] = field(default_factory=list)
    # Raw literal CSS
    additional_style_content: list[str] = field(default_factory=list)
    # Linked CSS Content
    additional_css_content: list[str] = field(default_factory=list)
    # Raw literal JavaScript
    additional_js_content: list[str] = field(default_factory=list)
    # Linked JavaScript Content
    additional_script_content: list[str] = field(default_factory=list)
    # Shadow DOM CSS
    use_shadow_dom: bool = False
    # Root element id, if None then will become
    root_element_id: str = "drafter-root--"
    # System Routes
    system_routes: dict[str, Optional[Callable]] = field(default_factory=dict)
    # TODO: Handle the system routes as configuration settings
    # TODO: Config setting to show white flash on navigation, also to control behavior
    # TODO: Config setting to add spinner to buttons
    # TODO: Config setting to forbid external links

    def to_json(self) -> dict:
        return {
            "server_name": self.server_name,
            "in_debug_mode": self.in_debug_mode,
            "enable_audit_logging": self.enable_audit_logging,
            "site_title": self.site_title,
            "information": self.information.to_json() if self.information else None,
            "framed": self.framed,
            "theme": self.theme,
            "override_asset_url": self.override_asset_url,
            "deploy_image_path": self.deploy_image_path,
            "additional_header_content": self.additional_header_content,
            "additional_style_content": self.additional_style_content,
            "additional_css_content": self.additional_css_content,
            "additional_js_content": self.additional_js_content,
            "additional_script_content": self.additional_script_content,
            "use_shadow_dom": self.use_shadow_dom,
            "root_element_id": self.root_element_id,
            "system_routes": list(self.system_routes.keys()),
        }

    def copy(self) -> "ClientServerConfiguration":
        """
        Creates a copy of the current configuration instance.

        Returns:
            ClientServerConfiguration: A new instance of ClientServerConfiguration with the same values.
        """
        return ClientServerConfiguration(
            in_debug_mode=self.in_debug_mode,
            enable_audit_logging=self.enable_audit_logging,
            site_title=self.site_title,
            information=self.information,
            framed=self.framed,
            theme=self.theme,
            deploy_image_path=self.deploy_image_path,
            additional_header_content=list(self.additional_header_content),
            additional_style_content=list(self.additional_style_content),
            additional_css_content=list(self.additional_css_content),
            additional_js_content=list(self.additional_js_content),
            additional_script_content=list(self.additional_script_content),
            use_shadow_dom=self.use_shadow_dom,
            server_name=self.server_name,
            root_element_id=self.root_element_id,
            system_routes=dict(self.system_routes),
            override_asset_url=self.override_asset_url,
        )

    def update_multiple_configuration(self, **kwargs):
        """
        Updates multiple configuration settings at once using keyword arguments.

        Example usage:
            config.update_multiple_configuration(
                theme="dark",
                in_debug_mode=False,
                additional_header_content="<meta name='viewport' content='width=device-width, initial-scale=1'>"
            )

        This will update the theme to "dark", set debug mode to False, and add a viewport meta tag to the header content.
        """
        for key, value in kwargs.items():
            self.update_configuration(key, value)

    def update_configuration(self, key: str, value):
        """
        Updates a specific configuration key with a new value.

        Args:
            key: The configuration key to update (e.g., 'theme', 'in_debug_mode').
        """
        if not hasattr(self, key):
            # TODO: InvalidConfigurationKeyError
            raise ValueError(f"Invalid configuration key: {key}")
        # TODO: Add validation for specific keys if necessary (e.g., theme should be a valid theme name)
        if key in (
            "additional_css_content",
            "additional_style_content",
            "additional_js_content",
            "additional_script_content",
            "additional_header_content",
        ):
            current_value = getattr(self, key)
            if isinstance(current_value, list):
                current_value.append(value)
            else:
                raise ValueError(
                    f"Configuration key {key} is not a list and cannot be appended to."
                )
        elif key in ("author", "description", "sources", "planning", "links"):
            if self.information is None:
                self.information = SiteInformation()
            setattr(self.information, key, value)
        else:
            setattr(self, key, value)
