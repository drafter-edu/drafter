"""Configuration for the Drafter ClientServer.

Defines ClientServerConfiguration dataclass for controlling client-side
rendering, UI theme, debugging, and asset serving.
"""

from dataclasses import dataclass, field
from typing import Optional, Callable, Union

from drafter.helpers.env_vars import EnvVars
from drafter.config.base import BaseConfiguration
from drafter.config.site_information import SiteInformation


@dataclass
class ClientServerConfiguration(BaseConfiguration):
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
        external_pages: List of external page links (URL or (URL, Text) tuples).
    """

    server_name: str = "MAIN_SERVER"
    in_debug_mode: bool = True
    enable_audit_logging: bool = True
    site_title: str = "Drafter Application"
    information: Optional[SiteInformation] = None
    # Parse semicolon-separated format: "URL Text;URL Text;URL;..."
    external_pages: Optional[list[Union[str, tuple[str, str]]]] = None
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
    
    @staticmethod
    def parse_env_variables(env_vars: dict) -> dict:
        result = EnvVars(env_vars)
        result.get_string_if_exists("DRAFTER_SERVER_NAME", "server_name")
        result.get_bool_if_exists("DRAFTER_IN_DEBUG_MODE", "in_debug_mode")
        result.get_bool_if_exists("DRAFTER_ENABLE_AUDIT_LOGGING", "enable_audit_logging")
        result.get_string_if_exists("DRAFTER_SITE_TITLE", "site_title")
        result.get_string_if_exists("DRAFTER_FRAMED", "framed")
        result.get_string_if_exists("DRAFTER_THEME", "theme")
        result.get_string_if_exists("DRAFTER_DEPLOY_IMAGE_PATH", "deploy_image_path")
        result.get_string_list_if_exists("DRAFTER_EXTERNAL_PAGES", "external_pages", ";")
        result.get_string_if_exists("DRAFTER_OVERRIDE_ASSET_URL", "override_asset_url")
        result.get_string_list_if_exists("DRAFTER_ADDITIONAL_HEADER_CONTENT", "additional_header_content", ";")
        result.get_string_list_if_exists("DRAFTER_ADDITIONAL_STYLE_CONTENT", "additional_style_content", ";")
        result.get_string_list_if_exists("DRAFTER_ADDITIONAL_CSS_CONTENT", "additional_css_content", ";")
        result.get_string_list_if_exists("DRAFTER_ADDITIONAL_JS_CONTENT", "additional_js_content", ";")
        result.get_string_list_if_exists("DRAFTER_ADDITIONAL_SCRIPT_CONTENT", "additional_script_content", ";")
        result.get_bool_if_exists("DRAFTER_USE_SHADOW_DOM", "use_shadow_dom")
        result.get_string_if_exists("DRAFTER_ROOT_ELEMENT_ID", "root_element_id")
        return result.as_dict()
    
    @staticmethod
    def extend_parser(parser):
        group = parser.add_argument_group("Client Server Configuration")
        group.add_argument(
            "--server-name",
            type=str,
            help="Internal server identifier",
        )
        group.add_argument(
            "--debug",
            action="store_true",
            help="Enable debug mode with debug panel",
        )
        group.add_argument(
            "--audit-logging",
            action="store_true",
            help="Enable audit logging of requests/responses",
        )
        group.add_argument(
            "--framed",
            action="store_true",
            help="Whether to frame the application",
        )
        group.add_argument(
            "--theme",
            type=str,
            help="Theme name (e.g., 'default')",
        )
        group.add_argument(
            "--deploy-image-path",
            type=str,
            help="Path for deployment images",
        )
        group.add_argument(
            "--external-pages",
            type=str,
            help="Semicolon-separated list of external page links (URL or 'URL Text' tuples)",
        )
        group.add_argument(
            "--additional-header-content",
            type=str,
            help="Semicolon-separated list of HTML strings for <head> section",
        )
        group.add_argument(
            "--additional-style-content",
            type=str,
            help="Semicolon-separated list of inline CSS strings",
        )
        group.add_argument(
            "--additional-css-content",
            type=str,
            help="Semicolon-separated list of external CSS URLs",
        )
        group.add_argument(
            "--additional-js-content",
            type=str,
            help="Semicolon-separated list of inline JavaScript strings",
        )
        group.add_argument(
            "--additional-script-content",
            type=str,
            help="Semicolon-separated list of external JS URLs",
        )
        group.add_argument(
            "--use-shadow-dom",
            action="store_true",
            help="Wrap app in Shadow DOM to prevent CSS conflicts",
        )
        group.add_argument(
            "--root-element-id",
            type=str,
            help="ID prefix for root element",
        )
        return group
    
    @staticmethod
    def parse_args(parsed_args: dict) -> dict:
        result = {}
        if parsed_args.get("server_name"):
            result["server_name"] = parsed_args["server_name"]
        if parsed_args.get("debug"):
            result["in_debug_mode"] = True
        if parsed_args.get("audit_logging"):
            result["enable_audit_logging"] = True
        if parsed_args.get("site_title"):
            result["site_title"] = parsed_args["site_title"]
        if parsed_args.get("framed"):
            result["framed"] = True
        if parsed_args.get("theme"):
            result["theme"] = parsed_args["theme"]
        if parsed_args.get("deploy_image_path"):
            result["deploy_image_path"] = parsed_args["deploy_image_path"]
        if parsed_args.get("external_pages"):
            result["external_pages"] = [
                page.strip() for page in parsed_args["external_pages"].split(";")
            ]
        if parsed_args.get("override_asset_url"):
            result["override_asset_url"] = parsed_args["override_asset_url"]
        if parsed_args.get("additional_header_content"):
            result["additional_header_content"] = [
                content.strip() for content in parsed_args["additional_header_content"].split(";")
            ]
        if parsed_args.get("additional_style_content"):
            result["additional_style_content"] = [
                content.strip() for content in parsed_args["additional_style_content"].split(";")
            ]
        if parsed_args.get("additional_css_content"):
            result["additional_css_content"] = [
                content.strip() for content in parsed_args["additional_css_content"].split(";")
            ]
        if parsed_args.get("additional_js_content"):
            result["additional_js_content"] = [
                content.strip() for content in parsed_args["additional_js_content"].split(";")
            ]
        if parsed_args.get("additional_script_content"):
            result["additional_script_content"] = [
                content.strip() for content in parsed_args["additional_script_content"].split(";")
            ]
        if parsed_args.get("use_shadow_dom"):
            result["use_shadow_dom"] = True
        if parsed_args.get("root_element_id"):
            result["root_element_id"] = parsed_args["root_element_id"]
        return result

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
            "external_pages": self.external_pages,
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
            information=self.information.copy() if self.information else None,
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
            external_pages=list(self.external_pages) if self.external_pages else None,
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
            
    SITE_INFORMATION_KEYS = ("author", "description", "sources", "planning", "links")

    def update_configuration(self, key: str, value):
        """
        Updates a specific configuration key with a new value.

        Args:
            key: The configuration key to update (e.g., 'theme', 'in_debug_mode').
        """
        if not hasattr(self, key) and key not in self.SITE_INFORMATION_KEYS:
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
        elif key in self.SITE_INFORMATION_KEYS:
            if self.information is None:
                self.information = SiteInformation()
            setattr(self.information, key, value)
        else:
            setattr(self, key, value)
