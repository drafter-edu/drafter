from drafter.site.site import DRAFTER_TAG_CLASSES, GLOBAL_DRAFTER_CSS_PATHS
import js
from drafter.helpers.utils import is_skulpt, is_pyodide

document = js.document  # type: ignore

ATTR_PAGE_SPECIFIC = "data-drafter-page-specific"


def add_js(
    root, src: str, is_page_specific: bool = False, with_class: str = ""
) -> None:
    """
    Adds a script to the page.

    Args:
        src: The script source URL or content.
        is_page_specific: If True, marks the script as page-specific (will be removed on navigation).
    """
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
    """
    Adds CSS content to the page by creating a style element if we're not
    using shadow DOM, or using CSSStyleSheet if we are.

    Args:
        css: CSS content to add to the page.
        is_page_specific: If True, marks the style as page-specific (will be removed on navigation).
    """
    if using_shadow_dom:
        if is_pyodide():
            style_sheet = js.CSSStyleSheet.new()
        else:
            style_sheet = js.CSSStyleSheet()
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
    # If href=GLOBAL_DRAFTER_CSS_PATHS[True].url exists, then we're in debug mode, so switch to the non-debug CSS. Otherwise, switch to the debug CSS.
    debug_css = GLOBAL_DRAFTER_CSS_PATHS[True].url
    non_debug_css = GLOBAL_DRAFTER_CSS_PATHS[False].url
    existing_debug_link = root.querySelector(f'link.{DRAFTER_TAG_CLASSES["DEBUG_CSS"]}')
    existing_non_debug_link = root.querySelector(f'link.{DRAFTER_TAG_CLASSES["NON_DEBUG_CSS"]}')
    if existing_debug_link:
        current_href = existing_debug_link.getAttribute("href")
        existing_debug_link.setAttribute(
            "href", _swap_asset_href(current_href, debug_css, non_debug_css)
        )
        # Update classes: remove DEBUG_CSS, add NON_DEBUG_CSS
        existing_debug_link.classList.remove(DRAFTER_TAG_CLASSES["DEBUG_CSS"])
        existing_debug_link.classList.add(DRAFTER_TAG_CLASSES["NON_DEBUG_CSS"])
    elif existing_non_debug_link:
        current_href = existing_non_debug_link.getAttribute("href")
        existing_non_debug_link.setAttribute(
            "href", _swap_asset_href(current_href, non_debug_css, debug_css)
        )
        # Update classes: remove NON_DEBUG_CSS, add DEBUG_CSS
        existing_non_debug_link.classList.remove(DRAFTER_TAG_CLASSES["NON_DEBUG_CSS"])
        existing_non_debug_link.classList.add(DRAFTER_TAG_CLASSES["DEBUG_CSS"])
    print(debug_css, non_debug_css, existing_debug_link, existing_non_debug_link)


def add_link(
    root, css_link: str, is_page_specific: bool = False, with_class: str = ""
) -> None:
    """
    Adds a link element to the page for CSS files.

    Args:
        css_link: The href of the CSS file to add.
        is_page_specific: If True, marks the link as page-specific (will be removed on navigation).
    """
    link = document.createElement("link")
    link.setAttribute("type", "text/css")
    link.setAttribute("rel", "stylesheet")
    link.setAttribute("href", css_link)
    if is_page_specific:
        link.setAttribute(ATTR_PAGE_SPECIFIC, "true")
    if with_class:
        link.setAttribute("class", with_class)
    # TODO: Handle this for shadow DOM by finding the pseudo-head and appending to that instead of the real head
    head = document.getElementsByTagName("head")[0]
    head.appendChild(link)
    return link


def add_header(root, header_content: str) -> None:
    """
    Adds content to the document head.

    Args:
        header_content: HTML content to add to the head.
    """
    # TODO: For shadow DOM need to find the pseudo-head and append to that instead of the real head
    head = document.getElementsByTagName("head")[0]
    temp_div = document.createElement("div")
    temp_div.innerHTML = header_content
    for child in temp_div.childNodes:
        head.appendChild(child)


def remove_page_content(root) -> None:
    """
    Removes all page-specific CSS and JS that were added for the previous page.
    This ensures that page-specific styles/scripts don't persist across navigation.
    """
    # Remove page-specific style tags
    elements = list(root.querySelectorAll(f"style[{ATTR_PAGE_SPECIFIC}='true']"))
    elements.extend(root.querySelectorAll(f"script[{ATTR_PAGE_SPECIFIC}='true']"))
    # TODO: For shadowdom need to find the pseudo-head
    head = document.getElementsByTagName("head")[0]

    if not head:
        return

    for element in elements:
        head.removeChild(element)


def remove_existing_theme(root, theme_class: str) -> None:
    """
    Removes existing theme-related link and style elements from the document head.

    Args:
        theme_class: The CSS class used to identify theme-related elements.
    """
    elements = list(document.querySelectorAll(f"link.{theme_class}"))
    elements.extend(document.querySelectorAll(f"script.{theme_class}"))

    # TODO: For shadowdom need to find the pseudo-head
    head = document.getElementsByTagName("head")[0]

    if head:
        for element in elements:
            head.removeChild(element)
