from typing import Optional, Dict, Any
from drafter.payloads.page import Page
from drafter.client_server.commands import get_main_server
from drafter.client_server.client_server import ClientServer

# Global storage for site information
_SITE_INFORMATION: Optional[Dict[str, Any]] = None


def hide_debug_information(server: Optional[ClientServer] = None):
    """
    Hides debug information from the website, so that it will not appear. Useful
    for deployed websites.
    
    :param server: The server to configure. If None, uses the main server.
    """
    if server is None:
        server = get_main_server()
    server.configuration.in_debug_mode = False


def show_debug_information(server: Optional[ClientServer] = None):
    """
    Shows debug information on the website. Useful for development.
    
    :param server: The server to configure. If None, uses the main server.
    """
    if server is None:
        server = get_main_server()
    server.configuration.in_debug_mode = True


def set_website_title(title: str, server: Optional[ClientServer] = None):
    """
    Sets the title of the website, as it appears in the browser tab.

    :param title: The title of the website.
    :param server: The server to configure. If None, uses the main server.
    """
    if server is None:
        server = get_main_server()
    server.configuration.site_title = title


def set_website_framed(framed: bool, server: Optional[ClientServer] = None):
    """
    Sets whether the website should be framed or not. If you are deploying the website, then
    this would be a common thing to set to False.

    :param framed: Whether the website should be framed or not.
    :param server: The server to configure. If None, uses the main server.
    """
    if server is None:
        server = get_main_server()
    server.configuration.framed = framed


def set_site_information(
    author,
    description,
    sources,
    planning,
    links,
):
    """
    Sets the information about the website, such as the author, description, sources,
    planning, and links. This information is used to populate the about page.
    
    :param author: The author(s) of the website
    :param description: A description of the website
    :param sources: Sources or references used
    :param planning: Planning information or documentation
    :param links: External links related to the website
    :return: None
    """
    global _SITE_INFORMATION
    _SITE_INFORMATION = {
        "author": author,
        "description": description,
        "sources": sources,
        "planning": planning,
        "links": links,
    }


def get_site_information() -> Optional[Dict[str, Any]]:
    """
    Gets the site information that was previously set.
    
    :return: Dictionary containing site information or None if not set
    """
    return _SITE_INFORMATION


def set_website_style(style: Optional[str], server: Optional[ClientServer] = None):
    """
    Sets the style of the website. This is a string that will be used to determine the
    CSS style of the website from the available styles (e.g., `skeleton`, `bootstrap`).
    This list will be expanded in the future.

    :param style: The style of the website.
    :param server: The server to configure. If None, uses the main server.
    """
    if server is None:
        server = get_main_server()
    if style is None:
        style = "none"
    server.configuration.style = style


def add_website_header(header: str, server: Optional[ClientServer] = None):
    """
    Adds additional header content to the website. This is useful for adding custom
    CSS or JavaScript to the website, or other arbitrary header tags like meta tags.

    :param header: The raw header content to add. This will not be wrapped in additional tags.
    :param server: The server to configure. If None, uses the main server.
    """
    if server is None:
        server = get_main_server()
    server.configuration.additional_header_content.append(header)


def add_website_css(selector: str, css: Optional[str] = None, server: Optional[ClientServer] = None):
    """
    Adds additional CSS content to the website. This is useful for adding custom
    CSS to the website, either for specific selectors or for general styles.
    If you only provide one parameter, it will be used as raw CSS content.
    If you provide both parameters, they will be used to create a CSS rule; the first parameter
    is the CSS selector, and the second parameter is the CSS content that will be wrapped in {}.

    :param selector: The CSS selector to apply the CSS to, or the CSS content if the second parameter is None.
    :param css: The CSS content to apply to the selector.
    :param server: The server to configure. If None, uses the main server.
    """
    if server is None:
        server = get_main_server()
    if css is None:
        # Treat selector as raw CSS content
        server.configuration.additional_css_content.append(selector)
    else:
        # Create a CSS rule from selector and content
        server.configuration.additional_css_content.append(
            f"{selector} {{{css}}}"
        )


def deploy_site(image_folder="images", server: Optional[ClientServer] = None):
    """
    Deploys the website with the given image folder. This will set the production
    flag to True and turn off debug information, too.

    :param image_folder: The folder where images are stored.
    :param server: The server to configure. If None, uses the main server.
    """
    hide_debug_information(server=server)
    # TODO: Implement production mode and image folder in V2
    pass


def default_index(state) -> Page:
    """
    The default index page for the website. This will show a simple "Hello world!" message.
    You should not modify or use this function; instead, create your own index page.
    """
    return Page(state, ["Hello world!", "Welcome to Drafter."])
