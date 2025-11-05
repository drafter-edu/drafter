# from drafter.setup import *
from dataclasses import dataclass
from drafter.components import (
    PageContent,
    Content,
    Component,
    Div,
    Span,
    LineBreak,
    HorizontalRule,
    Row,
    BulletedList,
    NumberedList,
    List,
    Division,
    Box,
    Text,
    Pre,
    PreformattedText,
    Header,
    TextBox,
    TextArea,
    SelectBox,
    CheckBox,
    Table,
    Link,
    Button,
    Argument,
    Image,
    Download,
    FileUpload,
    MatPlotLibPlot,
)
from drafter.launch import start_server

# from drafter.styling import *
from drafter.client_server.commands import get_main_server, set_main_server
from drafter.router.commands import route
from drafter.payloads.page import Page
from drafter.deploy import (
    hide_debug_information,
    show_debug_information,
    set_website_title,
    set_website_framed,
    set_website_style,
    add_website_header,
    add_website_css,
    set_site_information,
    get_site_information,
    deploy_site,
)

# from drafter.server import *
# from drafter.testing import assert_equal
# import drafter.hacks

# Provide default route
# route("index")(default_index)


__all__ = [
    "dataclass",
    "Page",
    "get_main_server",
    "set_main_server",
    "route",
    "start_server",
    "PageContent",
    "Div",
    "Span",
    "LineBreak",
    "HorizontalRule",
    "Row",
    "BulletedList",
    "NumberedList",
    "List",
    "Division",
    "Box",
    "Text",
    "Pre",
    "PreformattedText",
    "Header",
    "TextBox",
    "TextArea",
    "CheckBox",
    "SelectBox",
    "Table",
    "Link",
    "Button",
    "Argument",
    "Image",
    "Download",
    "FileUpload",
    "MatPlotLibPlot",
    "hide_debug_information",
    "show_debug_information",
    "set_website_title",
    "set_website_framed",
    "set_website_style",
    "add_website_header",
    "add_website_css",
    "set_site_information",
    "get_site_information",
    "deploy_site",
]

__version__ = "2.0.0"

if __name__ == "__main__":
    import sys
    from drafter.command_line import parse_args, build_site

    options = parse_args(sys.argv[1:])
    build_site(options)
