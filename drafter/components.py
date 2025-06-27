from dataclasses import dataclass, is_dataclass, fields
from typing import TYPE_CHECKING, Any, Self, TypeAlias, Union, Optional, List, Dict, Tuple
import io
import base64
# from urllib.parse import quote_plus
import json
import html

from drafter.configuration import ServerConfiguration
from drafter.constants import LABEL_SEPARATOR, SUBMIT_BUTTON_KEY, JSON_DECODE_SYMBOL
from drafter.urls import remap_attr_styles, friendly_urls, check_invalid_external_url, merge_url_query_params
from drafter.image_support import HAS_PILLOW, PILImage
from drafter.history import safe_repr

try:
    import matplotlib.pyplot as plt
    _has_matplotlib = True
except ImportError:
    _has_matplotlib = False

if TYPE_CHECKING:
    from _typeshed import DataclassInstance
    from drafter.server import Server


BASELINE_ATTRS = ["id", "class", "style", "title", "lang", "dir", "accesskey", "tabindex", "value",
                  "onclick", "ondblclick", "onmousedown", "onmouseup", "onmouseover", "onmousemove", "onmouseout",
                  "onkeypress", "onkeydown", "onkeyup",
                  "onfocus", "onblur", "onselect", "onchange", "onsubmit", "onreset", "onabort", "onerror", "onload",
                  "onunload", "onresize", "onscroll"]


BASE_PARAMETER_ERROR = ("""The {component_type} name must be a valid Python identifier name. A string is considered """
                        """a valid identifier if it only contains alphanumeric letters (a-z) and (0-9), or """
                        """underscores (_). A valid identifier cannot start with a number, or contain any spaces.""")

def validate_parameter_name(name: str, component_type: str) -> None:
    """
    Validates a parameter name to ensure it adheres to Python's identifier naming rules.
    The function verifies if the given name is a string, non-empty, does not contain spaces,
    does not start with a digit, and is a valid Python identifier. Additionally, it ensures
    the name starts with a letter or an underscore. Raises a `ValueError` with a detailed
    error message if validation fails.

    :param name: The name to validate.
    :type name: str
    :param component_type: Describes the type of component associated with the parameter.
    :type component_type: str
    :raises ValueError: If `name` is not a string, is empty, contains spaces, starts with a
        digit, does not start with a letter or underscore, or is not a valid identifier.
    """
    base_error = BASE_PARAMETER_ERROR.format(component_type=component_type)
    if not isinstance(name, str):
        raise ValueError(base_error + f"\n\nReason: The given name `{name!r}` is not a string.")
    if not name.isidentifier():
        if " " in name:
            raise ValueError(base_error + f"\n\nReason: The name `{name}` has a space, which is not allowed.")
        if not name:
            raise ValueError(base_error + f"\n\nReason: The name is an empty string.")
        if name[0].isdigit():
            raise ValueError(base_error + f"\n\nReason: The name `{name}` starts with a digit, which is not allowed.")
        if not name[0].isalpha() and name[0] != "_":
            raise ValueError(base_error + f"\n\nReason: The name `{name}` does not start with a letter or an underscore.")
        raise ValueError(base_error + f" The name `{name}` is not a valid Python identifier name.")


