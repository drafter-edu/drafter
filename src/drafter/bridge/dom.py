"""
DOM manipulation helpers for the bridge module.
Functions for adding/removing scripts, styles, links, and other DOM elements.
"""

from drafter.site.site import (
    DRAFTER_TAG_CLASSES,
    DRAFTER_TAG_IDS,
    GLOBAL_DRAFTER_CSS_PATHS,
)
from drafter.helpers.utils import is_skulpt, is_pyodide
from typing import Any
import js

ATTR_PAGE_SPECIFIC = "data-drafter-page-specific"


def get_document(node: Any) -> Any:
    """The document owning a node (element or shadow root).

    Instances may render into an iframe's document rather than the global one,
    so DOM helpers must always resolve the document from the node they operate
    on instead of capturing the global ``js.document``.
    """
    doc = getattr(node, "ownerDocument", None) if node is not None else None
    return doc if doc is not None else js.document


def get_window(node: Any) -> Any:
    """The window owning a node, falling back to the global scope."""
    view = getattr(get_document(node), "defaultView", None)
    return view if view is not None else js


def replace_html(tag: Any, html_content: str, is_fragment: bool = False) -> None:
    """Replace the contents or the tag itself with new HTML."""
    window = get_window(tag)
    scroll_top = window.scrollY
    scroll_left = window.scrollX

    try:
        r = get_document(tag).createRange()
        r.selectNode(tag)
        fragment = r.createContextualFragment(html_content)

        if not is_fragment:
            tag.replaceChildren(fragment)
            return

        parent = tag.parentNode
        if parent is None:
            tag.replaceChildren(fragment)
            return

        new_nodes = list(fragment.childNodes)

        if len(new_nodes) == 0:
            parent.removeChild(tag)
        elif len(new_nodes) == 1:
            parent.replaceChild(new_nodes[0], tag)
        else:
            for node in new_nodes:
                parent.insertBefore(node, tag)
            parent.removeChild(tag)

    finally:
        window.scrollTo(scroll_left, scroll_top)


def get_attribute_recursively(element: Any, attribute_name: str) -> list[str]:
    current_element = element
    attributes = []
    while current_element:
        if current_element.hasAttribute(attribute_name):
            attributes.append(current_element.getAttribute(attribute_name))
        current_element = current_element.parentElement
    return attributes


def add_js(
    root, src: str, is_page_specific: bool = False, with_class: str = ""
) -> None:
    """Create a script element, execute it, and detach it from the document.

    The script element is appended to the document head (which runs the
    JavaScript immediately) and then removed right away, so the source does
    not accumulate in the DOM across renders.

    Args:
        root: Node used to resolve the owning document (may be inside an
            iframe rather than the top page).
        src: JavaScript source code to execute.
        is_page_specific: Whether to mark the element as page-specific so it
            would be cleaned up on navigation.
        with_class: Optional class attribute to set on the element.

    Returns:
        The (now detached) script element that was executed.
    """
    document = get_document(root)
    # TODO: Investigate whether this has to be a blob for CSP compliance
    script = document.createElement("script")
    script.type = "text/javascript"
    script.textContent = f"{src}\n//# sourceURL=dynamic-user-code.js"
    if is_page_specific:
        script.setAttribute(ATTR_PAGE_SPECIFIC, "true")
    if with_class:
        script.setAttribute("class", with_class)
    head = document.head or document.documentElement
    head.appendChild(script)
    script.remove()
    return script


def add_style(
    root,
    css: str,
    is_page_specific: bool = False,
    with_class: str = "",
    using_shadow_dom: bool = False,
) -> None:
    """Adds CSS content to the page."""
    document = get_document(root)
    if using_shadow_dom:
        # Constructed stylesheets can only be adopted by documents from the
        # same realm, so build it with the owning window's constructor.
        window = get_window(root)
        if is_pyodide():
            style_sheet = window.CSSStyleSheet.new()
        else:
            style_sheet = window.CSSStyleSheet()
        style_sheet.replaceSync(css)
        root.adoptedStyleSheets = root.adoptedStyleSheets.concat([style_sheet])
    else:
        style = document.createElement("style")
        style.innerHTML = css
        if is_page_specific:
            style.setAttribute(ATTR_PAGE_SPECIFIC, "true")
        if with_class:
            style.setAttribute("class", with_class)
        head = document.getElementsByTagName("head")[0]
        head.appendChild(style)
        return style


def add_link(
    root, css_link: str, is_page_specific: bool = False, with_class: str = ""
) -> None:
    """Adds a link element to the page for CSS files."""
    document = get_document(root)
    link = document.createElement("link")
    link.setAttribute("type", "text/css")
    link.setAttribute("rel", "stylesheet")
    link.setAttribute("href", css_link)
    if is_page_specific:
        link.setAttribute(ATTR_PAGE_SPECIFIC, "true")
    if with_class:
        link.setAttribute("class", with_class)
    # TODO: Handle this for shadow DOM
    head = document.getElementsByTagName("head")[0]
    head.appendChild(link)
    return link


