"""User-facing functions for configuring site appearance and deployment.

Provides convenience wrappers around ClientServer.reconfigure for settings
such as debug information visibility, site title, theme, framing, custom
header/CSS content, and site metadata.
"""

from drafter.client_server.client_server import ClientServer
from drafter.client_server.commands import get_main_server


def hide_debug_information(server: ClientServer | None = None):
    """
    Hides debug information from the website, so that it will not appear. Useful
    for deployed websites.

    Args:
        server: The server to configure. If None, uses the main server.
    """
    if server is None:
        server = get_main_server()
    server.reconfigure(in_debug_mode=False)


def show_debug_information(server: ClientServer | None = None):
    """
    Shows debug information on the website. Useful for development.

    Args:
        server: The server to configure. If None, uses the main server.
    """
    if server is None:
        server = get_main_server()
    server.reconfigure(in_debug_mode=True)


def set_website_title(title: str, server: ClientServer | None = None):
    """
    Sets the title of the website, as it appears in the browser tab.

    Args:
        title: The title of the website.
        server: The server to configure. If None, uses the main server.
    """
    if server is None:
        server = get_main_server()
    server.reconfigure(site_title=title)


def set_website_framed(framed: bool, server: ClientServer | None = None):
    """
    Sets whether the website should be framed or not. If you are deploying the website, then
    this would be a common thing to set to False.

    Args:
        framed: Whether the website should be framed or not.
        server: The server to configure. If None, uses the main server.
    """
    if server is None:
        server = get_main_server()
    server.reconfigure(framed=framed)


def set_site_information(
    author,
    description,
    sources,
    planning,
    links,
    server: ClientServer | None = None,
):
    """
    Sets the information about the website, such as the author, description,
    sources, planning information, and related links.

    Args:
        author: The author of the website.
        description: Description of the website.
        sources: Sources used in the website.
        planning: Planning information.
        links: Related links.
        server: The server to configure. If None, uses the main server.

    Returns:
        None
    """
    if server is None:
        server = get_main_server()
    server.reconfigure(
        author=author,
        description=description,
        sources=sources,
        planning=planning,
        links=links,
    )


def get_site_information(server: ClientServer | None = None):
    """
    Gets the information about the website, such as the author, description, sources.

    Args:
        server: The server to query. If None, uses the main server.

    Returns:
        The site information configuration.
    """
    if server is None:
        server = get_main_server()
    return server.get_config_setting("information")


def set_website_style(style: str | None, server: ClientServer | None = None):
    """
    Sets the style of the website. This must be the name of a valid theme.

    Args:
        style: The theme of the website.
        server: The server to configure. If None, uses the main server.
    """
    if server is None:
        server = get_main_server()
    if style is None:
        style = "none"
    server.reconfigure(theme=style)


def set_website_theme(theme: str | None, server: ClientServer | None = None):
    """
    Sets the theme of the website. This must be the name of a valid theme.

    Args:
        theme: The theme of the website.
        server: The server to configure. If None, uses the main server.
    """
    if server is None:
        server = get_main_server()
    if theme is None:
        theme = "none"
    server.reconfigure(theme=theme)


def add_website_header(header: str, server: ClientServer | None = None):
    """
    Adds additional header content to the website. This is useful for adding custom
    CSS or JavaScript to the website, or other arbitrary header tags like meta tags.

    Args:
        header: The raw header content to add. This will not be wrapped in additional tags.
        server: The server to configure. If None, uses the main server.
    """
    if server is None:
        server = get_main_server()
    server.reconfigure(additional_header_content=header)


def add_website_css(
    selector: str, css: str | None = None, server: ClientServer | None = None
):
    """
    Adds additional CSS content to the website. This is useful for adding custom
    CSS to the website, either for specific selectors or for general styles.
    If you only provide one parameter, it will be used as raw CSS content.
    If you provide both parameters, they will be used to create a CSS rule; the first parameter
    is the CSS selector, and the second parameter is the CSS content that will be wrapped in {}.

    Args:
        selector: The CSS selector to apply the CSS to, or the CSS content if the second parameter is None.
        css: The CSS content to apply to the selector.
        server: The server to configure. If None, uses the main server.
    """
    if server is None:
        server = get_main_server()
    if css is None:
        # Treat selector as raw CSS content
        server.reconfigure(additional_style_content=selector)
    else:
        # Create a CSS rule from selector and content
        server.reconfigure(additional_style_content=f"{selector} {{{css}}}\n")


def deploy_site(image_folder="images", server: ClientServer | None = None):
    """
    Prepares the website for deployment. Currently this only turns off debug
    information; the `image_folder` argument is accepted for compatibility
    but is not yet used.

    Args:
        image_folder: The folder where images are stored (currently unused).
        server: The server to configure. If None, uses the main server.
    """
    hide_debug_information(server=server)
    # TODO: Implement production mode and image folder in V2
    pass
