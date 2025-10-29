# from drafter.setup import *
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
    PreformattedText,
    Header,
    TextBox,
    TextArea,
    SelectBox,
    Table,
    Link,
    Button,
    Image,
    Download,
    FileUpload,
    MatPlotLibPlot,
)
from drafter.launch import start_server

# from drafter.styling import *
from drafter.client_server import get_main_server, set_main_server, MAIN_SERVER
from drafter.commands import route
from drafter.payloads.page import Page
# from drafter.server import *
# from drafter.deploy import *
# from drafter.testing import assert_equal
# import drafter.hacks

# Provide default route
# route("index")(default_index)


__all__ = [
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
    "PreformattedText",
    "Header",
    "TextBox",
    "TextArea",
    "SelectBox",
    "Table",
    "Link",
    "Button",
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
