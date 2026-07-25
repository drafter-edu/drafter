"""
Rendering of the site's DOM for a single client instance.

The SiteRenderer builds the initial site (optionally inside a shadow root),
applies response bodies to their targets while parking/restoring persistent
components, injects channel content (scripts and styles), and manages the
site frame — all scoped to the instance's own document and root so multiple
concurrent instances never collide.
"""

from typing import Any

from drafter.bridge.dom import (
    add_header,
    add_js,
    add_link,
    add_link_to_shadow,
    add_style,
    add_style_to_shadow,
    insert_html_before,
    remove_existing_theme,
    remove_page_content,
    replace_html,
    reuse_theme_link_prefix,
)
from drafter.bridge.error_handling import (
    raise_bridge_system_error,
    report_bridge_error,
    report_bridge_warning,
)
from drafter.bridge.log import debug_log
from drafter.bridge.persistence import (
    apply_persistence,
    park_persistent_components,
)
from drafter.bridge.runtime import RuntimeAdapter
from drafter.data.channel import DEFAULT_CHANNEL_AFTER, DEFAULT_CHANNEL_BEFORE, Channel
from drafter.data.response import Response
from drafter.site.initial_site_data import InitialSiteData
from drafter.site.site import (
    DRAFTER_TAG_CLASSES,
    DRAFTER_TAG_IDS,
    SITE_HTML_SHADOW_DOM_TEMPLATE,
)

PAGE_TRANSITION_FADE_CLASS = "drafter-page-transition-fade--"
"""Class that fades the page body in from transparent (see drafter_base.css)."""
PAGE_TRANSITION_VEIL_CLASS = "drafter-page-transition-veil--"
"""Class that fades the page body in from a solid color veil."""


