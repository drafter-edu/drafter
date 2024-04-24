"""
TODO: Finish these
- [ ] Fix external links (ExternalLink command?)
- [X] Client-side server mode
- [?] Other HTML components
- [ ] set_page_title(title), set_page_style(**attributes)
- [ ] Reset all button
- [X] Copy ALL unique tests button
- [X] Show all of the tests in a nice clean way
- [X] Make it trivial to copy the route history as tests
- [X] Show the current route in the debug information
- [X] classes keyword parameter
- [ ] Create styling functions
- [ ] Make it so you can remove the frame and deploy this more easily
- [ ] Optional bootstrap support
- [ ] Swappable backends
- [ ] Text is equal to strings?

Components to develop:
- [x] Image
- [x] Table
- [X] Link
- [X] Button
- [ ] Markdown
- [X] Textbox
- [X] SelectBox
- [ ] RadioButtons
- [X] CheckBox
- [ ] Paragraph
- [X] BulletList (UnorderedList)
- [X] NumberedList (OrderedList)
- [X] Unordered
- [X] LineBreak
- [X] HorizontalRule
- [ ] PreformattedText
- [X] Header
- [X] TextArea
"""
import sys
import json
from typing import Any
from urllib.parse import urlencode, urlparse, parse_qs, quote_plus
import traceback
import inspect
import re
from functools import wraps
from dataclasses import dataclass, is_dataclass, replace, asdict, fields
from dataclasses import field as dataclass_field
import logging
from datetime import datetime
import pprint
import gzip
import base64
import difflib

logger = logging.getLogger('drafter')

try:
    from bottle import Bottle, abort, request, static_file

    DEFAULT_BACKEND = "bottle"
except ImportError:
    DEFAULT_BACKEND = "none"
    logger.warn("Bottle unavailable; backend will be disabled and run in test-only mode.")

__version__ = '1.0.5'

RESTORABLE_STATE_KEY = "--restorable-state"
SUBMIT_BUTTON_KEY = '--submit-button'
PREVIOUSLY_PRESSED_BUTTON = "--last-button"
LABEL_SEPARATOR = "$@~@$"

try:
    import bakery
except:
    bakery = None


@dataclass
class BakeryTestCase:
    args: tuple
    kwargs: dict
    result: Any
    line: int
    caller: str


def get_line_code(depth = 5):
    # Load in extract_stack, or provide shim for environments without it.
    try:
        from traceback import extract_stack
        trace = extract_stack()
        frame = trace[len(trace) - depth]
        line = frame[1]
        code = frame[3]
        return line, code
    except Exception:
        return None, None


class BakeryTests:
    def __init__(self):
        self.tests = []

    def wrap_get_line_code(self, original_function):
        @wraps(original_function)
        def new_function(*args, **kwargs):
            # line, code = original_function(*args, **kwargs)
            # return line, code
            return get_line_code()
        return new_function

    def track_bakery_tests(self, original_function):
        if bakery is None:
            return original_function
        @wraps(original_function)
        def new_function(*args, **kwargs):
            line, code = get_line_code(6)
            result = original_function(*args, **kwargs)
            self.tests.append(BakeryTestCase(args, kwargs, result, line, code))
            return result

        return new_function


# Modifies Bakery's copy of assert_equal, and also provides a new version for folks who already imported
_bakery_tests = BakeryTests()
if bakery is not None:
    bakery.assertions.get_line_code = _bakery_tests.wrap_get_line_code(bakery.assertions.get_line_code)
    assert_equal = bakery.assert_equal = _bakery_tests.track_bakery_tests(bakery.assert_equal)
else:
    def assert_equal(*args, **kwargs):
        """ Pointless definition of assert_equal to avoid errors """


DIFF_INDENT_WIDTH = 1
DIFF_WRAP_WIDTH = 60
DIFF_STYLE_TAG = """
<style type="text/css">
    table.diff {
        font-family:Courier,serif;
        border:medium;
        margin-bottom: 4em;
        width: 100%;
    }
    .diff_header {background-color:#e0e0e0}
    td.diff_header { text-align:right; }
    table.diff td {
        padding: 0px;
        border-bottom: 0px solid black;
    }
    .diff_next {background-color:#c0c0c0}
    .diff_add {background-color:#aaffaa}
    .diff_chg {background-color:#ffff77}
    .diff_sub {background-color:#ffaaaa}
</style>
"""
differ = difflib.HtmlDiff(tabsize=DIFF_INDENT_WIDTH, wrapcolumn=DIFF_WRAP_WIDTH)

def diff_tests(left, right, left_name, right_name):
    """ Compare two strings and show the differences in a table. """
    try:
        table = differ.make_table(left.splitlines(), right.splitlines(), left_name, right_name)
        return table
    except:
        if left == right:
            return "No differences found."
        return f"<pre>{left}</pre><pre>{right}</pre>"

def merge_url_query_params(url: str, additional_params: dict) -> str:
    """
    https://stackoverflow.com/a/52373377

    :param url:
    :param additional_params:
    :return:
    """
    url_components = urlparse(url)
    original_params = parse_qs(url_components.query, keep_blank_values=True)
    merged_params = dict(**original_params)
    merged_params.update(**additional_params)
    updated_query = urlencode(merged_params, doseq=True)
    return url_components._replace(query=updated_query).geturl()


def remove_url_query_params(url: str, params_to_remove: set) -> str:
    url_components = urlparse(url)
    original_params = parse_qs(url_components.query, keep_blank_values=True)
    merged_params = {k: v for k, v in original_params.items() if k not in params_to_remove}
    updated_query = urlencode(merged_params, doseq=True)
    return url_components._replace(query=updated_query).geturl()


