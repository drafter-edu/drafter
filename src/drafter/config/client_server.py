"""Configuration for the Drafter ClientServer.

Defines ClientServerConfiguration dataclass for controlling client-side
rendering, UI theme, debugging, and asset serving.
"""

from collections.abc import Callable
from dataclasses import dataclass, field

from drafter.config.base import BaseConfiguration
from drafter.config.site_information import SiteInformation
from drafter.helpers.env_vars import EnvVars


@dataclass
class ClientServerConfiguration(BaseConfiguration):
    """Configuration options for the ClientServer component.

    Controls how the server renders pages to the client, including theming,
    debugging, asset serving, and additional content/styling/scripts.

    Attributes:
        server_name: Internal server identifier.
        in_debug_mode: Enable debug mode with debug panel.
        console_mode: Where captured print() output (and the Python REPL)
            appears: "auto" shows a console in the site footer in debug mode
            only, "hover" shows a floating console box (also in production),
            "toast" shows each printed line briefly as a corner toast, and
            "devtools" only mirrors output to the browser devtools console.
        enable_subtle_debug_entry: Show a subtle production-only control to enter debug mode.
        enable_audit_logging: Enable audit logging of requests/responses.
        site_title: Title displayed in the UI.
        favicon: URL or adjacent file path for the browser tab icon; empty
            string uses the built-in Drafter favicon.
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
        additional_css_files: List of stylesheet URLs, or paths to CSS files
            next to the user's program, linked into every page verbatim (no
            asset-URL remapping). Filled by `add_website_css_file()`.
        additional_js_files: List of script URLs, or paths to JavaScript
            files next to the user's program, loaded on every page verbatim.
            Filled by `add_website_js_file()`.
        additional_files: List of paths (relative to the user's program) of
            files the site needs at runtime, copied into the built site.
            Filled by `add_website_file()`.
        use_shadow_dom: Wrap app in Shadow DOM to prevent CSS conflicts.
        root_element_id: ID prefix for root element.
        system_routes: Dict mapping route names to handler callables.
        external_pages: List of external page links (URL or (URL, Text) tuples).
        newlines_to_br: Whether to convert newlines to <br> tags in text content.
        page_transition: Visual transition applied to the page body on
            navigation: "none" disables transitions, "fade" fades the new
            page in from transparent, and any CSS color (e.g. "black",
            "white", "#004488") fades the new page in from that color.
        page_transition_duration: Length of the page transition in seconds.
        button_spinners: Whether pressed buttons show a loading spinner
            (and stop accepting clicks) until their request's response is
            committed.
        browser_history: Whether Drafter navigation is mirrored into the
            browser's history stack (making the back/forward buttons time
            travel through the app). Disable for embedded instances — a
            documentation page hosting live demos wants the back button to
            leave the page, not rewind the demo, and an embedded app shares
            its host page's history and URL. configure_instance() turns
            this off automatically for multi-instance embeds.
        error_page_title: Custom heading for the built-in error page; ""
            uses the default ("Something Went Wrong").
        error_page_message: Custom friendly message for the error page; ""
            uses the category-based default summary.
        error_page_show_details: Whether the error page includes the
            technical details/traceback section (disable for deployed
            sites).
    """

    server_name: str = "MAIN_SERVER"
    in_debug_mode: bool = True
    console_mode: str = "auto"
    enable_subtle_debug_entry: bool = False
    enable_audit_logging: bool = True
    site_title: str = "Drafter Application"
    favicon: str = ""
    information: SiteInformation | None = None
    # Entries are "URL" or "URL Text"; the env var is semicolon-separated,
    # while the CLI flag is repeated once per entry
    external_pages: list[str | tuple[str, str]] | None = None
    framed: bool = True
    theme: str = "default"
    deploy_image_path: str = ""

    override_asset_url: bool | str = False
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
    additional_css_files: list[str] = field(default_factory=list)
    additional_js_files: list[str] = field(default_factory=list)
    additional_files: list[str] = field(default_factory=list)
    # Shadow DOM CSS
    use_shadow_dom: bool = False
    # Id of the DOM element the app renders into; also used as the instance
    # registry key when configure_instance() supplies no explicit instance_id
    root_element_id: str = "drafter-root--"
    # System Routes
    system_routes: dict[str, Callable | None] = field(default_factory=dict)
    # Newlines to <br> conversion
    newlines_to_br: bool = True
    # Page navigation transition: "none", "fade", or a CSS color to fade in from
    page_transition: str = "none"
    # Page transition length in seconds
    page_transition_duration: float = 0.5
    # Show a loading spinner on buttons while their request is processed
    button_spinners: bool = False
    # Mirror navigation into the browser's history stack (back/forward
    # buttons time travel); disabled for embedded instances
    browser_history: bool = True
    # Custom heading for the error page ("" uses the default)
    error_page_title: str = ""
    # Custom friendly message for the error page ("" uses the default)
    error_page_message: str = ""
    # Whether the error page includes the technical details/traceback section
    error_page_show_details: bool = True
    # TODO: Handle the system routes as configuration settings
    # TODO: Config setting to forbid external links

    @staticmethod
    def get_key() -> str:
        """Return the key identifying this configuration section.

        Returns:
            The string "client_server".
        """
        return "client_server"

    @staticmethod
    def parse_env_variables(env_vars: dict) -> dict:
        """Extract client server settings from environment variables.

        Reads the DRAFTER_-prefixed variables for the server name, debug mode,
        subtle debug entry, audit logging, site title, favicon, framing, theme, deploy
        image path, asset URL override, Shadow DOM, root element id, newline
        conversion, and the semicolon-separated lists for external pages and
        additional header/style/CSS/JS/script content.

        Args:
            env_vars: A dictionary of environment variables.

        Returns:
            A dictionary of client server configuration values that were
            present.
        """
        result = EnvVars(env_vars)
        result.get_string_if_exists("DRAFTER_SERVER_NAME", "server_name")
        result.get_bool_if_exists("DRAFTER_IN_DEBUG_MODE", "in_debug_mode")
        result.get_string_if_exists("DRAFTER_CONSOLE_MODE", "console_mode")
        result.get_bool_if_exists(
            "DRAFTER_ENABLE_SUBTLE_DEBUG_ENTRY", "enable_subtle_debug_entry"
        )
        result.get_bool_if_exists(
            "DRAFTER_ENABLE_AUDIT_LOGGING", "enable_audit_logging"
        )
        result.get_string_if_exists("DRAFTER_SITE_TITLE", "site_title")
        result.get_string_if_exists("DRAFTER_FAVICON", "favicon")
        result.get_string_if_exists("DRAFTER_FRAMED", "framed")
        result.get_string_if_exists("DRAFTER_THEME", "theme")
        result.get_string_if_exists("DRAFTER_DEPLOY_IMAGE_PATH", "deploy_image_path")
        result.get_string_list_if_exists(
            "DRAFTER_EXTERNAL_PAGES", "external_pages", ";"
        )
        result.get_string_if_exists("DRAFTER_OVERRIDE_ASSET_URL", "override_asset_url")
        result.get_string_list_if_exists(
            "DRAFTER_ADDITIONAL_HEADER_CONTENT", "additional_header_content", ";"
        )
        result.get_string_list_if_exists(
            "DRAFTER_ADDITIONAL_STYLE_CONTENT", "additional_style_content", ";"
        )
        result.get_string_list_if_exists(
            "DRAFTER_ADDITIONAL_CSS_CONTENT", "additional_css_content", ";"
        )
        result.get_string_list_if_exists(
            "DRAFTER_ADDITIONAL_JS_CONTENT", "additional_js_content", ";"
        )
        result.get_string_list_if_exists(
            "DRAFTER_ADDITIONAL_SCRIPT_CONTENT", "additional_script_content", ";"
        )
        result.get_string_list_if_exists(
            "DRAFTER_ADDITIONAL_CSS_FILES", "additional_css_files", ";"
        )
        result.get_string_list_if_exists(
            "DRAFTER_ADDITIONAL_JS_FILES", "additional_js_files", ";"
        )
        result.get_string_list_if_exists(
            "DRAFTER_ADDITIONAL_FILES", "additional_files", ";"
        )
        result.get_bool_if_exists("DRAFTER_USE_SHADOW_DOM", "use_shadow_dom")
        result.get_string_if_exists("DRAFTER_ROOT_ELEMENT_ID", "root_element_id")
        result.get_bool_if_exists("DRAFTER_NEWLINES_TO_BR", "newlines_to_br")
        result.get_string_if_exists("DRAFTER_PAGE_TRANSITION", "page_transition")
        result.get_float_if_exists(
            "DRAFTER_PAGE_TRANSITION_DURATION", "page_transition_duration"
        )
        result.get_bool_if_exists("DRAFTER_BUTTON_SPINNERS", "button_spinners")
        result.get_bool_if_exists("DRAFTER_BROWSER_HISTORY", "browser_history")
        result.get_string_if_exists("DRAFTER_ERROR_PAGE_TITLE", "error_page_title")
        result.get_string_if_exists("DRAFTER_ERROR_PAGE_MESSAGE", "error_page_message")
        result.get_bool_if_exists(
            "DRAFTER_ERROR_PAGE_SHOW_DETAILS", "error_page_show_details"
        )
        return result.as_dict()

    @staticmethod
    def extend_parser(parser):
        """Add client server arguments to the command line parser.

        Adds the "Client Server Configuration" group. Several flags are named
        for the opposite of their field: --production disables
        `in_debug_mode`, --no-frame disables `framed`, and
        --no-browser-history disables `browser_history`. Other options
        include --theme, --subtle-debug-entry, --audit-logging,
        --external-pages, the --additional-*-content options,
        --use-shadow-dom, --root-element-id, and --newlines-to-br.

        Args:
            parser: An argparse.ArgumentParser instance to extend.

        Returns:
            The "Client Server Configuration" argument group that was added.
        """
        group = parser.add_argument_group("Client Server Configuration")
        group.add_argument(
            "--server-name",
            type=str,
            help="Internal server identifier",
        )
        group.add_argument(
            "--production",
            action="store_true",
            help="Enable production mode (disables debug mode and debug panel)",
        )
        group.add_argument(
            "--console-mode",
            type=str,
            choices=["auto", "hover", "toast", "devtools"],
            help=(
                "Where captured print() output appears: 'auto' (footer "
                "console in debug mode only), 'hover' (floating console box, "
                "also in production), 'toast' (temporary corner toasts), or "
                "'devtools' (browser devtools console only)"
            ),
        )
        group.add_argument(
            "--subtle-debug-entry",
            action="store_true",
            help="Show a subtle production-only control to enter debug mode",
        )
        group.add_argument(
            "--audit-logging",
            action="store_true",
            help="Enable audit logging of requests/responses",
        )
        group.add_argument(
            "--no-frame",
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
            action="append",
            help="External page link (URL or 'URL Text' tuple); repeat the flag for multiple links",
        )
        group.add_argument(
            "--additional-header-content",
            type=str,
            action="append",
            help="HTML string for <head> section; repeat the flag for multiple entries",
        )
        group.add_argument(
            "--additional-style-content",
            type=str,
            action="append",
            help="Inline CSS string; repeat the flag for multiple entries",
        )
        group.add_argument(
            "--additional-css-content",
            type=str,
            action="append",
            help="External CSS URL; repeat the flag for multiple URLs",
        )
        group.add_argument(
            "--additional-js-content",
            type=str,
            action="append",
            help="Inline JavaScript string; repeat the flag for multiple entries",
        )
        group.add_argument(
            "--additional-script-content",
            type=str,
            action="append",
            help="External JS URL; repeat the flag for multiple URLs",
        )
        group.add_argument(
            "--additional-css-files",
            type=str,
            action="append",
            help=(
                "Stylesheet URL or CSS file next to the main file, linked into "
                "every page; repeat the flag for multiple entries"
            ),
        )
        group.add_argument(
            "--additional-js-files",
            type=str,
            action="append",
            help=(
                "Script URL or JavaScript file next to the main file, loaded on "
                "every page; repeat the flag for multiple entries"
            ),
        )
        group.add_argument(
            "--additional-files",
            type=str,
            action="append",
            help=(
                "File next to the main file that the site needs (copied into "
                "the built site); repeat the flag for multiple entries"
            ),
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
        group.add_argument(
            "--newlines-to-br",
            action="store_true",
            help="Whether to convert newlines to <br> tags in text content",
        )
        group.add_argument(
            "--page-transition",
            type=str,
            help=(
                "Visual transition on page navigation: 'none', 'fade', or a "
                "CSS color to fade the new page in from (e.g. 'black')"
            ),
        )
        group.add_argument(
            "--page-transition-duration",
            type=float,
            help="Length of the page transition in seconds",
        )
        group.add_argument(
            "--button-spinners",
            action="store_true",
            help=(
                "Show a loading spinner on buttons while their request is "
                "being processed"
            ),
        )
        group.add_argument(
            "--no-browser-history",
            action="store_true",
            help=(
                "Do not mirror navigation into the browser's history stack "
                "(the back/forward buttons then leave the page instead of "
                "moving through the app)"
            ),
        )
        group.add_argument(
            "--error-page-title",
            type=str,
            help="Custom heading shown on the error page",
        )
        group.add_argument(
            "--error-page-message",
            type=str,
            help="Custom friendly message shown on the error page",
        )
        group.add_argument(
            "--hide-error-details",
            action="store_true",
            help="Hide the technical details/traceback section on the error page",
        )
        return group

    @staticmethod
    def parse_args(parsed_args: dict) -> dict:
        """Extract client server settings from parsed command line arguments.

        Note the inversions: --production sets `in_debug_mode` to False,
        --no-frame sets `framed` to False, and --no-browser-history sets
        `browser_history` to False. Repeatable options (external pages
        and the additional content lists) arrive as lists, with each entry
        stripped of surrounding whitespace.

        Args:
            parsed_args: A dictionary of parsed command line arguments.

        Returns:
            A dictionary of client server configuration values that were
            provided.
        """
        result = {}
        if parsed_args.get("server_name"):
            result["server_name"] = parsed_args["server_name"]
        if parsed_args.get("production"):
            result["in_debug_mode"] = False
        if parsed_args.get("console_mode"):
            result["console_mode"] = parsed_args["console_mode"]
        if parsed_args.get("subtle_debug_entry"):
            result["enable_subtle_debug_entry"] = True
        if parsed_args.get("audit_logging"):
            result["enable_audit_logging"] = True
        if parsed_args.get("site_title"):
            result["site_title"] = parsed_args["site_title"]
        if parsed_args.get("favicon"):
            result["favicon"] = parsed_args["favicon"]
        if parsed_args.get("no_frame"):
            result["framed"] = False
        if parsed_args.get("theme"):
            result["theme"] = parsed_args["theme"]
        if parsed_args.get("deploy_image_path"):
            result["deploy_image_path"] = parsed_args["deploy_image_path"]
        if parsed_args.get("external_pages"):
            result["external_pages"] = [
                page.strip() for page in parsed_args["external_pages"]
            ]
        if parsed_args.get("override_asset_url"):
            result["override_asset_url"] = parsed_args["override_asset_url"]
        if parsed_args.get("additional_header_content"):
            result["additional_header_content"] = [
                content.strip() for content in parsed_args["additional_header_content"]
            ]
        if parsed_args.get("additional_style_content"):
            result["additional_style_content"] = [
                content.strip() for content in parsed_args["additional_style_content"]
            ]
        if parsed_args.get("additional_css_content"):
            result["additional_css_content"] = [
                content.strip() for content in parsed_args["additional_css_content"]
            ]
        if parsed_args.get("additional_js_content"):
            result["additional_js_content"] = [
                content.strip() for content in parsed_args["additional_js_content"]
            ]
        if parsed_args.get("additional_script_content"):
            result["additional_script_content"] = [
                content.strip() for content in parsed_args["additional_script_content"]
            ]
        for files_key in (
            "additional_css_files",
            "additional_js_files",
            "additional_files",
        ):
            if parsed_args.get(files_key):
                result[files_key] = [
                    content.strip() for content in parsed_args[files_key]
                ]
        if parsed_args.get("use_shadow_dom"):
            result["use_shadow_dom"] = True
        if parsed_args.get("root_element_id"):
            result["root_element_id"] = parsed_args["root_element_id"]
        if parsed_args.get("newlines_to_br"):
            result["newlines_to_br"] = True
        if parsed_args.get("page_transition"):
            result["page_transition"] = parsed_args["page_transition"]
        if parsed_args.get("page_transition_duration") is not None:
            result["page_transition_duration"] = parsed_args["page_transition_duration"]
        if parsed_args.get("button_spinners"):
            result["button_spinners"] = True
        if parsed_args.get("no_browser_history"):
            result["browser_history"] = False
        if parsed_args.get("error_page_title"):
            result["error_page_title"] = parsed_args["error_page_title"]
        if parsed_args.get("error_page_message"):
            result["error_page_message"] = parsed_args["error_page_message"]
        if parsed_args.get("hide_error_details"):
            result["error_page_show_details"] = False
        return result

    def to_json(self) -> dict:
        """Serialize this configuration to a JSON-serializable dictionary.

        Unlike the base implementation, this handles fields that are not
        directly serializable: `information` becomes its `to_json` dictionary
        (or None), and `system_routes` is reduced to a list of route names,
        since the handler callables cannot be serialized.

        Returns:
            A dictionary representation of this configuration.
        """
        return {
            "server_name": self.server_name,
            "in_debug_mode": self.in_debug_mode,
            "console_mode": self.console_mode,
            "enable_subtle_debug_entry": self.enable_subtle_debug_entry,
            "enable_audit_logging": self.enable_audit_logging,
            "site_title": self.site_title,
            "favicon": self.favicon,
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
            "additional_css_files": self.additional_css_files,
            "additional_js_files": self.additional_js_files,
            "additional_files": self.additional_files,
            "use_shadow_dom": self.use_shadow_dom,
            "root_element_id": self.root_element_id,
            "system_routes": list(self.system_routes.keys()),
            "external_pages": self.external_pages,
            "newlines_to_br": self.newlines_to_br,
            "page_transition": self.page_transition,
            "page_transition_duration": self.page_transition_duration,
            "button_spinners": self.button_spinners,
            "browser_history": self.browser_history,
            "error_page_title": self.error_page_title,
            "error_page_message": self.error_page_message,
            "error_page_show_details": self.error_page_show_details,
        }

    def copy(self) -> "ClientServerConfiguration":
        """
        Creates a copy of the current configuration instance.

        Returns:
            ClientServerConfiguration: A new instance of ClientServerConfiguration with the same values.
        """
        return ClientServerConfiguration(
            in_debug_mode=self.in_debug_mode,
            console_mode=self.console_mode,
            enable_subtle_debug_entry=self.enable_subtle_debug_entry,
            enable_audit_logging=self.enable_audit_logging,
            site_title=self.site_title,
            favicon=self.favicon,
            information=self.information.copy() if self.information else None,
            framed=self.framed,
            theme=self.theme,
            deploy_image_path=self.deploy_image_path,
            additional_header_content=list(self.additional_header_content),
            additional_style_content=list(self.additional_style_content),
            additional_css_content=list(self.additional_css_content),
            additional_js_content=list(self.additional_js_content),
            additional_script_content=list(self.additional_script_content),
            additional_css_files=list(self.additional_css_files),
            additional_js_files=list(self.additional_js_files),
            additional_files=list(self.additional_files),
            use_shadow_dom=self.use_shadow_dom,
            server_name=self.server_name,
            root_element_id=self.root_element_id,
            system_routes=dict(self.system_routes),
            override_asset_url=self.override_asset_url,
            external_pages=list(self.external_pages) if self.external_pages else None,
            newlines_to_br=self.newlines_to_br,
            page_transition=self.page_transition,
            page_transition_duration=self.page_transition_duration,
            button_spinners=self.button_spinners,
            browser_history=self.browser_history,
            error_page_title=self.error_page_title,
            error_page_message=self.error_page_message,
            error_page_show_details=self.error_page_show_details,
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

    #: Configuration keys whose values are lists that `update_configuration`
    #: appends to (rather than replaces). Each Drafter instance resets these
    #: to empty lists before its code runs (see `configure_instance`).
    LIST_CONTENT_KEYS = (
        "additional_css_content",
        "additional_style_content",
        "additional_js_content",
        "additional_script_content",
        "additional_header_content",
        "additional_css_files",
        "additional_js_files",
        "additional_files",
    )

    def update_configuration(self, key: str, value):
        """
        Updates a specific configuration key with a new value.

        List-valued content keys (e.g., `additional_css_content`) have the
        value appended rather than replaced; site-information keys are set on
        the `information` object (created if needed); everything else is
        assigned directly.

        Args:
            key: The configuration key to update (e.g., 'theme', 'in_debug_mode').
            value: The new value to assign (or append, for list-valued keys).

        Raises:
            ValueError: If the key is not a known configuration attribute or
                site-information key, or if a content key's current value is
                not a list.
        """
        if not hasattr(self, key) and key not in self.SITE_INFORMATION_KEYS:
            # TODO: InvalidConfigurationKeyError
            raise ValueError(f"Invalid configuration key: {key}")
        # TODO: Add validation for specific keys if necessary (e.g., theme should be a valid theme name)
        if key in self.LIST_CONTENT_KEYS:
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