class PageContent:
    """
    Base class for all content that can be added to a page.
    This class is not meant to be used directly, but rather to be subclassed by other classes.
    Critically, each subclass must implement a ``__str__`` method that returns the HTML representation.

    Under most circumstances, a string value can be used in place of a ``PageContent`` object
    (in which case we say it is a ``Content`` type). However, the ``PageContent`` object
    allows for more customization and control over the content.

    Ultimately, the ``PageContent`` object is converted to a string when it is rendered.

    This class also has some helpful methods for verifying URLs and handling attributes/styles.
    """
    EXTRA_ATTRS: List[str] = []
    extra_settings: dict[str, Any]

    def verify(self, server: 'Server') -> bool:
        """
        Verify the status of this component. This method is called before rendering the component
        to ensure that the component is in a valid state. If the component is not valid, this method
        should return False.

        Default implementation returns True.

        :param server: The server object that is rendering the component
        :return: True if the component is valid, False otherwise
        """
        return True

    def parse_extra_settings(self, **kwargs: Any) -> str:
        """
        Parses and combines extra settings into valid attribute and style formats.

        This method processes additional configuration settings provided via arguments or stored
        in the `extra_settings` property, converts them into valid HTML attributes and styles,
        and then consolidates the processed values into the appropriate output format. Attributes
        not explicitly defined in the baseline or extra attribute lists are converted into inline
        style declarations.

        :param kwargs: Arbitrary keyword arguments containing extra configuration settings to be
            applied or overridden. The keys represent attribute or style names, and the values
            represent their corresponding values.
        :return: A string containing formatted HTML attributes along with an inline style block
            if any styles are provided.
        :rtype: str
        """
        extra_settings = self.extra_settings.copy()
        extra_settings.update(kwargs)
        raw_styles, raw_attrs = remap_attr_styles(extra_settings)
        styles, attrs = [], []
        for key, value in raw_attrs.items():
            if key not in self.EXTRA_ATTRS and key not in BASELINE_ATTRS:
                styles.append(f"{key}: {value}")
            else:
                # TODO: Is this safe enough?
                attrs.append(f"{key}={str(value)!r}")
        for key, value in raw_styles.items():
            styles.append(f"{key}: {value}")
        result = " ".join(attrs)
        if styles:
            result += f" style='{'; '.join(styles)}'"
        return result

    def update_style(self, style: str, value: Any) -> Self:
        """
        Updates the style of a specific setting and stores it in the
        extra_settings dictionary with a key formatted as "style_{style}".

        :param style: The key representing the style to be updated
        :type style: str
        :param value: The value to associate with the given style key
        :type value: Any
        :return: Returns the instance of the object after updating the style
        :rtype: self
        """
        self.extra_settings[f"style_{style}"] = value
        return self

    def update_attr(self, attr: str, value: Any) -> Self:
        """
        Updates a specific attribute with the given value in the extra_settings dictionary.

        This method modifies the `extra_settings` dictionary by setting the specified
        attribute to the given value. It returns the instance of the object, allowing
        for method chaining. No validation is performed on the input values, so they
        should conform to the expected structure or constraints of the `extra_settings`.

        :param attr: The key of the attribute to be updated in the dictionary.
        :type attr: str
        :param value: The value to set for the specified key in the dictionary.
        :type value: Any
        :return: The instance of the object after the update.
        :rtype: Self
        """
        self.extra_settings[attr] = value
        return self

    def render(self, current_state: Any, configuration: ServerConfiguration) -> str:
        """
        This method is called when the component is being rendered to a string. It should return
        the HTML representation of the component, using the current State and configuration to
        determine the final output.

        :param current_state: The current state of the component
        :type current_state: Any
        :param configuration: The configuration settings for the component
        :type configuration: Configuration
        :return: The HTML representation of the component
        """
        return str(self)


Content: TypeAlias = Union[PageContent, str]

def make_safe_json_argument(value: Any) -> str:
    """
    Converts the given value to a JSON-compatible string and escapes special
    HTML characters, making it safe for inclusion in HTML contexts.

    :param value: The input value to be converted and escaped. The value can
        be of any type that is serializable to JSON.
    :return: An HTML-safe JSON string representation of the input value.
    """
    return html.escape(json.dumps(value), True)

def make_safe_argument(value: Any) -> str:
    """
    Encodes the given value into JSON format and escapes any special HTML
    characters to ensure the argument is safe for use in HTML contexts.

    This function is particularly useful in scenarios where you need
    to serialize a Python object into JSON, while making sure that the
    output is safe to insert into an HTML document, protecting against
    potential HTML injection attacks.

    :param value: Any Python object that needs to be converted to a
        JSON string and HTML escaped.
    :type value: Any
    :return: A string containing the HTML-escaped and JSON-encoded
        representation of the input value.
    :rtype: str
    """
    return html.escape(json.dumps(value), True)

def make_safe_name(value: Any) -> str:
    """
    This function takes a value as input and generates a safe string version of it by escaping
    special characters to prevent injection attacks or unintended HTML rendering. It ensures that
    the provided input is safely transformed into an escaped HTML string.

    :param value: The input value to be escaped. It is converted to a string if it is not already.
    :type value: Any
    :return: The escaped HTML version of the input value as a string.
    :rtype: str
    """
    return html.escape(str(value))


