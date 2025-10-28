"""Drafter components - remaining components not yet split into separate modules.

This file contains components that haven't been moved to dedicated modules yet.
The base classes, Link, Button, and Argument have been extracted to separate files.
"""

from dataclasses import dataclass, is_dataclass, fields
from typing import Any, Union, Optional, List, Dict, Tuple
import io
import base64
import json
import html

from drafter.constants import LABEL_SEPARATOR, SUBMIT_BUTTON_KEY, JSON_DECODE_SYMBOL
from drafter.urls import remap_attr_styles, friendly_urls, check_invalid_external_url, merge_url_query_params
from drafter.image_support import HAS_PILLOW, PILImage
from drafter.history import safe_repr

# Import base classes from the new base module
from drafter.components.base import (
    PageContent,
    LinkContent,
    Content,
    BASELINE_ATTRS,
    validate_parameter_name,
    make_safe_json_argument,
    make_safe_argument,
    make_safe_name,
)

try:
    import matplotlib.pyplot as plt
    _has_matplotlib = True
except ImportError:
    _has_matplotlib = False


BASE_IMAGE_FOLDER = "/__images"


class Image(PageContent, LinkContent):
    url: str
    width: int
    height: int

    def __init__(self, url: str, width=None, height=None, **kwargs):
        self.url = url
        self.width = width
        self.height = height
        self.extra_settings = kwargs
        self.base_image_folder = BASE_IMAGE_FOLDER

    def open(self, *args, **kwargs):
        if not HAS_PILLOW:
            raise ImportError("Pillow is not installed. Please install it to use this feature.")
        return PILImage.open(*args, **kwargs)

    def new(self, *args, **kwargs):
        if not HAS_PILLOW:
            raise ImportError("Pillow is not installed. Please install it to use this feature.")
        return PILImage.new(*args, **kwargs)

    def render(self, current_state, configuration):
        self.base_image_folder = configuration.deploy_image_path
        return super().render(current_state, configuration)

    def _handle_pil_image(self, image):
        if not HAS_PILLOW or isinstance(image, str):
            return False, image

        image_data = io.BytesIO()
        image.save(image_data, format="PNG")
        image_data.seek(0)
        figure = base64.b64encode(image_data.getvalue()).decode('utf-8')
        figure = f"data:image/png;base64,{figure}"
        return True, figure

    def __str__(self) -> str:
        extra_settings = {}
        if self.width is not None:
            extra_settings['width'] = self.width
        if self.height is not None:
            extra_settings['height'] = self.height
        was_pil, url = self._handle_pil_image(self.url)
        if was_pil:
            return f"<img src='{url}' {self.parse_extra_settings(**extra_settings)}>"
        url, external = self._handle_url(self.url)
        if not external:
            url = self.base_image_folder + url
        parsed_settings = self.parse_extra_settings(**extra_settings)
        return f"<img src='{url}' {parsed_settings}>"


Picture = Image


@dataclass
class TextBox(PageContent):
    name: str
    kind: str
    default_value: Optional[str]

    def __init__(self, name: str, default_value: Optional[str] = None, kind: str = "text", **kwargs):
        validate_parameter_name(name, "TextBox")
        self.name = name
        self.kind = kind
        self.default_value = str(default_value) if default_value is not None else ""
        self.extra_settings = kwargs

    def __str__(self) -> str:
        extra_settings = {}
        if self.default_value is not None:
            extra_settings['value'] = html.escape(self.default_value)
        parsed_settings = self.parse_extra_settings(**extra_settings)
        # TODO: investigate whether we need to make the name safer
        return f"<input type='{self.kind}' name='{self.name}' {parsed_settings}>"


@dataclass
class TextArea(PageContent):
    name: str
    default_value: str
    EXTRA_ATTRS = ["rows", "cols", "autocomplete", "autofocus", "disabled", "placeholder", "readonly", "required"]

    def __init__(self, name: str, default_value: Optional[str] = None, **kwargs):
        validate_parameter_name(name, "TextArea")
        self.name = name
        self.default_value = str(default_value) if default_value is not None else ""
        self.extra_settings = kwargs

    def __str__(self) -> str:
        parsed_settings = self.parse_extra_settings(**self.extra_settings)
        return f"<textarea name='{self.name}' {parsed_settings}>{html.escape(self.default_value)}</textarea>"


@dataclass
class SelectBox(PageContent):
    name: str
    options: List[str]
    default_value: Optional[str]

    def __init__(self, name: str, options: List[str], default_value: Optional[str] = None, **kwargs):
        validate_parameter_name(name, "SelectBox")
        self.name = name
        self.options = [str(option) for option in options]
        self.default_value = str(default_value) if default_value is not None else ""
        self.extra_settings = kwargs

    def __str__(self) -> str:
        extra_settings = {}
        if self.default_value is not None:
            extra_settings['value'] = html.escape(self.default_value)
        parsed_settings = self.parse_extra_settings(**extra_settings)
        options = "\n".join(f"<option {'selected' if option == self.default_value else ''} "
                            f"value='{html.escape(option)}'>{option}</option>"
                            for option in self.options)
        return f"<select name='{self.name}' {parsed_settings}>{options}</select>"


