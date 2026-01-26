from drafter.site.site import GLOBAL_DRAFTER_CSS_PATHS
import js

document = js.document  # type: ignore

ATTR_PAGE_SPECIFIC = "data-drafter-page-specific"


def add_script(
    root, src: str, is_page_specific: bool = False, with_class: str = ""
) -> None:
    """
    Adds a script to the page.

    Args:
        src: The script source URL or content.
        is_page_specific: If True, marks the script as page-specific (will be removed on navigation).
    """
    script = document.createElement("script")
    script.src = src
    if is_page_specific:
        script.setAttribute(ATTR_PAGE_SPECIFIC, "true")
    if with_class:
        script.setAttribute("class", with_class)
    head = root.getElementsByTagName("head")[0]
    head.appendChild(script)
    return script


def add_style(
    root, css: str, is_page_specific: bool = False, with_class: str = ""
) -> None:
    """
    Adds CSS content to the page by creating a style element.

    Args:
        css: CSS content to add to the page.
        is_page_specific: If True, marks the style as page-specific (will be removed on navigation).
    """
    style = document.createElement("style")
    style.innerHTML = css
    if is_page_specific:
        style.setAttribute(ATTR_PAGE_SPECIFIC, "true")
    if with_class:
        style.setAttribute("class", with_class)
    head = root.getElementsByTagName("head")[0]
    head.appendChild(style)
    return style


def swap_debug_mode(root):
    # If href=GLOBAL_DRAFTER_CSS_PATHS[True] exists, then we're in debug mode, so switch to the non-debug CSS. Otherwise, switch to the debug CSS.
    debug_css = GLOBAL_DRAFTER_CSS_PATHS[True]
    non_debug_css = GLOBAL_DRAFTER_CSS_PATHS[False]
    existing_debug_link = root.querySelector(f'link[href="{debug_css}"]')
    existing_non_debug_link = root.querySelector(f'link[href="{non_debug_css}"]')
    if existing_debug_link:
        existing_debug_link.setAttribute("href", non_debug_css)
    elif existing_non_debug_link:
        existing_non_debug_link.setAttribute("href", debug_css)


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
