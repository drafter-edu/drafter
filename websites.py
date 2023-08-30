"""
TODO: Finish these
- [ ] Optional bootstrap support
- [ ] Swappable backends
- [ ] Client-side server mode
- [ ] Debug information: show state history
- [ ] Debug information: show current state
- [ ] Debug information: show the page as its original structure
- [ ] Other HTML components
"""

from typing import Any
import traceback
import inspect
import re
from functools import wraps
from dataclasses import dataclass, is_dataclass
from bottle import Bottle, abort, request

__version__ = '0.0.2'


@dataclass
class Page:
    state: Any
    content: list[str]

    def __init__(self, state, content=None):
        if content is None:
            state, content = None, state
        self.state = state
        self.content = content

        if not isinstance(content, list):
            raise ValueError("The content of a page must be a list of strings.")
        else:
            for chunk in content:
                if not isinstance(chunk, (str, PageContent)):
                    raise ValueError("The content of a page must be a list of strings.")

    def render_content(self) -> str:
        chunked = []
        for chunk in self.content:
            if isinstance(chunk, str):
                chunked.append(f"<p>{chunk}</p>")
            else:
                chunked.append(str(chunk))
        content = "\n".join(chunked)
        return f"<form>{content}</form>"

    def verify_content(self, server) -> bool:
        for chunk in self.content:
            if isinstance(chunk, Link):
                chunk.verify(server)
        return True


BASELINE_ATTRS = ["id", "class", "style", "title", "lang", "dir", "accesskey", "tabindex",
                  "onclick", "ondblclick", "onmousedown", "onmouseup", "onmouseover", "onmousemove", "onmouseout",
                  "onkeypress", "onkeydown", "onkeyup",
                  "onfocus", "onblur", "onselect", "onchange", "onsubmit", "onreset", "onabort", "onerror", "onload",
                  "onunload", "onresize", "onscroll"]


class PageContent:
    EXTRA_ATTRS = []

    def verify(self, server) -> bool:
        return True

    def parse_extra_settings(self, **kwargs):
        extra_settings = self.extra_settings.copy()
        extra_settings.update(kwargs)
        styles, attrs = [], []
        for key, value in kwargs.items():
            if key not in self.EXTRA_ATTRS and key not in BASELINE_ATTRS:
                styles.append(f"{key}: {value}")
            else:
                attrs.append(f"{key}={str(value)!r}")
        result = " ".join(attrs)
        if styles:
            result += f" style='{'; '.join(styles)}'"
        return result


URL_REGEX = "^(?:http(s)?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$"


def check_invalid_external_url(url: str) -> str:
    if url.startswith("file://"):
        return "The URL references a local file on your computer, not a file on a server."
    if re.match(URL_REGEX, url) is not None:
        return "is a valid external url"
    return ""


TEMPLATE_404 = """
<h3>{title}</h3>

<p>{message}</p>

<p>Original error message:</p>
<pre>{error}</pre>

<p>Available routes:</p>
{routes}
"""
TEMPLATE_500 = """
<h3>{title}</h3>

<p>{message}</p>

<p>Original error message:</p>
<pre>{error}</pre>

<p>Available routes:</p>
{routes}
"""


@dataclass
class Link(PageContent):
    text: str
    url: str

    def __init__(self, text: str, url: str, external=None, **kwargs):
        self.text = text
        if callable(url):
            url = url.__name__
        if external is None:
            external = check_invalid_external_url(url) != ""
        self.external = external
        self.url = url if external else friendly_urls(url)
        self.extra_settings = kwargs

    def __str__(self) -> str:
        return f"<a href='{self.url}' {self.parse_extra_settings()}>{self.text}</a>"

    def verify(self, server) -> bool:
        if self.url not in server._handle_route:
            invalid_external_url_reason = check_invalid_external_url(self.url)
            if invalid_external_url_reason == "is a valid external url":
                return True
            elif invalid_external_url_reason:
                raise ValueError(f"Link `{self.url}` is not a valid external url.\n{invalid_external_url_reason}.")
            raise ValueError(f"Link `{self.text}` points to non-existent page `{self.url}`.")
        return True


@dataclass
class Image(PageContent):
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
        parsed_settings = self.parse_extra_settings(**extra_settings)
        return f"<img src='{self.url}' {parsed_settings}>"


@dataclass
class Textbox(PageContent):
    name: str
    kind: str
    default_value: str

    def __init__(self, name: str, kind: str = "text", default_value: str = None, **kwargs):
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
class Dropdown(PageContent):
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
        options = "\n".join(f"<option value='{option}'>{option}</option>" for option in self.options)
        return f"<select name='{self.name}' {parsed_settings}>{options}</select>"


@dataclass
class Button(PageContent):
    text: str
    url: str
    javascript: str = None

    def __init__(self, text: str, url: str, **kwargs):
        self.text = text
        self.url = url
        self.extra_settings = kwargs

    def __str__(self) -> str:
        extra_settings = {}
        if 'onclick' not in self.extra_settings:
            extra_settings['onclick'] = f"window.location.href=\"{self.url}\""
        parsed_settings = self.parse_extra_settings(**extra_settings)
        return f"<button {parsed_settings}>{self.text}</button>"