def remap_attr_styles(attributes: dict) -> tuple[dict, dict]:
    styles, attrs = {}, {}
    # Handle classes keyword
    if 'classes' in attributes:
        attributes['class'] = attributes.pop('classes')
        if isinstance(attributes['class'], list):
            attributes['class'] = " ".join(attributes['class'])
    # Handle styles_ prefixed keyword
    for key, value in attributes.items():
        target = attrs
        if key.startswith("style_"):
            key = key[len("style_"):]
            target = styles
        key = key.replace("_", "-")
        target[key] = value
    # All done
    return styles, attrs


def _hijack_bottle():
    def _stderr(*args):
        try:
            if args:
                first_arg = str(args[0])
                if first_arg.startswith("Bottle v") and "server starting up" in first_arg:
                    args = list(args)
                    args[0] = "Drafter server starting up (using Bottle backend)."
            print(*args, file=sys.stderr)
        except (IOError, AttributeError):
            pass

    try:
        import bottle
        bottle._stderr = _stderr
    except ImportError:
        pass


_hijack_bottle()


@dataclass
class Page:
    state: Any
    content: list

    def __init__(self, state, content=None):
        if content is None:
            state, content = None, state
        self.state = state
        self.content = content

        if not isinstance(content, list):
            incorrect_type = type(content).__name__
            raise ValueError("The content of a page must be a list of strings or components."
                             f" Found {incorrect_type} instead.")
        else:
            for index, chunk in enumerate(content):
                if not isinstance(chunk, (str, PageContent)):
                    incorrect_type = type(chunk).__name__
                    raise ValueError("The content of a page must be a list of strings or components."
                                     f" Found {incorrect_type} at index {index} instead.")

    def render_content(self, current_state) -> str:
        # TODO: Decide if we want to dump state on the page
        chunked = [
            # f'<input type="hidden" name="{RESTORABLE_STATE_KEY}" value={current_state!r}/>'
        ]
        for chunk in self.content:
            if isinstance(chunk, str):
                chunked.append(f"<p>{chunk}</p>")
            else:
                chunked.append(str(chunk))
        content = "\n".join(chunked)
        return (f"<div class='container btlw-header'>Drafter Website</div>"
                f"<div class='container btlw-container'>"
                f"<form>{content}</form>"
                f"</div>")

    def verify_content(self, server) -> bool:
        for chunk in self.content:
            if isinstance(chunk, Link):
                chunk.verify(server)
        return True


BASELINE_ATTRS = ["id", "class", "style", "title", "lang", "dir", "accesskey", "tabindex", "value",
                  "onclick", "ondblclick", "onmousedown", "onmouseup", "onmouseover", "onmousemove", "onmouseout",
                  "onkeypress", "onkeydown", "onkeyup",
                  "onfocus", "onblur", "onselect", "onchange", "onsubmit", "onreset", "onabort", "onerror", "onload",
                  "onunload", "onresize", "onscroll"]


class PageContent:
    EXTRA_ATTRS = []
    extra_settings: dict

    def verify(self, server) -> bool:
        return True

    def parse_extra_settings(self, **kwargs):
        extra_settings = self.extra_settings.copy()
        extra_settings.update(kwargs)
        raw_styles, raw_attrs = remap_attr_styles(extra_settings)
        styles, attrs = [], []
        for key, value in raw_attrs.items():
            if key not in self.EXTRA_ATTRS and key not in BASELINE_ATTRS:
                styles.append(f"{key}: {value}")
            else:
                attrs.append(f"{key}={str(value)!r}")
        for key, value in raw_styles.items():
            styles.append(f"{key}: {value}")
        result = " ".join(attrs)
        if styles:
            result += f" style='{'; '.join(styles)}'"
        return result

    def update_style(self, style, value):
        self.extra_settings[f"style_{style}"] = value
        return self

    def update_attr(self, attr, value):
        self.extra_settings[attr] = value
        return self


class LinkContent:
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
            return "\n".join(f"<input type='hidden' name='{name}' value='{quote_plus(str(value))}' />"
                             for name, value in parameters.items())
        return ""

    def parse_arguments(self, arguments, label_namespace):
        if arguments is None:
            return {}
        if isinstance(arguments, dict):
            return arguments
        if isinstance(arguments, Argument):
            return {f"{label_namespace}{LABEL_SEPARATOR}{arguments.name}": arguments.value}
        if isinstance(arguments, list):
            result = {}
            for arg in arguments:
                if isinstance(arg, Argument):
                    arg, value = arg.name, arg.value
                    result[arg.name] = arg.value
                else:
                    arg, value = arg
                result[f"{label_namespace}{LABEL_SEPARATOR}{arg}"] = value
        raise ValueError(f"Could not create arguments from the provided value: {arguments}")

URL_REGEX = r"^(?:http(s)?://)[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$"


def check_invalid_external_url(url: str) -> str:
    if url.startswith("file://"):
        return "The URL references a local file on your computer, not a file on a server."
    if re.match(URL_REGEX, url) is not None:
        return "is a valid external url"
    return ""