def add_link_to_shadow(shadow_root, css_link: str, with_class: str = "") -> None:
    """Adds a link element to the shadow DOM for CSS files."""
    link = get_document(shadow_root).createElement("link")
    link.setAttribute("type", "text/css")
    link.setAttribute("rel", "stylesheet")
    link.setAttribute("href", css_link)
    if with_class:
        link.setAttribute("class", with_class)
    shadow_root.appendChild(link)


def add_style_to_shadow(
    shadow_root, css: str, with_class: str = "", is_page_specific: bool = False
) -> None:
    """Adds CSS content to the shadow DOM by creating a style element."""
    style = get_document(shadow_root).createElement("style")
    style.innerHTML = css
    if is_page_specific:
        style.setAttribute(ATTR_PAGE_SPECIFIC, "true")
    if with_class:
        style.setAttribute("class", with_class)
    shadow_root.appendChild(style)


def add_header(root, header_content: str) -> None:
    """Adds content to the document head."""
    document = get_document(root)
    # TODO: For shadow DOM need to find the pseudo-head
    head = document.getElementsByTagName("head")[0]
    temp_div = document.createElement("div")
    temp_div.innerHTML = header_content
    for child in temp_div.childNodes:
        head.appendChild(child)


def remove_page_content(root) -> None:
    """Removes all page-specific CSS and JS that were added for the previous page.

    Page-specific styles may live in the global head (light DOM) or inside an
    instance's shadow root, so remove each element from its own parent rather
    than assuming the head.
    """
    elements = list(root.querySelectorAll(f"style[{ATTR_PAGE_SPECIFIC}='true']"))
    elements.extend(root.querySelectorAll(f"script[{ATTR_PAGE_SPECIFIC}='true']"))
    head = get_document(root).getElementsByTagName("head")[0]
    if head:
        elements.extend(head.querySelectorAll(f"style[{ATTR_PAGE_SPECIFIC}='true']"))
        elements.extend(head.querySelectorAll(f"script[{ATTR_PAGE_SPECIFIC}='true']"))

    for element in elements:
        element.remove()


def remove_existing_theme(root, theme_class: str) -> None:
    """Removes existing theme-related link and style elements from the document head."""
    document = get_document(root)
    elements = list(document.querySelectorAll(f"link.{theme_class}"))
    elements.extend(document.querySelectorAll(f"script.{theme_class}"))

    # TODO: For shadowdom need to find the pseudo-head
    head = document.getElementsByTagName("head")[0]

    if head:
        for element in elements:
            head.removeChild(element)


def _swap_asset_href(current_href: str, from_path: str, to_path: str) -> str:
    if not current_href:
        return to_path
    if current_href.endswith(from_path):
        return current_href[: -len(from_path)] + to_path
    index = current_href.rfind(from_path)
    if index != -1:
        return current_href[:index] + to_path + current_href[index + len(from_path) :]
    return to_path


def swap_debug_mode(root):
    debug_css = GLOBAL_DRAFTER_CSS_PATHS[True].url
    non_debug_css = GLOBAL_DRAFTER_CSS_PATHS[False].url
    existing_debug_link = root.querySelector(f"link.{DRAFTER_TAG_CLASSES['DEBUG_CSS']}")
    existing_non_debug_link = root.querySelector(
        f"link.{DRAFTER_TAG_CLASSES['NON_DEBUG_CSS']}"
    )
    if existing_debug_link:
        current_href = existing_debug_link.getAttribute("href")
        existing_debug_link.setAttribute(
            "href", _swap_asset_href(current_href, debug_css, non_debug_css)
        )
        existing_debug_link.classList.remove(DRAFTER_TAG_CLASSES["DEBUG_CSS"])
        existing_debug_link.classList.add(DRAFTER_TAG_CLASSES["NON_DEBUG_CSS"])
    elif existing_non_debug_link:
        current_href = existing_non_debug_link.getAttribute("href")
        existing_non_debug_link.setAttribute(
            "href", _swap_asset_href(current_href, non_debug_css, debug_css)
        )
        existing_non_debug_link.classList.remove(DRAFTER_TAG_CLASSES["NON_DEBUG_CSS"])
        existing_non_debug_link.classList.add(DRAFTER_TAG_CLASSES["DEBUG_CSS"])


def update_subtle_debug_entry(root, in_debug_mode: bool, enabled: bool) -> None:
    """Update subtle production debug-entry visibility and metadata."""
    subtle_entry = root.querySelector(f"#{DRAFTER_TAG_IDS['SUBTLE_DEBUG_ENTRY']}")
    if not subtle_entry:
        return

    subtle_entry.setAttribute("data-enabled", "true" if enabled else "false")
    subtle_entry.setAttribute(
        "data-visible", "true" if enabled and not in_debug_mode else "false"
    )
