"""Drafter: a friendly web framework for students learning Python.

Drafter turns plain Python functions into interactive websites: routes
(functions decorated with `@route`) take the current state and return a
`Page` of components, and `start_server(state)` launches the site. This
package root re-exports everything a student application needs, so a
single `from drafter import *` provides:

- The `route` decorator, `start_server`, and the `Page`, `Fragment`,
  `Update`, and `Redirect` payload types.
- All page components, from basic content (`Text`, `Header`, `Image`,
  `Table`) and form inputs (`TextBox`, `Button`, `SelectBox`) to richer
  widgets (`Map`, `CurrentLocation`, `Timer`, and the audio family such
  as `Tone`, `Melody`, and `Sound`).
- Styling helpers (`bold`, `change_color`, `update_style`, ...) and site
  configuration functions (`set_website_title`, `set_website_style`, ...).
- Testing and convenience utilities such as `assert_equal`, `dataclass`,
  and `open`.
"""

# Provide dataclass decorator for users' convenience
from dataclasses import dataclass

# Handle configuration if needed
from drafter.configuration import get_system_configuration

from drafter.version import CURRENT_DRAFTER_VERSION

# Load all the Drafter components
from drafter.components import (
    PageContent,
    Content,
    Paragraph,
    Section,
    Article,
    Aside,
    Main,
    Nav,
    HeaderContent,
    FooterContent,
    Component,
    Div,
    Span,
    LineBreak,
    HorizontalRule,
    Row,
    BulletedList,
    NumberedList,
    Division,
    Box,
    Text,
    BlockQuote,
    InlineCode,
    HtmlTag,
    Pre,
    PreformattedText,
    Header,
    TextBox,
    TextArea,
    SelectBox,
    RelatedCheckBox,
    CheckBox,
    Label,
    DateTimeInput,
    DateInput,
    TimeInput,
    CurrentLocation,
    Location,
    Map,
    MapLocation,
    MapMarker,
    MapView,
    AddMarkerFunction,
    Progress,
    Output,
    RawHTML,
    Audio,
    Video,
    Canvas,
    SVG,
    Table,
    Link,
    Button,
    Argument,
    Image,
    Download,
    FileUpload,
    MatPlotLibPlot,
    Timer,
    Clock,
    RemovePersistent,
    Tone,
    Melody,
    Sound,
    Microphone,
    AudioRecorder,
    AudioLevel,
    Recording,
    Echo,
    Reverb,
    Muffle,
    Sharpen,
    Distortion,
)

from drafter.styling.styling import (
    update_style,
    update_attr,
    float_right,
    float_left,
    bold,
    italic,
    underline,
    strikethrough,
    monospace,
    small_font,
    large_font,
    change_color,
    change_background_color,
    change_text_size,
    change_text_font,
    change_text_align,
    change_text_decoration,
    change_height,
    change_width,
    change_border,
    change_margin,
    change_padding,
)
from drafter.router.commands import route, add_route
from drafter.payloads import Page, Fragment, Redirect, Update
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

# Alternative file handling approach
from drafter.files.opening import open, get_drafter_path
from drafter.testing import assert_equal
from drafter.client_server.commands import get_main_server, set_main_server

# Key starting point for Drafter applications, whether building or running
from drafter.launch import start_server


__all__ = [
    "get_system_configuration",
    "dataclass",
    "open",
    "get_drafter_path",
    "Page",
    "Fragment",
    "Update",
    "Redirect",
    "Content",
    "PageContent",
    "Component",
    "get_main_server",
    "set_main_server",
    "route",
    "add_route",
    "start_server",
    "PageContent",
    "Div",
    "Span",
    "LineBreak",
    "HorizontalRule",
    "Row",
    "Paragraph",
    "Section",
    "Article",
    "Aside",
    "Main",
    "Nav",
    "HeaderContent",
    "FooterContent",
    "BulletedList",
    "NumberedList",
    "Division",
    "Box",
    "BlockQuote",
    "Text",
    "InlineCode",
    "HtmlTag",
    "Pre",
    "PreformattedText",
    "Header",
    "TextBox",
    "TextArea",
    "CheckBox",
    "RelatedCheckBox",
    "SelectBox",
    "Label",
    "DateTimeInput",
    "DateInput",
    "TimeInput",
    "CurrentLocation",
    "Map",
    "MapLocation",
    "MapMarker",
    "MapView",
    "AddMarkerFunction",
    "Location",
    "Progress",
    "Output",
    "RawHTML",
    "Audio",
    "Video",
    "Canvas",
    "SVG",
    "Table",
    "Link",
    "Button",
    "Argument",
    "Image",
    "Download",
    "FileUpload",
    "MatPlotLibPlot",
    "Timer",
    "Clock",
    "RemovePersistent",
    "Tone",
    "Melody",
    "Sound",
    "Microphone",
    "AudioRecorder",
    "AudioLevel",
    "Recording",
    "Echo",
    "Reverb",
    "Muffle",
    "Sharpen",
    "Distortion",
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
    "assert_equal",
    "update_style",
    "update_attr",
    "float_right",
    "float_left",
    "bold",
    "italic",
    "underline",
    "strikethrough",
    "monospace",
    "small_font",
    "large_font",
    "change_color",
    "change_background_color",
    "change_text_size",
    "change_text_font",
    "change_text_align",
    "change_text_decoration",
    "change_height",
    "change_width",
    "change_border",
    "change_margin",
    "change_padding",
]

__version__ = CURRENT_DRAFTER_VERSION

if __name__ == "__main__":
    # This drafter/__init__.py file was executed directly, unusual circumstance.
    # Give a message to the user about running it normally.
    print(
        "This file is not meant to be executed directly. Please run your Drafter application script instead."
    )
