"""Re-exports the Drafter component API from its submodules.

This package gathers every component into a single import location, so
that `from drafter.components import ...` works for all of them. The main
groups are:

- Base machinery: `Component`, `Content`, `PageContent`
- Layout: `Div`, `Span`, `Row`, `BulletedList`, `NumberedList`,
  `DefinitionList`, `Figure`, `Details`, semantic sections, and spacing
  elements
- Text: `Text`, `Header`, `Pre`, `BlockQuote`, `InlineCode`, `RawHTML`,
  and semantic inline text such as `Strong`, `Emphasis`, `MarkedText`,
  and `Abbreviation`
- Forms: `TextBox`, `TextArea`, `SelectBox`, `CheckBox`, `Label`, and
  date/time inputs
- Navigation: `Link`, `Button`, `Argument`
- Media and graphics: `Image`, `Audio`, `Video`, `Canvas`, `SVG`,
  `MatPlotLibPlot`
- Data display: `Table`, `Output`, `ProgressBar`, `Meter`, `TimeOutput`
- Files: `Download`, `FileUpload`
- Location and maps: `CurrentLocation`, `Location`, `Map` and its markers
  and views
- Timing and persistence: `Timer`, `Clock`, `RemovePersistent`
- Audio recording and effects: `Microphone`, `AudioRecorder`, `Tone`,
  `Melody`, `Sound`, and effect wrappers like `Echo` and `Reverb`
- Photo capture: `Camera` and `Photo`
"""

from drafter.components.audio import (
    AudioLevel,
    AudioRecorder,
    Distortion,
    Echo,
    Melody,
    Microphone,
    Muffle,
    Recording,
    Reverb,
    Sharpen,
    Sound,
    Tone,
)
from drafter.components.camera import Camera
from drafter.components.data.photo import Photo
from drafter.components.files import Download, FileUpload
from drafter.components.forms import (
    CheckBox,
    DateInput,
    DateTimeInput,
    Label,
    RelatedCheckBox,
    SelectBox,
    TextArea,
    TextBox,
    TimeInput,
)
from drafter.components.geolocation import CurrentLocation, Location
from drafter.components.images import Image
from drafter.components.layout import (
    Article,
    Aside,
    Box,
    BulletedList,
    DefinitionList,
    Details,
    Div,
    Division,
    Figure,
    FigureCaption,
    FooterContent,
    HeaderContent,
    HorizontalRule,
    LineBreak,
    Main,
    Nav,
    NumberedList,
    Paragraph,
    Row,
    Section,
    Span,
)
from drafter.components.links import Argument, Button, Link
from drafter.components.map import (
    AddMarkerFunction,
    Map,
    MapLocation,
    MapMarker,
    MapView,
)
from drafter.components.media import SVG, Audio, Canvas, Video
from drafter.components.output import Meter, Output, ProgressBar, TimeOutput
from drafter.components.page_content import Component, Content, PageContent
from drafter.components.persistence import RemovePersistent
from drafter.components.plotting import MatPlotLibPlot

# TODO: Sliders, Autocomplete, RadioButtons
from drafter.components.tables import Table
from drafter.components.text import (
    Abbreviation,
    BlockQuote,
    DefinitionTerm,
    DeletedText,
    Emphasis,
    Header,
    HtmlTag,
    InlineCode,
    InlineQuotation,
    InlineVariable,
    InsertedText,
    KeyboardInput,
    MarkedText,
    Pre,
    PreformattedText,
    RawHTML,
    SampleOutput,
    SmallText,
    Strong,
    Subscript,
    Superscript,
    Text,
)
from drafter.components.timer import Clock, Timer

__all__ = [
    "PageContent",
    "Content",
    "Component",
    "Div",
    "Span",
    "LineBreak",
    "HorizontalRule",
    "Paragraph",
    "Section",
    "Article",
    "Aside",
    "Main",
    "Nav",
    "HeaderContent",
    "FooterContent",
    "Row",
    "BulletedList",
    "NumberedList",
    "Division",
    "Box",
    "Figure",
    "FigureCaption",
    "Details",
    "DefinitionList",
    "BlockQuote",
    "Text",
    "InlineCode",
    "HtmlTag",
    "RawHTML",
    "Pre",
    "PreformattedText",
    "Header",
    "Strong",
    "Emphasis",
    "InlineQuotation",
    "DefinitionTerm",
    "Abbreviation",
    "DeletedText",
    "InsertedText",
    "KeyboardInput",
    "MarkedText",
    "SampleOutput",
    "SmallText",
    "Superscript",
    "Subscript",
    "InlineVariable",
    "TextBox",
    "TextArea",
    "SelectBox",
    "CheckBox",
    "RelatedCheckBox",
    "Label",
    "DateTimeInput",
    "DateInput",
    "TimeInput",
    "CurrentLocation",
    "Location",
    "Map",
    "MapLocation",
    "MapMarker",
    "MapView",
    "AddMarkerFunction",
    "ProgressBar",
    "Meter",
    "TimeOutput",
    "Output",
    "Table",
    "Link",
    "Button",
    "Argument",
    "Image",
    "Download",
    "FileUpload",
    "MatPlotLibPlot",
    "Audio",
    "Video",
    "Canvas",
    "SVG",
    "Timer",
    "Clock",
    "RemovePersistent",
    "Camera",
    "Photo",
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
]