BASIC_SCRIPTS = "<script>" + """
    let snippets = document.getElementsByClassName('copyable');
    const buttonText = "📋";
    console.log(snippets);
    for (let i = 0; i < snippets.length; i++) {
        code = snippets[i].textContent;
        //snippets[i].classList.add('hljs'); // append copy button to pre tag
        snippets[i].innerHTML = '<button class="copy-button">'+buttonText+'</button>' + snippets[i].innerHTML; // append copy button
        snippets[i].getElementsByClassName("copy-button")[0].addEventListener("click", function () {
            this.innerText = 'Copying..';
            navigator.clipboard.writeText(code);
            this.innerText = 'Copied!';
            button = this;
            setTimeout(function () {
                button.innerText = buttonText;
            }, 1000)
        });
    }
""" + "</script>"
BASIC_STYLE = """
<style>
    div.btlw-debug .copy-button {
         float: right;
         cursor: pointer;
         background-color: white;
         padding: 4px;
     }

    div.btlw-container {
        padding: 1em;
        border: 1px solid lightgrey;
    }
    
    div.btlw-header {
        border: 1px solid lightgrey;
        border-bottom: 0px;
        background-color: #EEE;
        padding-left: 1em;
        font-weight: bold;
    }
    
    div.btlw-container img {
        display: block;
    }
</style>
"""
SKELETON_COMPRESSED = "<style>" + gzip.decompress(base64.b64decode(
    "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")).decode('utf-8') + "</style>"

INCLUDE_STYLES = {
    'bootstrap': {
        'styles': [
            BASIC_STYLE,
            '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" integrity="sha384-rbsA2VBKQhggwzxH7pPCaAqO46MgnOM80zW1RWuH61DGLwZJEdK2Kadq2F9CUG65" crossorigin="anonymous">',
            DIFF_STYLE_TAG,
        ],
        'scripts': [
            '<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-kenU1KFdBIe4zVF0s0G1M5b4hcpxyD9F7jL+jjXkk+Q2h455rYXK/7HAuoJl+0I4" crossorigin="anonymous"></script>',
            '<script src="https://code.jquery.com/jquery-3.7.1.slim.min.js" integrity="sha256-kmHvs0B+OpCW5GVHUNjv9rOmY0IvSIRcf7zGUDTDQM8=" crossorigin="anonymous"></script>',
            BASIC_SCRIPTS,
        ]
    },
    "skeleton": {
        "styles": [
            SKELETON_COMPRESSED,
            BASIC_STYLE,
            DIFF_STYLE_TAG,
        ],
        "scripts": [BASIC_SCRIPTS,]
    },
    "skeleton_cdn": {
        "styles": [
            BASIC_STYLE,
            '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/skeleton/2.0.4/skeleton.min.css" integrity="sha512-EZLkOqwILORob+p0BXZc+Vm3RgJBOe1Iq/0fiI7r/wJgzOFZMlsqTa29UEl6v6U6gsV4uIpsNZoV32YZqrCRCQ==" crossorigin="anonymous" referrerpolicy="no-referrer" />',
            DIFF_STYLE_TAG,
        ],
        "scripts": [BASIC_SCRIPTS,]
    },
    'none': {
        'styles': [BASIC_STYLE, DIFF_STYLE_TAG],
        'scripts': [BASIC_SCRIPTS,]
    }
}

TEMPLATE_200 = """
"""
TEMPLATE_404 = """
<style type="text/css">
  .btlw {{background-color: #eee; font-family: sans-serif;}}
  div.btlw {{background-color: #fff; border: 1px solid #ddd;
        padding: 15px; margin: 15px;}}
  .btlw pre {{background-color: #eee; border: 1px solid #ddd; padding: 5px;}}
</style>
<h3>{title}</h3>

<p>{message}</p>

<p>Original error message:</p>
<pre>{error}</pre>

<p>Available routes:</p>
{routes}
"""
TEMPLATE_500 = """
<style type="text/css">
  .btlw {{background-color: #eee; font-family: sans-serif;}}
  div.btlw {{background-color: #fff; border: 1px solid #ddd;
        padding: 15px; margin: 15px;}}
  .btlw pre {{background-color: #eee; border: 1px solid #ddd; padding: 5px;}}
</style>
<h3>{title}</h3>

<p>{message}</p>

<p>Original error message:</p>
<pre>{error}</pre>

<p>Available routes:</p>
{routes}
"""


@dataclass
class Argument(PageContent):
    name: str
    value: Any

    def __init__(self, name: str, value: Any, **kwargs):
        self.name = name
        if not isinstance(value, (str, int, float, bool)):
            raise ValueError(f"Argument values must be strings, integers, floats, or booleans. Found {type(value)}")
        self.value = value
        self.extra_settings = kwargs

    def __str__(self) -> str:
        value = quote_plus(self.value)
        return f"<input type='hidden' name='{self.name}' value='{value}' {self.parse_extra_settings()} />"


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

    def __str__(self) -> str:
        extra_settings = {}
        if self.width is not None:
            extra_settings['width'] = self.width
        if self.height is not None:
            extra_settings['height'] = self.height
        url, external = self._handle_url(self.url)
        if not external:
            url = BASE_IMAGE_FOLDER + url
        parsed_settings = self.parse_extra_settings(**extra_settings)
        return f"<img src='{url}' {parsed_settings}>"


@dataclass
class TextBox(PageContent):
    name: str
    kind: str
    default_value: str

    def __init__(self, name: str, default_value: str = None, kind: str = "text", **kwargs):
        self.name = name
        self.kind = kind
        self.default_value = default_value
        self.extra_settings = kwargs

    def __str__(self) -> str:
        extra_settings = {}
        if self.default_value is not None:
            extra_settings['value'] = self.default_value
        parsed_settings = self.parse_extra_settings(**extra_settings)
        return f"<input type='{self.kind}' name='{self.name}' {parsed_settings}>"


@dataclass
class TextArea(PageContent):
    name: str
    default_value: str
    EXTRA_ATTRS = ["rows", "cols", "autocomplete", "autofocus", "disabled", "placeholder", "readonly", "required"]

    def __init__(self, name: str, default_value: str = None, **kwargs):
        self.name = name
        self.default_value = default_value
        self.extra_settings = kwargs

    def __str__(self) -> str:
        parsed_settings = self.parse_extra_settings(**self.extra_settings)
        return f"<textarea name='{self.name}' {parsed_settings}>{self.default_value}</textarea>"