@dataclass
class CheckBox(PageContent):
    EXTRA_ATTRS = ["checked"]
    name: str
    default_value: bool

    def __init__(self, name: str, default_value: bool = False, **kwargs):
        validate_parameter_name(name, "CheckBox")
        self.name = name
        self.default_value = bool(default_value)
        self.extra_settings = kwargs

    def __str__(self) -> str:
        parsed_settings = self.parse_extra_settings(**self.extra_settings)
        checked = 'checked' if self.default_value else ''
        return (f"<input type='hidden' name='{self.name}' value='' {parsed_settings}>"
                f"<input type='checkbox' name='{self.name}' {checked} value='checked' {parsed_settings}>")


@dataclass
class LineBreak(PageContent):
    def __str__(self) -> str:
        return "<br />"


@dataclass
class HorizontalRule(PageContent):
    def __str__(self) -> str:
        return "<hr />"


@dataclass(repr=False)
class _HtmlGroup(PageContent):
    content: List[Any]
    extra_settings: Dict
    kind: str

    def __init__(self, *args, **kwargs):
        self.content = list(args)
        if 'content' in kwargs:
            self.content.extend(kwargs.pop('content'))
        if 'kind' in kwargs:
            self.kind = kwargs.pop('kind')
        if 'extra_settings' in kwargs:
            self.extra_settings = kwargs.pop('extra_settings')
            self.extra_settings.update(kwargs)
        else:
            self.extra_settings = kwargs

    def __repr__(self):
        if self.extra_settings:
            return f"{self.kind.capitalize()}({', '.join(repr(item) for item in self.content)}, {self.extra_settings})"
        return f"{self.kind.capitalize()}({', '.join(repr(item) for item in self.content)})"

    def __str__(self) -> str:
        parsed_settings = self.parse_extra_settings(**self.extra_settings)
        return f"<{self.kind} {parsed_settings}>{''.join(str(item) for item in self.content)}</{self.kind}>"


@dataclass(repr=False)
class Span(_HtmlGroup):
    kind = 'span'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


@dataclass(repr=False)
class Div(_HtmlGroup):
    kind = 'div'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


Division = Div
Box = Div


@dataclass(repr=False)
class Pre(_HtmlGroup):
    content: List[Any]
    kind = 'pre'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


PreformattedText = Pre


@dataclass(repr=False)
class Row(Div):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extra_settings['style_display'] = "flex"
        self.extra_settings['style_flex_direction'] = "row"
        self.extra_settings['style_align_items'] = "center"


@dataclass
class _HtmlList(PageContent):
    items: List[Any]
    kind: str = ""

    def __init__(self, items: List[Any], **kwargs):
        self.items = items
        self.extra_settings = kwargs

    def __str__(self) -> str:
        parsed_settings = self.parse_extra_settings(**self.extra_settings)
        items = "\n".join(f"<li>{item}</li>" for item in self.items)
        return f"<{self.kind} {parsed_settings}>{items}</{self.kind}>"


class NumberedList(_HtmlList):
    kind = "ol"


class BulletedList(_HtmlList):
    kind = "ul"


@dataclass
class Header(PageContent):
    body: str
    level: int = 1

    def __str__(self):
        return f"<h{self.level}>{self.body}</h{self.level}>"


@dataclass
class Table(PageContent):
    rows: List[List[str]]

    def __init__(self, rows: List[List[str]], header=None, **kwargs):
        self.rows = rows
        self.header = header
        self.extra_settings = kwargs
        self.reformat_as_tabular()

    def reformat_as_single(self):
        result = []
        for field in fields(self.rows):
            value = getattr(self.rows, field.name)
            result.append(
                [f"<code>{html.escape(field.name)}</code>",
                 f"<code>{html.escape(field.type.__name__)}</code>",
                 f"<code>{safe_repr(value)}</code>"])
        self.rows = result
        if not self.header:
            self.header = ["Field", "Type", "Current Value"]

    def reformat_as_tabular(self):
        # print(self.rows, is_dataclass(self.rows))
        if is_dataclass(self.rows):
            self.reformat_as_single()
            return
        result = []
        had_dataclasses = False
        for row in self.rows:
            if is_dataclass(row):
                had_dataclasses = True
                result.append([str(getattr(row, attr)) for attr in row.__dataclass_fields__])
            if isinstance(row, str):
                result.append(row)
            elif isinstance(row, list):
                result.append([str(cell) for cell in row])

        if had_dataclasses and self.header is None:
            self.header = list(row.__dataclass_fields__.keys())
        self.rows = result

    def __str__(self) -> str:
        parsed_settings = self.parse_extra_settings(**self.extra_settings)
        rows = "\n".join(f"<tr>{''.join(f'<td>{cell}</td>' for cell in row)}</tr>"
                         for row in self.rows)
        header = "" if not self.header else f"<thead><tr>{''.join(f'<th>{cell}</th>' for cell in self.header)}</tr></thead>"
        return f"<table {parsed_settings}>{header}{rows}</table>"