class LinkContent:
    """
    Represents content for a hyperlink.

    This class encapsulates the URL and display text of a link.
    It provides utility methods for verifying the URL, handling its structure,
    and processing associated arguments.

    :ivar url: The URL of the link.
    :type url: str
    :ivar text: The display text of the link.
    :type text: str
    """
    url: str
    text: str

    def _handle_url(self, url, external=None):
        if callable(url):
            url = url.__name__
        if external is None:
            external = check_invalid_external_url(url) != ""
        url = url if external else friendly_urls(url)
        return url, external

    def verify(self, server) -> bool:
        if self.url not in server._handle_route:
            invalid_external_url_reason = check_invalid_external_url(self.url)
            if invalid_external_url_reason == "is a valid external url":
                return True
            elif invalid_external_url_reason:
                raise ValueError(f"Link `{self.url}` is not a valid external url.\n{invalid_external_url_reason}.")
            raise ValueError(f"Link `{self.text}` points to non-existent page `{self.url}`.")
        return True



    def create_arguments(self, arguments, label_namespace):
        parameters = self.parse_arguments(arguments, label_namespace)
        if parameters:
            return "\n".join(f"<input type='hidden' name='{name}' value='{make_safe_json_argument(value)}' />"
                             for name, value in parameters.items())
        return ""

    def parse_arguments(self, arguments, label_namespace):
        if arguments is None:
            return {}
        if isinstance(arguments, dict):
            return arguments
        if isinstance(arguments, Argument):
            escaped_label_namespace = make_safe_argument(label_namespace)
            return {f"{escaped_label_namespace}{LABEL_SEPARATOR}{arguments.name}": arguments.value}
        if isinstance(arguments, list):
            result = {}
            escaped_label_namespace = make_safe_argument(label_namespace)
            for arg in arguments:
                if isinstance(arg, Argument):
                    arg, value = arg.name, arg.value
                else:
                    arg, value = arg
                result[f"{escaped_label_namespace}{LABEL_SEPARATOR}{arg}"] = value
            return result
        raise ValueError(f"Could not create arguments from the provided value: {arguments}")


@dataclass
class Argument(PageContent):
    name: str
    value: Any

    def __init__(self, name: str, value: Any, **kwargs):
        validate_parameter_name(name, "Argument")
        self.name = name
        if not isinstance(value, (str, int, float, bool)):
            raise ValueError(f"Argument values must be strings, integers, floats, or booleans. Found {type(value)}")
        self.value = value
        self.extra_settings = kwargs

    def __str__(self) -> str:
        value = make_safe_json_argument(self.value)
        return f"<input type='hidden' name='{JSON_DECODE_SYMBOL}{self.name}' value='{value}' {self.parse_extra_settings()} />"


@dataclass
class Link(PageContent, LinkContent):
    text: str
    url: str

    def __init__(self, text: str, url: str, arguments=None, **kwargs):
        self.text = text
        self.url, self.external = self._handle_url(url)
        self.extra_settings = kwargs
        self.arguments = arguments

    def __str__(self) -> str:
        precode = self.create_arguments(self.arguments, self.text)
        url = merge_url_query_params(self.url, {SUBMIT_BUTTON_KEY: self.text})
        return f"{precode}<a href='{url}' {self.parse_extra_settings()}>{self.text}</a>"


@dataclass
class Button(PageContent, LinkContent):
    text: str
    url: str
    arguments: List[Argument]
    external: bool = False

    def __init__(self, text: str, url: str, arguments=None, **kwargs):
        self.text = text
        self.url, self.external = self._handle_url(url)
        self.extra_settings = kwargs
        self.arguments = arguments

    def __repr__(self):
        if self.arguments:
            return f"Button(text={self.text!r}, url={self.url!r}, arguments={self.arguments!r})"
        return f"Button(text={self.text!r}, url={self.url!r})"

    def __str__(self) -> str:
        precode = self.create_arguments(self.arguments, self.text)
        url = merge_url_query_params(self.url, {SUBMIT_BUTTON_KEY: self.text})
        parsed_settings = self.parse_extra_settings(**self.extra_settings)
        value = make_safe_argument(self.text)
        return f"{precode}<button type='submit' name='{SUBMIT_BUTTON_KEY}' value='{value}' formaction='{url}' {parsed_settings}>{self.text}</button>"


SubmitButton = Button


BASE_IMAGE_FOLDER = "/__images"


@dataclass
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
    # rows: List[List[str]]

    def __init__(self, rows: Union[List[List[str]], 'DataclassInstance'], header: Optional[list[str]] = None, **kwargs) -> str:
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
        self.extra_settings = kwargs

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