@dataclass
class SelectBox(PageContent):
    name: str
    options: list[str]
    default_value: str

    def __init__(self, name: str, options: list[str], default_value: str = None, **kwargs):
        self.name = name
        self.options = options
        self.default_value = default_value
        self.extra_settings = kwargs

    def __str__(self) -> str:
        extra_settings = {}
        if self.default_value is not None:
            extra_settings['value'] = self.default_value
        parsed_settings = self.parse_extra_settings(**extra_settings)
        options = "\n".join(f"<option selected value='{option}'>{option}</option>"
                            if option == self.default_value else
                            f"<option value='{option}'>{option}</option>"
                            for option in self.options)
        return f"<select name='{self.name}' {parsed_settings}>{options}</select>"


@dataclass
class CheckBox(PageContent):
    EXTRA_ATTRS = ["checked"]
    name: str
    default_value: bool

    def __init__(self, name: str, default_value: bool = False, **kwargs):
        self.name = name
        self.default_value = default_value
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


@dataclass
class Span(PageContent):
    def __init__(self, *args):
        self.content = args

    def __str__(self) -> str:
        return f"<span>{''.join(str(item) for item in self.content)}</span>"


@dataclass
class Button(PageContent, LinkContent):
    text: str
    url: str
    arguments: list[Argument]
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
        return f"{precode}<input type='submit' name='{SUBMIT_BUTTON_KEY}' value='{self.text}' formaction='{url}' {parsed_settings} />"


@dataclass
class _HtmlList(PageContent):
    items: list[Any]
    kind: str = ""

    def __init__(self, items: list[Any], **kwargs):
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
    rows: list[list[str]]

    def __init__(self, rows: list[list[str]], header=None, **kwargs):
        self.rows = rows
        self.header = header
        self.extra_settings = kwargs
        self.reformat_as_tabular()

    def reformat_as_single(self):
        result = []
        for field in fields(self.rows):
            value = getattr(self.rows, field.name)
            result.append(
                [f"<code>{field.name}</code>", f"<code>{field.type.__name__}</code>", f"<code>{value!r}</code>"])
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


class Text(PageContent):
    body: str

    def __init__(self, body: str):
        self.body = body

    def __str__(self):
        return self.body


def friendly_urls(url: str) -> str:
    if url.strip("/") == "index":
        return "/"
    if not url.startswith('/'):
        url = '/' + url
    return url


def update_style(component, style, value):
    if isinstance(component, str):
        component = Text(component)
    return component.update_style(style, value)


def update_attr(component, attr, value):
    if isinstance(component, str):
        component = Text(component)
    return component.update_attr(attr, value)


"""
TODO:
- [ ] indent
- [ ] center
- [ ] Superscript, subscript
- [ ] border/margin/padding (all sides)
"""


def float_right(component: PageContent) -> PageContent:
    return update_style(component, 'float', 'right')


def float_left(component: PageContent) -> PageContent:
    return update_style(component, 'float', 'left')


def bold(component: PageContent) -> PageContent:
    return update_style(component, 'font-weight', 'bold')


def italic(component: PageContent) -> PageContent:
    return update_style(component, 'font-style', 'italic')


def underline(component: PageContent) -> PageContent:
    return update_style(component, 'text-decoration', 'underline')


def strikethrough(component: PageContent) -> PageContent:
    return update_style(component, 'text-decoration', 'line-through')


def monospace(component: PageContent) -> PageContent:
    return update_style(component, 'font-family', 'monospace')


def small_font(component: PageContent) -> PageContent:
    return update_style(component, 'font-size', 'small')


def large_font(component: PageContent) -> PageContent:
    return update_style(component, 'font-size', 'large')


def change_color(component: PageContent, c: str) -> PageContent:
    return update_style(component, 'color', c)


def change_background_color(component: PageContent, color: str) -> PageContent:
    return update_style(component, 'background-color', color)


def change_text_size(component: PageContent, size: str) -> PageContent:
    return update_style(component, 'font-size', size)


def change_text_font(component: PageContent, font: str) -> PageContent:
    return update_style(component, 'font-family', font)


def change_text_align(component: PageContent, align: str) -> PageContent:
    return update_style(component, 'text-align', align)


def change_text_decoration(component: PageContent, decoration: str) -> PageContent:
    return update_style(component, 'text-decoration', decoration)


def change_text_transform(component: PageContent, transform: str) -> PageContent:
    return update_style(component, 'text-transform', transform)


def change_height(component: PageContent, height: str) -> PageContent:
    return update_style(component, 'height', height)


def change_width(component: PageContent, width: str) -> PageContent:
    return update_style(component, 'width', width)


def change_border(component: PageContent, border: str) -> PageContent:
    return update_style(component, 'border', border)


def change_margin(component: PageContent, margin: str) -> PageContent:
    return update_style(component, 'margin', margin)


def change_padding(component: PageContent, padding: str) -> PageContent:
    return update_style(component, 'padding', padding)


@dataclass
class ServerConfiguration:
    host: str = "localhost"
    port: int = 8080
    debug: bool = True
    # "none", "flask", etc.
    backend: str = DEFAULT_BACKEND
    reloader: bool = False
    style: str = 'skeleton'


@dataclass
class ConversionRecord:
    parameter: str
    value: Any
    expected_type: Any
    converted_value: Any

    def as_html(self):
        return (f"<li><code>{self.parameter}</code>: "
                f"<code>{self.value!r}</code> &rarr; "
                f"<code>{self.converted_value!r}</code></li>")

