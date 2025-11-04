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
from drafter.client_server.commands import get_main_server, set_main_server, MAIN_SERVER
from drafter.router.commands import route
from drafter.payloads.page import Page

# from drafter.server import *
# from drafter.deploy import add_website_css
from drafter.testing import assert_equal
# import drafter.hacks

# Provide default route
# route("index")(default_index)


__all__ = [
    "dataclass",
    "Page",
    "get_main_server",
    "set_main_server",
    "MAIN_SERVER",
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
]

__version__ = "2.0.0"

if __name__ == "__main__":
    import sys
    from drafter.command_line import parse_args, build_site

    options = parse_args(sys.argv[1:])
    build_site(options)