@dataclass
class Text(PageContent):
    body: str
    extra_settings: dict

    def __init__(self, body: str, **kwargs):
        self.body = body
        if 'body' in kwargs:
            self.body = kwargs.pop('content')
        if 'extra_settings' in kwargs:
            self.extra_settings = kwargs.pop('extra_settings')
            self.extra_settings.update(kwargs)
        else:
            self.extra_settings = kwargs

    def __eq__(self, other):
        if isinstance(other, Text):
            return (self.body == other.body and
                    self.extra_settings == other.extra_settings)
        elif isinstance(other, str):
            return self.extra_settings == {} and self.body == other
        return NotImplemented

    def __hash__(self):
        if self.extra_settings:
            items = tuple(sorted(self.extra_settings.items()))
            return hash((self.body, items))
        else:
            return hash(self.body)

    def __repr__(self):
        if self.extra_settings:
            return f"Text({self.body!r}, {self.extra_settings})"
        return f"Text({self.body!r})"



    def __str__(self):
        parsed_settings = self.parse_extra_settings(**self.extra_settings)
        if not parsed_settings:
            return self.body
        return f"<span {parsed_settings}>{self.body}</span>"


@dataclass
class MatPlotLibPlot(PageContent):
    extra_matplotlib_settings: dict
    close_automatically: bool

    def __init__(self, extra_matplotlib_settings=None, close_automatically=True, **kwargs):
        if not _has_matplotlib:
            raise ImportError("Matplotlib is not installed. Please install it to use this feature.")
        if extra_matplotlib_settings is None:
            extra_matplotlib_settings = {}
        self.extra_matplotlib_settings = extra_matplotlib_settings
        self.extra_settings = kwargs
        if "format" not in extra_matplotlib_settings:
            extra_matplotlib_settings["format"] = "png"
        if "bbox_inches" not in extra_matplotlib_settings:
            extra_matplotlib_settings["bbox_inches"] = "tight"
        self.close_automatically = close_automatically

    def __str__(self):
        parsed_settings = self.parse_extra_settings(**self.extra_settings)
        # Handle image processing
        image_data = io.BytesIO()
        plt.savefig(image_data, **self.extra_matplotlib_settings)
        if self.close_automatically:
            plt.close()
        image_data.seek(0)
        if self.extra_matplotlib_settings["format"] == "png":
            figure = base64.b64encode(image_data.getvalue()).decode('utf-8')
            figure = f"data:image/png;base64,{figure}"
            return f"<img src='{figure}' {parsed_settings}/>"
        elif self.extra_matplotlib_settings["format"] == "svg":
            figure = image_data.read().decode()
            return figure
        else:
            raise ValueError(f"Unsupported format {self.extra_matplotlib_settings['format']}")


@dataclass
class Download(PageContent):
    text: str
    filename: str
    content: str
    content_type: str = "text/plain"

    def __init__(self, text: str, filename: str, content: str, content_type: str = "text/plain"):
        self.text = text
        self.filename = filename
        self.content = content
        self.content_type = content_type

    def _handle_pil_image(self, image):
        if not HAS_PILLOW or isinstance(image, str):
            return False, image

        image_data = io.BytesIO()
        image.save(image_data, format="PNG")
        image_data.seek(0)
        figure = base64.b64encode(image_data.getvalue()).decode('utf-8')
        figure = f"data:image/png;base64,{figure}"
        return True, figure

    def __str__(self):
        was_pil, url = self._handle_pil_image(self.content)
        if was_pil:
            return f'<a download="{self.filename}" href="{url}">{self.text}</a>'
        return f'<a download="{self.filename}" href="data:{self.content_type},{self.content}">{self.text}</a>'


@dataclass
class FileUpload(PageContent):
    """
    A file upload component that allows users to upload files to the server.

    This works by creating a hidden input field that stores the file data as a JSON string.
    That input is sent, but the file data is not sent directly.

    The accept field can be used to specify the types of files that can be uploaded.
    It accepts either a literal string (e.g. "image/*") or a list of strings (e.g. ["image/png", "image/jpeg"]).
    You can either provide MIME types, extensions, or extensions without a period (e.g., "png", ".jpg").

    To have multiple files uploaded, use the `multiple` attribute, which will cause
    the corresponding parameter to be a list of files.
    """
    name: str
    EXTRA_ATTRS = ["accept", "capture", "multiple", "required"]

    def __init__(self, name: str, accept: Union[str, List[str], None] = None, **kwargs):
        validate_parameter_name(name, "FileUpload")
        self.name = name
        self.extra_settings = kwargs

        # Parse accept options
        if accept is not None:
            if isinstance(accept, str):
                accept = [accept]
            accept= [f".{ext}" if "/" not in ext and not ext.startswith(".") else ext
                     for ext in accept]
            self.extra_settings['accept'] = ", ".join(accept)

    def __str__(self):
        parsed_settings = self.parse_extra_settings(**self.extra_settings)
        return f"<input type='file' name={self.name!r} {parsed_settings} />"
