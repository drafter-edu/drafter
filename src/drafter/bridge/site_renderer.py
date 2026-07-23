from typing import Optional, Any

from drafter.site.initial_site_data import InitialSiteData
from drafter.data.channel import DEFAULT_CHANNEL_AFTER, DEFAULT_CHANNEL_BEFORE, Channel
from drafter.data.response import Response
from drafter.bridge.runtime import RuntimeAdapter
from drafter.bridge.log import debug_log
from drafter.bridge.error_handling import (
    raise_bridge_system_error,
    report_bridge_error,
    report_bridge_warning,
)
from drafter.site.site import (
    DRAFTER_TAG_IDS,
    DRAFTER_TAG_CLASSES,
    SITE_HTML_SHADOW_DOM_TEMPLATE,
)

import js
from drafter.bridge.dom import (
    add_js,
    add_style,
    add_link,
    add_link_to_shadow,
    add_style_to_shadow,
    add_header,
    remove_page_content,
    remove_existing_theme,
    replace_html,
)
from drafter.bridge.persistence import (
    apply_persistence,
    park_persistent_components,
)


class SiteRenderer:
    """
    Handles all aspects of updating and rendering the DOM.
    Does not handle event handling or navigation logic.
    """

    root_id: str
    true_root_id: str
    runtime: RuntimeAdapter
    channel_history: dict[str, set[str]]
    debug_panel: Optional[Any] = None

    def __init__(self, runtime, root_id, true_root_id, debug_panel=None):
        self.runtime = runtime
        self.root_id = root_id
        self.true_root_id = true_root_id
        self.debug_panel = debug_panel
        self.channel_history = {}
        # The document this instance renders into: an iframe's document for
        # embedded instances, otherwise the global one. All root lookups must
        # go through it so instances in different documents never collide.
        self.document = runtime.context.document
        # The DOM node all inner-frame lookups are scoped to: the shadow root
        # when shadow DOM is enabled, otherwise the root element. Set during
        # setup(). Scoping here (instead of the global document) is what lets
        # multiple concurrent instances coexist without ID collisions.
        self.scope = None
        # Whether this instance renders inside a shadow root. Controls whether
        # runtime-injected CSS is scoped to the shadow root or the global head.
        self.use_shadow_dom = False

    ### Accessors

    def get_scope(self):
        """The node to scope inner-frame DOM queries to (shadow root or root)."""
        if self.scope is not None:
            return self.scope
        return self.document.getElementById(self.root_id)

    def get_root(self):
        return self.get_scope()

    def get_parking_area(self):
        """The hidden footer area that holds persisted components, or None."""
        scope = self.get_scope()
        if scope is None:
            return None
        return scope.querySelector("#" + DRAFTER_TAG_IDS["PERSIST"])

    ### Site

    def _setup_error_site(self, initial_site_data: InitialSiteData) -> None:
        report_bridge_warning(
            "bridge.error_site_rendered",
            "Initial site data contained an error; rendering fallback error site",
            "bridge.site_renderer._setup_error_site",
            f"InitialSiteData: {repr(initial_site_data)}",
            phase="setup",
        )
        true_root = self.document.getElementById(self.true_root_id)
        true_root.innerHTML = initial_site_data.site_html
        self.scope = true_root
        return None

    def setup(self, initial_site_data: InitialSiteData) -> None:
        if initial_site_data.error:
            return self._setup_error_site(initial_site_data)

        self.use_shadow_dom = initial_site_data.use_shadow_dom

        try:
            true_root = self.document.getElementById(self.true_root_id)
            remove_existing_theme(true_root, DRAFTER_TAG_CLASSES["THEME"])
            remove_existing_theme(true_root, DRAFTER_TAG_CLASSES["PRECOMPILE_HEADERS"])

            if initial_site_data.use_shadow_dom:
                true_root.innerHTML = SITE_HTML_SHADOW_DOM_TEMPLATE
                # Scope to this instance's root: the shadow-host id is shared, so a
                # global getElementById would return the first instance's host.
                shadow_host = true_root.querySelector(
                    "#" + DRAFTER_TAG_IDS["SHADOW_HOST"]
                )
                if not shadow_host:
                    raise ValueError("Shadow host element not found in the document.")
                shadow_root = shadow_host.attachShadow({"mode": "open"})
                shadow_root.innerHTML = initial_site_data.site_html
                root = shadow_root

                for css in initial_site_data.additional_css:
                    css_url = css.url if hasattr(css, "url") else css
                    css_classes = (
                        " ".join(css.classes) if hasattr(css, "classes") else ""
                    )
                    classes = f"{DRAFTER_TAG_CLASSES['THEME']} {css_classes}".strip()
                    add_link_to_shadow(shadow_root, css_url, with_class=classes)
                for style in initial_site_data.additional_style:
                    js.console.log("Adding", style, shadow_root)
                    add_style_to_shadow(
                        shadow_root, style, with_class=DRAFTER_TAG_CLASSES["THEME"]
                    )
            else:
                true_root.innerHTML = initial_site_data.site_html
                root = true_root

                for css in initial_site_data.additional_css:
                    css_url = css.url if hasattr(css, "url") else css
                    css_classes = (
                        " ".join(css.classes) if hasattr(css, "classes") else ""
                    )
                    classes = f"{DRAFTER_TAG_CLASSES['THEME']} {css_classes}".strip()
                    add_link(root, css_url, with_class=classes)
                for style in initial_site_data.additional_style:
                    add_style(root, style, with_class=DRAFTER_TAG_CLASSES["THEME"])

            for js_code in initial_site_data.additional_js:
                add_js(root, js_code, with_class=DRAFTER_TAG_CLASSES["THEME"])
            for header in initial_site_data.additional_header:
                add_header(root, header)

            # Remember the scope (shadow root or root element) for all later
            # inner-frame lookups.
            self.scope = root

            if not initial_site_data.framed:
                self.toggle_frame()

        except Exception as e:
            raise_bridge_system_error(
                "client.site_setup_failed",
                "Failed to set up site container",
                "bridge.site_renderer.setup",
                f"InitialSiteData: {repr(initial_site_data)}",
                exception=e,
                phase="setup",
            )

    def update_site(self, response: Response) -> bool:
        """
        Updates the DOM based on the response from the server.
        If the DOM updated, returns True (indicating that events should be re-registered).
        """
        # Replace the body
        body = response.body
        if body is not None:
            # Convert target to CSS selector
            if response.target:
                selector = response.target.to_selector()
            else:
                selector = f"#{DRAFTER_TAG_IDS['BODY']}"

            elements = self.get_scope().querySelectorAll(selector)

            if not elements:
                raise_bridge_system_error(
                    "client.update_site_target_missing",
                    "Target element not found while applying response body",
                    "bridge.site_renderer.update_site",
                    f"Selector: {selector}; response_url: {response.url}",
                    route=response.url,
                    request_id=response.request_id,
                    response_id=response.id,
                    phase="navigation",
                )

            parking_area = self.get_parking_area()
            for element in list(elements):
                # Move persistent components (background music, running
                # timers) out of the subtree before it is destroyed.
                if parking_area is not None:
                    park_persistent_components(element, parking_area)
                replace_html(
                    element,
                    body,
                    response.target.replace if response.target else False,
                )
            # Swap parked components back in place of their freshly-rendered
            # counterparts (and process any eviction markers).
            if parking_area is not None:
                apply_persistence(self.get_scope(), parking_area)

            debug_log("client.update_site_complete", response)
            # TODO: Shouldn't it be detecting the specific targets that were updated?
            if not response.target or response.target.id == DRAFTER_TAG_IDS["BODY"]:
                return True

        return False

    ### Channel Content

    def remove_page_specific_content(self) -> None:
        """
        Removes CSS and JS that were added for the previous page.
        This ensures that page-specific styles/scripts don't persist across navigation.
        """
        remove_page_content(self.get_root())

    def apply_before_channel(self, response: Response) -> None:
        self.add_channel_content(
            response.channels.get(DEFAULT_CHANNEL_BEFORE),
            is_page_specific=True,
            response=response,
        )

    def apply_after_channel(self, response: Response) -> None:
        self.add_channel_content(
            response.channels.get(DEFAULT_CHANNEL_AFTER),
            is_page_specific=True,
            response=response,
        )

    def add_channel_content(
        self,
        channel: Optional[Channel],
        is_page_specific: bool = False,
        response: Optional[Response] = None,
    ) -> None:
        """
        Processes messages from a channel and adds them to the page.
        Supports 'script' and 'style' message kinds.

        Failures applying an individual message are reported through
        structured telemetry (phase ``channel_execution``) and do not stop
        the remaining messages from being applied.

        Args:
            channel: The channel containing messages to process.
            is_page_specific: If True, marks content as page-specific (will be removed on navigation).
            response: The response the channel belongs to (for correlation).
        """
        if channel:
            root = self.get_root()
            for message in channel.messages:
                if message.sigil is not None:
                    if channel.name not in self.channel_history:
                        self.channel_history[channel.name] = set()
                    if message.sigil in self.channel_history[channel.name]:
                        continue
                    self.channel_history[channel.name].add(message.sigil)
                try:
                    if message.kind == "script":
                        add_js(root, message.content, is_page_specific=is_page_specific)
                    elif message.kind == "style":
                        # Scope runtime CSS to this instance's shadow root so it
                        # doesn't leak into other instances via the global head.
                        if self.use_shadow_dom:
                            add_style_to_shadow(
                                root,
                                message.content,
                                is_page_specific=is_page_specific,
                            )
                        else:
                            add_style(
                                root,
                                message.content,
                                is_page_specific=is_page_specific,
                            )
                except Exception as e:
                    report_bridge_error(
                        "bridge.channel_message_failed",
                        f"Failed to apply {message.kind} message from channel '{channel.name}'",
                        "bridge.site_renderer.add_channel_content",
                        f"Message content: {message.content!r}",
                        exception=e,
                        route=response.url if response else None,
                        request_id=response.request_id if response else None,
                        response_id=response.id if response else None,
                        phase="channel_execution",
                    )

    ### Frame

    def toggle_frame(self) -> None:
        FRAME_PIECES = ",".join(
            f".{DRAFTER_TAG_IDS[key]}"
            for key in ["PADDING_V", "PADDING_H", "HEADER", "FOOTER"]
        )
        scope = self.get_scope()
        frames = scope.querySelectorAll(FRAME_PIECES)
        if frames:
            for frame in frames:
                frame.classList.toggle("drafter-hidden--")
        body = scope.querySelector("." + DRAFTER_TAG_IDS["BODY"])
        if body:
            body.classList.toggle("drafter-body-frame-hidden--")
