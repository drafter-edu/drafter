# from drafter.setup import *
from drafter.components.components import Text, Table, TextBox, Button, MatPlotLibPlot
from drafter.launch import start_server

# from drafter.styling import *
from drafter.client_server import Server, get_main_server, set_main_server, MAIN_SERVER
from drafter.commands import route
from drafter.page import Page
# from drafter.server import *
# from drafter.deploy import *
# from drafter.testing import assert_equal
# import drafter.hacks

# Provide default route
# route("index")(default_index)


__all__ = [
    "Server",
    "get_main_server",
    "set_main_server",
    "MAIN_SERVER",
    "route",
    "start_server",
    "Page",
    "Text",
    "Table",
    "TextBox",
    "Button",
    "MatPlotLibPlot",
]

__version__ = "2.0.0"

if __name__ == "__main__":
    import sys
    from drafter.command_line import parse_args, build_site

    options = parse_args(sys.argv[1:])
    build_site(options)