class SiteRenderer:
    """
    Handles all aspects of updating and rendering the DOM.
    Does not handle event handling or navigation logic.
    """

    root_id: str
    true_root_id: str
    runtime: RuntimeAdapter
    channel_history: dict[str, set[str]]
    debug_panel: Any | None = None

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
        """The root node for content injection; alias for get_scope."""
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
        """Build the initial site DOM inside this instance's root element.

        If the initial site data carries an error, renders the fallback
        error site instead. Otherwise, clears any previously-injected theme
        assets, inserts the site HTML — inside a freshly attached shadow
        root when shadow DOM is enabled, directly into the root element
        otherwise — injects the additional CSS, styles, JS, and headers,
        records the resulting node as the scope for all later inner-frame
        lookups, and hides the frame if the site is configured unframed.

        Args:
            initial_site_data: The rendered initial site (HTML, assets, and
                flags) produced by the server's render phase.

        Raises:
            RuntimeError: If constructing the site container fails for any
                reason (raised via raise_bridge_system_error after the
                failure is reported through telemetry).
        """
        if initial_site_data.error:
            return self._setup_error_site(initial_site_data)

        self.use_shadow_dom = initial_site_data.use_shadow_dom

        try:
            true_root = self.document.getElementById(self.true_root_id)
            remove_existing_theme(true_root, DRAFTER_TAG_CLASSES["PRECOMPILE_HEADERS"])

            # The stylesheet links this render needs, as (url, class attribute)
            # pairs in cascade order. Where a previous run of this instance
            # left links connected, the matching prefix is reused in place
            # instead of recreated: a link that never leaves the DOM never
            # refetches its CSS (dev servers often serve it uncacheable).
            wanted_css = self._as_wanted_css(initial_site_data.additional_css)

            reused_links = 0
            if initial_site_data.use_shadow_dom:
                # Head-level theme links can only be left over from a previous
                # non-shadow run of this instance; this never touches links
                # scoped inside the shadow root.
                remove_existing_theme(true_root, DRAFTER_TAG_CLASSES["THEME"])

                shadow_root = self._find_existing_shadow_root(true_root)
                if shadow_root is None:
                    true_root.innerHTML = SITE_HTML_SHADOW_DOM_TEMPLATE
                    # Scope to this instance's root: the shadow-host id is shared, so a
                    # global getElementById would return the first instance's host.
                    shadow_host = true_root.querySelector(
                        "#" + DRAFTER_TAG_IDS["SHADOW_HOST"]
                    )
                    if not shadow_host:
                        raise ValueError(
                            "Shadow host element not found in the document."
                        )
                    shadow_root = shadow_host.attachShadow({"mode": "open"})
                    shadow_root.innerHTML = initial_site_data.site_html
                else:
                    reused_links = self._rebuild_shadow_content(
                        shadow_root, initial_site_data.site_html, wanted_css
                    )
                root = shadow_root

                for css_url, classes in wanted_css[reused_links:]:
                    add_link_to_shadow(shadow_root, css_url, with_class=classes)
                for style in initial_site_data.additional_style:
                    add_style_to_shadow(
                        shadow_root, style, with_class=DRAFTER_TAG_CLASSES["THEME"]
                    )
            else:
                # Reuse the head's still-wanted theme links across runs,
                # removing only theme scripts and the stale link tail.
                existing_links = list(
                    self.document.querySelectorAll(
                        f"link.{DRAFTER_TAG_CLASSES['THEME']}"
                    )
                )
                remove_existing_theme(
                    true_root, DRAFTER_TAG_CLASSES["THEME"], scripts_only=True
                )
                reused_links = reuse_theme_link_prefix(existing_links, wanted_css)

                true_root.innerHTML = initial_site_data.site_html
                root = true_root

                for css_url, classes in wanted_css[reused_links:]:
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

    def _as_wanted_css(self, additional_css) -> list:
        """Normalize CSS assets to (url, class attribute) pairs in cascade
        order, tagging each with the shared theme class.

        Args:
            additional_css: CSSLink objects (or bare URL strings) from an
                InitialSiteData.

        Returns:
            A list of (url, class attribute value) tuples.
        """
        wanted_css = []
        for css in additional_css:
            css_url = css.url if hasattr(css, "url") else css
            css_classes = " ".join(css.classes) if hasattr(css, "classes") else ""
            wanted_css.append(
                (css_url, f"{DRAFTER_TAG_CLASSES['THEME']} {css_classes}".strip())
            )
        return wanted_css

    def refresh_theme_css(self, additional_css) -> None:
        """Swap the connected stylesheet links to match a new CSS list.

        Runtime companion to the CSS portion of setup(), used when the
        theme changes mid-run (debug menu "Switch Theme" or a student's
        set_website_theme call): the still-matching prefix of connected
        links stays untouched (no refetch, no flash), the stale tail is
        removed, and the remaining wanted links are created in cascade
        order. The page body is never rebuilt.

        Args:
            additional_css: The new CSSLink list, as produced by
                Site.render() with the updated configuration.
        """
        if self.scope is None:
            return
        wanted_css = self._as_wanted_css(additional_css)
        theme_class = DRAFTER_TAG_CLASSES["THEME"]
        if self.use_shadow_dom:
            existing_links = list(
                self.scope.querySelectorAll(f"link.{theme_class}")
            )
            reused_links = reuse_theme_link_prefix(existing_links, wanted_css)
            for css_url, classes in wanted_css[reused_links:]:
                add_link_to_shadow(self.scope, css_url, with_class=classes)
        else:
            existing_links = list(
                self.document.querySelectorAll(f"link.{theme_class}")
            )
            reused_links = reuse_theme_link_prefix(existing_links, wanted_css)
            for css_url, classes in wanted_css[reused_links:]:
                add_link(self.scope, css_url, with_class=classes)

    def _find_existing_shadow_root(self, true_root):
        """The shadow root left behind by a previous run of this instance.

        Every run builds a fresh SiteRenderer, so reuse detection must be
        DOM-based: a surviving shadow host inside the root element means the
        previous run rendered here with shadow DOM enabled.

        Args:
            true_root: This instance's root element (may be None).

        Returns:
            The previous run's shadow root, or None if there is nothing to
            reuse (first run, prior error site, or prior non-shadow run).
        """
        if true_root is None:
            return None
        shadow_host = true_root.querySelector("#" + DRAFTER_TAG_IDS["SHADOW_HOST"])
        if not shadow_host:
            return None
        shadow_root = getattr(shadow_host, "shadowRoot", None)
        return shadow_root if shadow_root else None

    def _rebuild_shadow_content(self, shadow_root, site_html, wanted_css) -> int:
        """Replace a surviving shadow root's content, reusing its theme links.

        The still-wanted prefix of stylesheet <link> elements stays connected
        while everything else (old site frame, injected styles, stale links)
        is removed, and the new site HTML is inserted before the kept links.
        Keeping the links connected avoids refetching their CSS on every
        editor-driven restart (and the flash of unstyled content that comes
        with it).

        Args:
            shadow_root: The previous run's shadow root to render into.
            site_html: The new site frame HTML.
            wanted_css: (url, class attribute) pairs in cascade order.

        Returns:
            The number of links reused; the caller creates the rest.
        """
        theme_class = DRAFTER_TAG_CLASSES["THEME"]
        existing_links = list(shadow_root.querySelectorAll(f"link.{theme_class}"))
        reused_links = reuse_theme_link_prefix(existing_links, wanted_css)
        kept_links = existing_links[:reused_links]

        for child in list(shadow_root.children):
            tag = (getattr(child, "tagName", "") or "").lower()
            if tag == "link" and child.classList.contains(theme_class):
                continue
            child.remove()
        insert_html_before(
            shadow_root, site_html, kept_links[0] if kept_links else None
        )
        return reused_links

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

    def apply_page_transition(self, transition: str, duration: float) -> None:
        """Play the configured navigation transition on the page body.

        Restarts a CSS animation on the (persistent) body container after
        its children have been swapped: "fade" fades the new page in from
        transparent, while any other non-"none" value is treated as a CSS
        color the new page fades in from (via an overlay veil). The
        animation classes and keyframes live in drafter_base.css; failures
        are reported but never block navigation.

        Args:
            transition: "none" (or empty) to do nothing, "fade", or a CSS
                color such as "black" or "#004488".
            duration: Animation length in seconds.
        """
        if not transition or transition == "none":
            return
        scope = self.get_scope()
        if scope is None:
            return
        element = scope.querySelector("#" + DRAFTER_TAG_IDS["BODY"])
        if element is None:
            return
        try:
            element.classList.remove(
                PAGE_TRANSITION_FADE_CLASS, PAGE_TRANSITION_VEIL_CLASS
            )
            # The body container survives navigation (only its children are
            # replaced), so the animation must be restarted: reading
            # offsetWidth forces a reflow between removing and re-adding the
            # class.
            getattr(element, "offsetWidth", None)
            element.style.setProperty(
                "--drafter-page-transition-duration", f"{duration}s"
            )
            if transition == "fade":
                element.classList.add(PAGE_TRANSITION_FADE_CLASS)
            else:
                element.style.setProperty("--drafter-page-transition-color", transition)
                element.classList.add(PAGE_TRANSITION_VEIL_CLASS)
        except Exception as e:
            report_bridge_error(
                "client.page_transition_failed",
                "Failed to apply the page transition",
                "bridge.site_renderer.apply_page_transition",
                f"Transition: {transition!r}; duration: {duration!r}",
                exception=e,
                phase="navigation",
            )

    ### Channel Content

    def remove_page_specific_content(self) -> None:
        """
        Removes CSS and JS that were added for the previous page.
        This ensures that page-specific styles/scripts don't persist across navigation.
        """
        remove_page_content(self.get_root())

    def apply_before_channel(self, response: Response) -> None:
        """Apply the response's default "before" channel as page-specific
        content (intended to run before the body update).

        Args:
            response: The response whose "before" channel, if any, should
                be applied.
        """
        self.add_channel_content(
            response.channels.get(DEFAULT_CHANNEL_BEFORE),
            is_page_specific=True,
            response=response,
        )

    def apply_after_channel(self, response: Response) -> None:
        """Apply the response's default "after" channel as page-specific
        content (intended to run after the body update).

        Args:
            response: The response whose "after" channel, if any, should
                be applied.
        """
        self.add_channel_content(
            response.channels.get(DEFAULT_CHANNEL_AFTER),
            is_page_specific=True,
            response=response,
        )

    def add_channel_content(
        self,
        channel: Channel | None,
        is_page_specific: bool = False,
        response: Response | None = None,
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
        """Toggle visibility of the site frame within this instance's scope.

        Flips the hidden class on the frame pieces (vertical/horizontal
        padding, header, and footer) and flips the frame-hidden class on the
        body element, so the body can restyle itself when the frame is
        absent.
        """
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
