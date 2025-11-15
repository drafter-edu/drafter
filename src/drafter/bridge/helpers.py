import document  # type: ignore

ATTR_PAGE_SPECIFIC = "data-drafter-page-specific"


def add_script(src: str, is_page_specific: bool = False, with_class: str = "") -> None:
    """
    Adds a script to the page.

    :param src: The script source URL or content.
    :param is_page_specific: If True, marks the script as page-specific (will be removed on navigation).
    """
    script = document.createElement("script")
    script.src = src
    if is_page_specific:
        script.setAttribute(ATTR_PAGE_SPECIFIC, "true")
    if with_class:
        script.setAttribute("class", with_class)
    head = document.getElementsByTagName("head")[0]
    head.appendChild(script)
    return script


def add_style(css: str, is_page_specific: bool = False, with_class: str = "") -> None:
    """
    Adds CSS content to the page by creating a style element.

    :param css: CSS content to add to the page.
    :param is_page_specific: If True, marks the style as page-specific (will be removed on navigation).
    """
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
    css_link: str, is_page_specific: bool = False, with_class: str = ""
) -> None:
    """
    Adds a link element to the page for CSS files.

    :param css_link: The href of the CSS file to add.
    :param is_page_specific: If True, marks the link as page-specific (will be removed on navigation).
    """
    link = document.createElement("link")
    link.setAttribute("type", "text/css")
    link.setAttribute("rel", "stylesheet")
    link.setAttribute("href", css_link)
    if is_page_specific:
        link.setAttribute(ATTR_PAGE_SPECIFIC, "true")
    if with_class:
        link.setAttribute("class", with_class)
    head = document.getElementsByTagName("head")[0]
    head.appendChild(link)
    return link


def add_header(header_content: str) -> None:
    """
    Adds content to the document head.

    :param header_content: HTML content to add to the head.
    """
    head = document.getElementsByTagName("head")[0]
    temp_div = document.createElement("div")
    temp_div.innerHTML = header_content
    for child in temp_div.childNodes:
        head.appendChild(child)


def remove_page_content() -> None:
    """
    Removes all page-specific CSS and JS that were added for the previous page.
    This ensures that page-specific styles/scripts don't persist across navigation.
    """
    # Remove page-specific style tags
    elements = list(document.querySelectorAll(f"style[{ATTR_PAGE_SPECIFIC}='true']"))
    elements.extend(document.querySelectorAll(f"script[{ATTR_PAGE_SPECIFIC}='true']"))

    for element in elements:
        if element.parentNode:
            # TODO: Haven't implemented parentNode yet in skulpt
            element.parentNode.removeChild(element)


def remove_existing_theme(theme_class: str) -> None:
    """
    Removes existing theme-related link and style elements from the document head.

    :param theme_class: The CSS class used to identify theme-related elements.
    """
    elements = list(document.querySelectorAll(f"link.{theme_class}"))
    elements.extend(document.querySelectorAll(f"script.{theme_class}"))

    head = document.getElementsByTagName("head")[0]

    if head:
        for element in elements:
            head.removeChild(element)