@dataclass
class UnchangedRecord:
    parameter: str
    value: Any
    expected_type: Any = None

    def as_html(self):
        return (f"<li><code>{self.parameter}</code>: "
                f"<code>{self.value!r}</code></li>")

def format_page_content(content, width=80):
    try:
        return pprint.pformat(content, indent=DIFF_INDENT_WIDTH, width=width)
    except Exception as e:
        return repr(content)


def remap_hidden_form_parameters(kwargs: dict, button_pressed: str):
    renamed_kwargs = {}
    for key, value in kwargs.items():
        if button_pressed and key.startswith(f"{button_pressed}{LABEL_SEPARATOR}"):
            key = key[len(f"{button_pressed}{LABEL_SEPARATOR}"):]
            renamed_kwargs[key] = value
        elif LABEL_SEPARATOR not in key:
            renamed_kwargs[key] = value
    return renamed_kwargs


@dataclass
class VisitedPage:
    url: str
    function: callable
    arguments: str
    status: str
    button_pressed: str
    original_page_content: str = None
    old_state: Any = None
    started: datetime = dataclass_field(default_factory=datetime.utcnow)
    stopped: datetime = None

    def update(self, new_status, original_page_content=None):
        self.status = new_status
        if original_page_content is not None:
            self.original_page_content = format_page_content(original_page_content, 120)

    def finish(self, new_status):
        self.status = new_status
        self.stopped = datetime.utcnow()

    def as_html(self):
        function_name = self.function.__name__
        return (f"<strong>Current Route:</strong><br>Route function: <code>{function_name}</code><br>"
                f"URL: <href='{self.url}'><code>{self.url}</code></href>")


def dehydrate_json(value):
    if isinstance(value, (list, set, tuple)):
        return [dehydrate_json(v) for v in value]
    elif isinstance(value, dict):
        return {dehydrate_json(k): dehydrate_json(v) for k, v in value.items()}
    elif isinstance(value, (int, str, float, bool)) or value == None:
        return value
    elif is_dataclass(value):
        return {f.name: dehydrate_json(getattr(value, f.name))
                for f in fields(value)}
    raise ValueError(
        f"Error while serializing state: The {value!r} is not a int, str, float, bool, list, or dataclass.")


def rehydrate_json(value, new_type):
    if isinstance(value, list):
        if hasattr(new_type, '__args__'):
            element_type = new_type.__args__
            return [rehydrate_json(v, element_type) for v in value]
        elif hasattr(new_type, '__origin__') and getattr(new_type, '__origin__') == list:
            return value
    elif isinstance(value, (int, str, float, bool)) or value is None:
        # TODO: More validation that the structure is consistent; what if the target is not these?
        return value
    elif isinstance(value, dict):
        if hasattr(new_type, '__args__'):
            # TODO: Handle various kinds of dictionary types more intelligently
            # In particular, should be able to handle dict[int: str] (slicing) and dict[int, str]
            key_type, value_type = new_type.__args__
            return {rehydrate_json(k, key_type): rehydrate_json(v, value_type)
                    for k, v in value.items()}
        elif hasattr(new_type, '__origin__') and getattr(new_type, '__origin__') == dict:
            return value
        elif is_dataclass(new_type):
            converted = {f.name: rehydrate_json(value[f.name], f.type) if f.name in value else f.default
                         for f in fields(new_type)}
            return new_type(**converted)
    # Fall through if an error
    raise ValueError(f"Error while restoring state: Could not create {new_type!r} from {value!r}")


def get_params():
    if hasattr(request.params, 'decode'):
        return request.params.decode('utf-8')
    else:
        return request.params


