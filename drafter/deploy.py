from drafter.server import MAIN_SERVER
from drafter.page import Page

def hide_debug_information():
    MAIN_SERVER.default_configuration.debug = False


def show_debug_information():
    MAIN_SERVER.default_configuration.debug = True


def set_website_title(title: str):
    MAIN_SERVER.default_configuration.title = title

def set_website_style(style: str):
    MAIN_SERVER.default_configuration.custom_style = style


def deploy_site(image_folder='images'):
    hide_debug_information()
    MAIN_SERVER.production = True
    MAIN_SERVER.image_folder = image_folder


def default_index(state) -> Page:
    return Page(state, ["Hello world!", "Welcome to Drafter."])
