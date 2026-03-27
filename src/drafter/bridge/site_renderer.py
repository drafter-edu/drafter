import json
import time
import html
from dataclasses import dataclass, field
from typing import Callable, Optional, Any

from drafter.site.initial_site_data import InitialSiteData
from drafter.data.channel import DEFAULT_CHANNEL_AFTER, DEFAULT_CHANNEL_BEFORE, Channel
from drafter.data.response import Response
from drafter.data.request import Request
from drafter.bridge.runtime import RuntimeAdapter, create_runtime
from drafter.bridge.log import debug_log, console_log
from drafter.site.site import (
    DRAFTER_TAG_IDS,
    DRAFTER_TAG_CLASSES,
    SITE_HTML_SHADOW_DOM_TEMPLATE,
)

import js
from drafter.bridge.dom import (
    document,
    add_js,
    add_style,
    add_link,
    add_link_to_shadow,
    add_style_to_shadow,
    add_header,
    remove_page_content,
    remove_existing_theme,
    replace_html,
    get_attribute_recursively,
    swap_debug_mode,
)

class SiteRenderer:
    """
    Handles all aspects of updating and rendering the DOM.
    Does not handle event handling or navigation logic.
    """
    
    root_id: str
    true_root_id: str
    runtime: RuntimeAdapter
    channel_history: dict[str, set[str]] = field(default_factory=dict)
    debug_panel: Optional[Any] = None
    
    def __init__(self, runtime, root_id, true_root_id, debug_panel=None):
        self.runtime = runtime
        self.root_id = root_id
        self.true_root_id = true_root_id
        self.debug_panel = debug_panel
        self.channel_history = {}
        
    ### Accessors

    def get_root(self):
        # TODO: Handle this correctly for shadowdom
        return document.getElementById(self.root_id)

    ### Site
    
    def _setup_error_site(self, initial_site_data: InitialSiteData) -> None:
        console_log("Error in initial site data: " + repr(initial_site_data))
        true_root = document.getElementById(self.true_root_id)
        true_root.innerHTML = initial_site_data.site_html
        return None

    def setup(self, initial_site_data: InitialSiteData) -> None:
        if initial_site_data.error:
            return self._setup_error_site(initial_site_data)

        try:
            true_root = document.getElementById(self.true_root_id)
            remove_existing_theme(true_root, DRAFTER_TAG_CLASSES["THEME"])
            remove_existing_theme(true_root, DRAFTER_TAG_CLASSES["PRECOMPILE_HEADERS"])

            if initial_site_data.use_shadow_dom:
                true_root.innerHTML = SITE_HTML_SHADOW_DOM_TEMPLATE
                shadow_host = document.getElementById(DRAFTER_TAG_IDS["SHADOW_HOST"])
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
                    classes = (
                        f"{DRAFTER_TAG_CLASSES['THEME']} {css_classes}".strip()
                    )
                    add_link_to_shadow(shadow_root, css_url, with_class=classes)
                for style in initial_site_data.additional_style:
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
                    classes = (
                        f"{DRAFTER_TAG_CLASSES['THEME']} {css_classes}".strip()
                    )
                    add_link(root, css_url, with_class=classes)
                for style in initial_site_data.additional_style:
                    add_style(root, style, with_class=DRAFTER_TAG_CLASSES["THEME"])

            for js_code in initial_site_data.additional_js:
                add_js(root, js_code, with_class=DRAFTER_TAG_CLASSES["THEME"])
            for header in initial_site_data.additional_header:
                add_header(root, header)

            if not initial_site_data.framed:
                self.toggle_frame()

        except Exception as e:
            console_log(f"Error setting up site: {e}")
            raise e
        
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

            elements = js.document.querySelectorAll(selector)

            if not elements:
                # TODO: Handle this more gracefully
                raise RuntimeError("Target element not found in document.")

            elements.forEach(
                lambda element, index, array: replace_html(
                    element,
                    body,
                    response.target.replace if response.target else False,
                )
            )

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
        self.add_channel_content(response.channels.get(DEFAULT_CHANNEL_BEFORE), is_page_specific=True)
    
    def apply_after_channel(self, response: Response) -> None:
        self.add_channel_content(response.channels.get(DEFAULT_CHANNEL_AFTER), is_page_specific=True)

    def add_channel_content(
        self, channel: Optional[Channel], is_page_specific: bool = False
    ) -> None:
        """
        Processes messages from a channel and adds them to the page.
        Supports 'script' and 'style' message kinds.

        Args:
            channel: The channel containing messages to process.
            is_page_specific: If True, marks content as page-specific (will be removed on navigation).
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
                if message.kind == "script":
                    # TODO: Handle errors while executing this script
                    add_js(root, message.content, is_page_specific=is_page_specific)
                elif message.kind == "style":
                    # TODO: Need to look up whether we are using the shadow dom or not
                    add_style(
                        root,
                        message.content,
                        is_page_specific=is_page_specific,
                    )
                    
    ### Frame
                    
    def toggle_frame(self) -> None:
        FRAME_PIECES = ",".join(
            f".{DRAFTER_TAG_IDS[key]}"
            for key in ["PADDING_V", "PADDING_H", "HEADER", "FOOTER"]
        )
        frames = js.document.querySelectorAll(FRAME_PIECES)
        if frames:
            for frame in frames:
                frame.classList.toggle("drafter-hidden--")
        body = js.document.querySelector("." + DRAFTER_TAG_IDS["BODY"])
        if body:
            body.classList.toggle("drafter-body-frame-hidden--")