class Server:
    _page_history: list[tuple[VisitedPage, Any]]

    def __init__(self, **kwargs):
        self.routes = {}
        self._handle_route = {}
        self.default_configuration = ServerConfiguration(**kwargs)
        self._state = None
        self._initial_state = None
        self._state_history = []
        self._state_frozen_history = []
        self._page_history = []
        self._conversion_record = []
        self.original_routes = []
        self.app = None
        self.image_folder = '__images'

    def reset(self):
        self.routes.clear()

    def dump_state(self):
        return json.dumps(dehydrate_json(self._state))

    def restore_state_if_available(self, original_function):
        params = get_params()
        if RESTORABLE_STATE_KEY in params:
            # Get state
            old_state = json.loads(params.pop(RESTORABLE_STATE_KEY))
            # Get state type
            parameters = inspect.signature(original_function).parameters
            if 'state' in parameters:
                state_type = parameters['state'].annotation
                self._state = rehydrate_json(old_state, state_type)
                self.flash_warning("Successfully restored old state: " + repr(self._state))

    def add_route(self, url, func):
        if url in self.routes:
            raise ValueError(f"URL `{url}` already exists for an existing routed function: `{func.__name__}`")
        self.original_routes.append((url, func))
        url = friendly_urls(url)
        func = self.make_bottle_page(func)
        self.routes[url] = func
        self._handle_route[url] = self._handle_route[func] = func

    def setup(self, initial_state=None):
        self._initial_state = initial_state
        self._state = initial_state
        self.app = Bottle()

        # Setup error pages
        def handle_404(error):
            message = "<p>The requested page <code>{url}</code> was not found.</p>".format(url=request.url)
            # TODO: Only show if not the index
            message += "\n<p>You might want to return to the <a href='/'>index</a> page.</p>"
            return TEMPLATE_404.format(title="404 Page not found", message=message,
                                       error=error.body,
                                       routes="\n".join(
                                           f"<li><code>{r!r}</code>: <code>{func}</code></li>" for r, func in
                                           self.original_routes))

        def handle_500(error):
            message = "<p>Sorry, the requested URL <code>{url}</code> caused an error.</p>".format(url=request.url)
            message += "\n<p>You might want to return to the <a href='/'>index</a> page.</p>"
            return TEMPLATE_500.format(title="500 Internal Server Error", message=message,
                                       error=error.body,
                                       routes="\n".join(
                                           f"<li><code>{r!r}</code>: <code>{func}</code></li>" for r, func in
                                           self.original_routes))

        self.app.error(404)(handle_404)
        self.app.error(500)(handle_500)
        # Setup routes
        if not self.routes:
            raise ValueError("No routes have been defined.\nDid you remember the @route decorator?")
        for url, func in self.routes.items():
            self.app.route(url, 'GET', func)
        if '/' not in self.routes:
            first_route = list(self.routes.values())[0]
            self.app.route('/', 'GET', first_route)
        self.handle_images()

    def run(self, **kwargs):
        configuration = replace(self.default_configuration, **kwargs)
        self.app.run(**asdict(configuration))

    def prepare_args(self, original_function, args, kwargs):
        self._conversion_record.clear()
        args = list(args)
        kwargs = dict(**kwargs)
        button_pressed = ""
        params = get_params()
        if SUBMIT_BUTTON_KEY in params:
            button_pressed = params.pop(SUBMIT_BUTTON_KEY)
        elif PREVIOUSLY_PRESSED_BUTTON in params:
            button_pressed = params.pop(PREVIOUSLY_PRESSED_BUTTON)
        # TODO: Handle non-bottle backends
        for key in list(params.keys()):
            kwargs[key] = params.pop(key)
        signature_parameters = inspect.signature(original_function).parameters
        expected_parameters = list(signature_parameters.keys())
        show_names = {param.name: (param.kind in (inspect.Parameter.KEYWORD_ONLY, inspect.Parameter.VAR_KEYWORD))
                      for param in signature_parameters.values()}
        kwargs = remap_hidden_form_parameters(kwargs, button_pressed)
        # Insert state into the beginning of args
        if (expected_parameters and expected_parameters[0] == "state") or (
                len(expected_parameters) - 1 == len(args) + len(kwargs)):
            args.insert(0, self._state)
        # Check if there are too many arguments
        if len(expected_parameters) < len(args) + len(kwargs):
            self.flash_warning(
                f"The {original_function.__name__} function expected {len(expected_parameters)} parameters, but {len(args) + len(kwargs)} were provided.\n"
                f"  Expected: {', '.join(expected_parameters)}\n"
                f"  But got: {repr(args)} and {repr(kwargs)}")
            # TODO: Select parameters to keep more intelligently by inspecting names
            args = args[:len(expected_parameters)]
            while len(expected_parameters) < len(args) + len(kwargs) and kwargs:
                kwargs.pop(list(kwargs.keys())[-1])
        # Type conversion if required
        expected_types = {name: p.annotation for name, p in
                          inspect.signature(original_function).parameters.items()}
        args = [self.convert_parameter(param, val, expected_types)
                for param, val in zip(expected_parameters, args)]
        kwargs = {param: self.convert_parameter(param, val, expected_types)
                  for param, val in kwargs.items()}
        # Verify all arguments are in expected_parameters
        for key, value in kwargs.items():
            if key not in expected_parameters:
                raise ValueError(
                    f"Unexpected parameter {key}={value!r} in {original_function.__name__}. "
                    f"Expected parameters: {expected_parameters}")
        # Final return result
        representation = [repr(arg) for arg in args] + [
            f"{key}={value!r}" if show_names.get(key, False) else repr(value)
            for key, value in sorted(kwargs.items(), key=lambda item: expected_parameters.index(item[0]))]
        return args, kwargs, ", ".join(representation), button_pressed

    def handle_images(self):
        self.app.route(f'/{self.image_folder}/<path:path>', 'GET', self.serve_image)

    def serve_image(self, path):
        return static_file(path, root='./', mimetype='image/png')

    def convert_parameter(self, param, val, expected_types):
        if param in expected_types:
            expected_type = expected_types[param]
            if expected_type == inspect.Parameter.empty:
                self._conversion_record.append(UnchangedRecord(param, val, expected_types[param]))
                return val
            if hasattr(expected_type, '__origin__'):
                # TODO: Ignoring the element type for now, but should really handle that properly
                expected_type = expected_type.__origin__
            if not isinstance(val, expected_type):
                try:
                    converted_arg = expected_types[param](val)
                    self._conversion_record.append(ConversionRecord(param, val, expected_types[param], converted_arg))
                except Exception as e:
                    try:
                        from_name = type(val).__name__
                        to_name = expected_types[param].__name__
                    except:
                        from_name = repr(type(val))
                        to_name = repr(expected_types[param])
                    raise ValueError(
                        f"Could not convert {param} ({val!r}) from {from_name} to {to_name}\n") from e
                return converted_arg
        # Fall through
        self._conversion_record.append(UnchangedRecord(param, val))
        return val

    def make_bottle_page(self, original_function):
        @wraps(original_function)
        def bottle_page(*args, **kwargs):
            # TODO: Handle non-bottle backends
            url = remove_url_query_params(request.url, {RESTORABLE_STATE_KEY, SUBMIT_BUTTON_KEY})
            self.restore_state_if_available(original_function)
            original_state = self.dump_state()
            try:
                args, kwargs, arguments, button_pressed = self.prepare_args(original_function, args, kwargs)
            except Exception as e:
                return self.make_error_page("Error preparing arguments for page", e, original_function)
            # Actually start building up the page
            visiting_page = VisitedPage(url, original_function, arguments, "Creating Page", button_pressed)
            self._page_history.append((visiting_page, original_state))
            try:
                page = original_function(*args, **kwargs)
            except Exception as e:
                return self.make_error_page("Error creating page", e, original_function)
            visiting_page.update("Verifying Page Result", original_page_content=page)
            verification_status = self.verify_page_result(page, original_function)
            if verification_status:
                return verification_status
            try:
                page.verify_content(self)
            except Exception as e:
                return self.make_error_page("Error verifying content", e, original_function)
            self._state_history.append(page.state)
            self._state = page.state
            visiting_page.update("Rendering Page Content")
            try:
                content = page.render_content(self.dump_state())
            except Exception as e:
                return self.make_error_page("Error rendering content", e, original_function)
            visiting_page.finish("Finished Page Load")
            if self.default_configuration.debug:
                content = content + self.make_debug_page()
            content = self.wrap_page(content)
            return content

        return bottle_page

    def verify_page_result(self, page, original_function):
        message = ""
        if page is None:
            message = (f"The server did not return a Page object from {original_function}.\n"
                       f"Instead, it returned None (which happens by default when you do not return anything else).\n"
                       f"Make sure you have a proper return statement for every branch!")
        elif isinstance(page, str):
            message = (
                f"The server did not return a Page() object from {original_function}. Instead, it returned a string:\n"
                f"  {page!r}\n"
                f"Make sure you are returning a Page object with the new state and a list of strings!")
        elif isinstance(page, list):
            message = (
                f"The server did not return a Page() object from {original_function}. Instead, it returned a list:\n"
                f" {page!r}\n"
                f"Make sure you return a Page object with the new state and the list of strings, not just the list of strings.")
        elif not isinstance(page, Page):
            message = (f"The server did not return a Page() object from {original_function}. Instead, it returned:\n"
                       f" {page!r}\n"
                       f"Make sure you return a Page object with the new state and the list of strings.")
        else:
            verification_status = self.verify_page_state_history(page, original_function)
            if verification_status:
                return verification_status
            elif isinstance(page.content, str):
                message = (f"The server did not return a valid Page() object from {original_function}.\n"
                           f"Instead of a list of strings or content objects, the content field was a string:\n"
                           f" {page.content!r}\n"
                           f"Make sure you return a Page object with the new state and the list of strings/content objects.")
            elif not isinstance(page.content, list):
                message = (
                    f"The server did not return a valid Page() object from {original_function}.\n"
                    f"Instead of a list of strings or content objects, the content field was:\n"
                    f" {page.content!r}\n"
                    f"Make sure you return a Page object with the new state and the list of strings/content objects.")
            else:
                for item in page.content:
                    if not isinstance(item, (str, PageContent)):
                        message = (
                            f"The server did not return a valid Page() object from {original_function}.\n"
                            f"Instead of a list of strings or content objects, the content field was:\n"
                            f" {page.content!r}\n"
                            f"One of those items is not a string or a content object. Instead, it was:\n"
                            f" {item!r}\n"
                            f"Make sure you return a Page object with the new state and the list of strings/content objects.")

        if message:
            return self.make_error_page("Error after creating page", ValueError(message), original_function)

    def verify_page_state_history(self, page, original_function):
        if not self._state_history:
            return
        message = ""
        last_type = self._state_history[-1].__class__
        if not isinstance(page.state, last_type):
            message = (
                f"The server did not return a valid Page() object from {original_function}. The state object's type changed from its previous type. The new value is:\n"
                f" {page.state!r}\n"
                f"The most recent value was:\n"
                f" {self._state_history[-1]!r}\n"
                f"The expected type was:\n"
                f" {last_type}\n"
                f"Make sure you return the same type each time.")
        # TODO: Typecheck each field
        if message:
            return self.make_error_page("Error after creating page", ValueError(message), original_function)

    def wrap_page(self, content):
        style = self.default_configuration.style
        if style in INCLUDE_STYLES:
            scripts = INCLUDE_STYLES[style]['scripts']
            styles = INCLUDE_STYLES[style]['styles']
            content = "\n".join(styles) + content + "\n".join(scripts)
        return "<div class='btlw'>" + content + "</div>"

    def make_error_page(self, title, error, original_function):
        tb = traceback.format_exc()
        new_message = f"{title}.\nError in {original_function.__name__}:\n{error}\n\n\n{tb}"
        abort(500, new_message)

    def flash_warning(self, message):
        print(message)

    def make_debug_page(self):
        content = DebugInformation(self._page_history, self._state, self.routes, self._conversion_record)
        return content.generate()


