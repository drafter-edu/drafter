from typing import Optional, Union
from drafter.server import MAIN_SERVER, SiteInformationType
from drafter.payloads.page import Page
from drafter.components.components import PageContent


def hide_debug_information():
    """
    Hides debug information from the website, so that it will not appear. Useful
    for deployed websites.
    """
    MAIN_SERVER.configuration.debug = False


def show_debug_information():
    """
    Shows debug information on the website. Useful for development.
    """
    MAIN_SERVER.configuration.debug = True


def set_website_title(title: str):
    """
    Sets the title of the website, as it appears in the browser tab.

    :param title: The title of the website.
    """
    MAIN_SERVER.configuration.title = title


def set_website_framed(framed: bool):
    """
    Sets whether the website should be framed or not. If you are deploying the website, then
    this would be a common thing to set to False.

    :param framed: Whether the website should be framed or not.
    """
    MAIN_SERVER.configuration.framed = framed


def set_site_information(
    author: SiteInformationType,
    description: SiteInformationType,
    sources: SiteInformationType,
    planning: SiteInformationType,
    links: SiteInformationType,
):
    """
    Sets the information about the website, such as the author, description, sources,
    :param author:
    :param description:
    :param sources:
    :param planning:
    :param links:
    :return:
    """
    return MAIN_SERVER.set_information(
        author=author,
        description=description,
        sources=sources,
        planning=planning,
        links=links,
    )


def set_website_style(style: Optional[str]):
    """
    Sets the style of the website. This is a string that will be used to determine the
    CSS style of the website from the available styles (e.g., `skeleton`, `bootstrap`).
    This list will be expanded in the future.

    :param style: The style of the website.
    """
    if style is None:
        style = "none"
    MAIN_SERVER.configuration.style = style


def add_website_header(header: str):
    """
    Adds additional header content to the website. This is useful for adding custom
    CSS or JavaScript to the website, or other arbitrary header tags like meta tags.

    :param header: The raw header content to add. This will not be wrapped in additional tags.
    """
    MAIN_SERVER.configuration.additional_header_content.append(header)


def add_website_css(selector: str, css: Optional[str] = None):
    """
    Adds additional CSS content to the website. This is useful for adding custom
    CSS to the website, either for specific selectors or for general styles.
    If you only provide one parameter, it will be wrapped in <style> tags.
    If you provide both parameters, they will be used to create a CSS rule; the first parameter
    is the CSS selector, and the second parameter is the CSS content that will be wrapped in {}.

    :param selector: The CSS selector to apply the CSS to, or the CSS content if the second parameter is None.
    :param css: The CSS content to apply to the selector.
    """
    if css is None:
        MAIN_SERVER.configuration.additional_css_content.append(selector + "\n")
    else:
        MAIN_SERVER.configuration.additional_css_content.append(
            f"{selector} {{{css}}}\n"
        )


def deploy_site(image_folder="images"):
    """
    Deploys the website with the given image folder. This will set the production
    flag to True and turn off debug information, too.

    :param image_folder: The folder where images are stored.
    """
    hide_debug_information()
    MAIN_SERVER.production = True
    MAIN_SERVER.image_folder = image_folder


def default_index(state) -> Page:
    """
    The default index page for the website. This will show a simple "Hello world!" message.
    You should not modify or use this function; instead, create your own index page.
    """
    return Page(state, ["Hello world!", "Welcome to Drafter."])
