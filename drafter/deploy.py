from typing import Optional
from drafter.server import MAIN_SERVER
from drafter.page import Page


def hide_debug_information():
    """
    Hides debug information from the website, so that it will not appear. Useful
    for deployed websites.
    """
    MAIN_SERVER.configuration.debug = False


def show_debug_information():
    MAIN_SERVER.configuration.debug = True


def set_website_title(title: str):
    MAIN_SERVER.configuration.title = title


def set_website_framed(framed: bool):
    MAIN_SERVER.configuration.framed = framed


def set_website_style(style: str):
    MAIN_SERVER.configuration.style = style


def add_website_header(header: str):
    MAIN_SERVER.configuration.additional_header_content.append(header)


def add_website_css(selector: str, css: Optional[str] = None):
    if css is None:
        MAIN_SERVER.configuration.additional_css_content.append(selector+"\n")
    else:
        MAIN_SERVER.configuration.additional_css_content.append(f"{selector} {{{css}}}\n")


def deploy_site(image_folder='images'):
    hide_debug_information()
    MAIN_SERVER.production = True
    MAIN_SERVER.image_folder = image_folder


def default_index(state) -> Page:
    return Page(state, ["Hello world!", "Welcome to Drafter."])