@dataclass
class DebugInformation:
    page_history: list[tuple[VisitedPage, Any]]
    state: Any
    routes: dict[str, callable]
    conversion_record: list[ConversionRecord]

    INDENTATION_START_HTML = "<div class='row'><div class='one column'></div><div class='eleven columns'>"
    INDENTATION_END_HTML = "</div></div>"

    def generate(self):
        parts = [
            "<div class='btlw-debug'>",
            "<h3>Debug Information</h3>",
            "<em>To hide this information, call <code>hide_debug_information()</code> in your code.</em><br>",
            *self.current_route(),
            *self.current_state(),
            *self.available_routes(),
            *self.page_load_history(),
            *self.test_status(),
            "</div>"
        ]
        return "\n".join(parts)

    def current_route(self):
        # Current route
        if not self.page_history:
            yield "Currently no pages have been successfully visited."
        else:
            yield self.page_history[-1][0].as_html()
        yield f"<br>"
        non_state_parameters = [record for record in self.conversion_record if record.parameter != 'state']
        if non_state_parameters:
            yield "<details open><summary><strong>Current parameter values:</strong></summary>"
            yield f"{self.INDENTATION_START_HTML}"
            yield f"<ul>"
            for record in self.conversion_record:
                if record.parameter != 'state':
                    yield record.as_html()
            yield f"</ul>{self.INDENTATION_END_HTML}</details>"
        else:
            yield "<strong>No parameters were provided.</strong>"

    def current_state(self):
        # Current State
        yield "<details open><summary><strong>Current State</strong></summary>"
        yield f"{self.INDENTATION_START_HTML}"
        if self.state is not None:
            yield self.render_state(self.state)
        else:
            yield "<code>None</code>"
        yield f"{self.INDENTATION_END_HTML}</details>"

    def available_routes(self):
        # Routes
        yield f"<details open><summary><strong>Available Routes</strong></summary>"
        yield f"{self.INDENTATION_START_HTML}"
        yield f"<ul>"
        for original_route, function in self.routes.items():
            parameter_list = inspect.signature(function).parameters.keys()
            parameters = ", ".join(parameter_list)
            if original_route != '/':
                original_route += '/'
            route = f"<code>{original_route}</code>"
            call = f"{function.__name__}({parameters})"
            if len(parameter_list) == 1:
                call = f"<a href='{original_route}'>{call}</a>"
            yield f"<li>{route}: <code>{call}</code></li>"
        yield f"</ul>{self.INDENTATION_END_HTML}</details>"

    def page_load_history(self):
        # Page History
        yield "<details open><summary><strong>Page Load History</strong></summary><ol>"
        all_visits = set()
        for page_history, old_state in reversed(self.page_history):
            button_pressed = f"Clicked <code>{page_history.button_pressed}</code> &rarr; " if page_history.button_pressed else ""
            url = merge_url_query_params(page_history.url, {
                RESTORABLE_STATE_KEY: old_state,
                PREVIOUSLY_PRESSED_BUTTON: page_history.button_pressed
            })
            yield f"<li>{button_pressed}{page_history.status}"  # <details><summary>
            yield f"{self.INDENTATION_START_HTML}"
            yield f"URL: <a href='{url}'><code>{page_history.url}/</code></a><br>"
            call = f"{page_history.function.__name__}({page_history.arguments})"
            yield f"Call: <code>{call}</code><br>"
            yield f"<details><summary>Page Content:</summary><pre style='width: fit-content' class='copyable'>"
            full_code = f"assert_equal(\n {call},\n {page_history.original_page_content})"
            all_visits.add(full_code)
            yield f"<code>{full_code}</code></pre></details>"
            yield f"{self.INDENTATION_END_HTML}"
            yield f"</li>"
        yield "</ol>"
        for part in self.copy_all_page_history(all_visits):
            yield part
        yield "</details>"

    def copy_all_page_history(self, all_visits):
        yield "<details><summary><strong>Combined Page History</strong></summary>"
        yield f"{self.INDENTATION_START_HTML}"
        yield "<pre style='width: fit-content' class='copyable'><code>" + "\n\n".join(all_visits) + "</code></pre>"
        yield f"{self.INDENTATION_END_HTML}"
        yield "</details>"

    def test_status(self):
        if bakery is None and _bakery_tests.tests:
            yield ""
        else:
            if _bakery_tests.tests:
                yield "<details open><summary><strong>Test Status</strong></summary>"
                yield f"{self.INDENTATION_START_HTML}"
                yield "<ul>"
                for test_case in _bakery_tests.tests:
                    if len(test_case.args) == 2:
                        given, expected = test_case.args
                        if not isinstance(expected, Page):
                            continue
                        # Status is either a checkmark or a red X
                        status = "✅" if test_case.result else "❌"
                        yield f"<li>{status} Line {test_case.line}: <code>{test_case.caller}</code>"
                        if not test_case.result:
                            given, expected = format_page_content(given, DIFF_WRAP_WIDTH), format_page_content(expected, DIFF_WRAP_WIDTH)
                            yield diff_tests(given, expected,
                                             "Your function returned",
                                             "But the test expected")
                yield "</ul>"
                yield f"{self.INDENTATION_END_HTML}"
                yield "</details>"
            else:
                yield "<strong>No Tests</strong>"

    def render_state(self, state):
        if is_dataclass(state):
            return str(Table(state))
        else:
            return str(Table([[f"<code>{type(state).__name__}</code>", f"<code>{state}</code>"]]))


MAIN_SERVER = Server()


def route(url: str = None, server: Server = MAIN_SERVER):
    if callable(url):
        local_url = url.__name__
        server.add_route(local_url, url)
        return url

    def make_route(func):
        local_url = url
        if url is None:
            local_url = func.__name__
        server.add_route(local_url, func)
        return func

    return make_route


def start_server(initial_state=None, server: Server = MAIN_SERVER, **kwargs):
    server.setup(initial_state)
    server.run(**kwargs)


def hide_debug_information():
    MAIN_SERVER.default_configuration.debug = False


def show_debug_information():
    MAIN_SERVER.default_configuration.debug = True


def default_index(state) -> Page:
    return Page(state, ["Hello world!", "Welcome to Drafter."])


def set_website_title(title: str):
    MAIN_SERVER.default_configuration.title = title

def set_website_style(style: str):
    MAIN_SERVER.default_configuration.custom_style = style


def deploy_site(image_folder='images'):
    hide_debug_information()
    MAIN_SERVER.production = True
    MAIN_SERVER.image_folder = image_folder


# Provide default route
route('index')(default_index)

if __name__ == '__main__':
    print("This package is meant to be imported, not run as a script. For now, at least.")