@dataclass
class SubmitButton(PageContent):
    text: str
    url: str

    def __init__(self, text: str, url: str, **kwargs):
        self.text = text
        self.url = url if isinstance(url, str) else url.__name__
        self.extra_settings = kwargs

    def __str__(self) -> str:
        extra_settings = {}
        parsed_settings = self.parse_extra_settings(**extra_settings)
        return f"<input type='submit' value='{self.text}' formaction='{self.url}' {parsed_settings} />"


@dataclass
class Table(PageContent):
    rows: list[list[str]]

    def __init__(self, rows: list[list[str]], **kwargs):
        self.rows = rows
        self.extra_settings = kwargs
        self.reformat_as_tabular()

    def reformat_as_tabular(self):
        result = []
        had_dataclasses = False
        for row in self.rows:
            if is_dataclass(row):
                had_dataclasses = True
                result.append([str(getattr(row, attr)) for attr in row.__dataclass_fields__])

        if had_dataclasses:
            result.insert(0, list(row.__dataclass_fields__.keys()))
        self.rows = result

    def __str__(self) -> str:
        extra_settings = {}
        parsed_settings = self.parse_extra_settings(**extra_settings)
        rows = "\n".join(f"<tr>{''.join(f'<td>{cell}</td>' for cell in row)}</tr>"
                         for row in self.rows)
        return f"<table {parsed_settings}>{rows}</table>"


def Text(text: str, bold: bool):
    pass


def friendly_urls(url: str) -> str:
    if url.strip("/") == "index":
        return "/"
    if not url.startswith('/'):
        url = '/' + url
    return url


class Server:
    def __init__(self):
        self.routes = {}
        self._handle_route = {}
        self.default_configuration = {
            "host": "localhost",
            "port": 8080,
            "debug": True
        }
        self._state = None
        self._state_history = []
        self.original_routes = set()

    def reset(self):
        self.routes.clear()

    def add_route(self, url, func):
        if url in self.routes:
            raise ValueError(f"URL `{url}` already exists for an existing routed function: `{func.__name__}`")
        self.original_routes.add((url, func))
        url = friendly_urls(url)
        func = self.make_bottle_page(func)
        self.routes[url] = func
        self._handle_route[url] = self._handle_route[func] = func

    def setup(self, initial_state=None):
        self._state = initial_state
        self.app = Bottle()

        # Setup error pages
        def handle_404(error):
            return TEMPLATE_404.format(title="404 Page not found", message="The requested page was not found.",
                                       error=error.body,
                                       routes="\n".join(
                                           f"<li><code>{r!r}</code>: <code>{func}</code></li>" for r, func in
                                           self.original_routes))

        self.app.error(404)(handle_404)
        # Setup routes
        if not self.routes:
            raise ValueError("No routes have been defined.\nDid you remember the @route decorator?")
        for url, func in self.routes.items():
            self.app.route(url, 'GET', func)
        if '/' not in self.routes:
            first_route = list(self.routes.values())[0]
            self.app.route('/', 'GET', first_route)

    def run(self, **kwargs):
        configuration = self.default_configuration.copy()
        configuration.update(kwargs)
        self.app.run(**configuration)

    def prepare_args(self, original_function, args, kwargs):
        args = list(args)
        kwargs = dict(**kwargs)
        for key in list(request.params.keys()):
            kwargs[key] = request.params.pop(key)
        expected_parameters = list(inspect.signature(original_function).parameters.keys())
        if (expected_parameters and expected_parameters[0] == "state") or (
                len(expected_parameters) - 1 == len(args) + len(kwargs)):
            args.insert(0, self._state)
        if len(expected_parameters) < len(args) + len(kwargs):
            self.flash_warning(
                f"The {original_function.__name__} function expected {len(expected_parameters)} parameters, but {len(args) + len(kwargs)} were provided.")
            # TODO: Select parameters to keep more intelligently by inspecting names
            args = args[:len(expected_parameters)]
            while len(expected_parameters) < len(args) + len(kwargs) and kwargs:
                kwargs.pop(list(kwargs.keys())[-1])
        return args, kwargs

    def make_bottle_page(self, original_function) -> str:
        @wraps(original_function)
        def bottle_page(*args, **kwargs):
            try:
                args, kwargs = self.prepare_args(original_function, args, kwargs)
            except Exception as e:
                return self.make_error_page("Error preparing arguments for page", e, original_function)
            try:
                page = original_function(*args, **kwargs)
            except Exception as e:
                return self.make_error_page("Error creating page", e, original_function)
            try:
                page.verify_content(self)
            except Exception as e:
                return self.make_error_page("Error verifying content", e, original_function)
            self._state_history.append(page.state)
            self._state = page.state
            try:
                content = page.render_content()
            except Exception as e:
                return self.make_error_page("Error rendering content", e, original_function)
            return content

        return bottle_page

    def make_error_page(self, title, error, original_function):
        tb = traceback.format_exc()
        new_message = f"{title}.\nError in {original_function.__name__}:\n{error}\n\n\n{tb}"
        abort(500, new_message)

    def flash_warning(self, message):
        print(message)


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


if __name__ == '__main__':
    print("This package is meant to be imported, not run as a script. For now, at least.")
