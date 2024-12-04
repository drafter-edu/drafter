import html
import os
import traceback
from dataclasses import dataclass, asdict, replace, field, fields
from functools import wraps
from typing import Any, Optional
import json
import inspect
import pathlib

import bottle

from drafter import friendly_urls, PageContent
from drafter.configuration import ServerConfiguration
from drafter.constants import RESTORABLE_STATE_KEY, SUBMIT_BUTTON_KEY, PREVIOUSLY_PRESSED_BUTTON
from drafter.debug import DebugInformation
from drafter.setup import Bottle, abort, request, static_file
from drafter.history import VisitedPage, rehydrate_json, dehydrate_json, ConversionRecord, UnchangedRecord, get_params, \
    remap_hidden_form_parameters, safe_repr
from drafter.page import Page
from drafter.files import TEMPLATE_200, TEMPLATE_404, TEMPLATE_500, INCLUDE_STYLES, TEMPLATE_200_WITHOUT_HEADER, \
    TEMPLATE_SKULPT_DEPLOY, seek_file_by_line
from drafter.urls import remove_url_query_params
from drafter.image_support import HAS_PILLOW, PILImage

import logging
logger = logging.getLogger('drafter')


DEFAULT_ALLOWED_EXTENSIONS = ('py', 'js', 'css', 'txt', 'json', 'csv', 'html', 'md')

def bundle_files_into_js(main_file, root_path, allowed_extensions=DEFAULT_ALLOWED_EXTENSIONS):
    skipped_files, added_files = [], []
    all_files = {}
    for root, dirs, files in os.walk(root_path):
        for file in files:
            is_main = os.path.join(root_path, file) == main_file
            path = pathlib.Path(os.path.join(root, file)).relative_to(root_path)
            if pathlib.Path(file).suffix[1:].lower() not in allowed_extensions:
                skipped_files.append(os.path.join(root, file))
                continue
            with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                content = f.read()
                filename = str(path.as_posix()) if not is_main else "main.py"
                all_files[filename] = content
                added_files.append(os.path.join(root, file))

    js_lines = []
    for filename, contents in all_files.items():
        js_lines.append(f"Sk.builtinFiles.files[{filename!r}] = {contents!r};\n")

    return "\n".join(js_lines), skipped_files, added_files


class Server:
    _page_history: list[tuple[VisitedPage, Any]]
    _custom_name = None

    def __init__(self, _custom_name=None, **kwargs):
        self.routes = {}
        self._handle_route = {}
        self.configuration = ServerConfiguration(**kwargs)
        self._state = None
        self._initial_state = None
        self._initial_state_type = None
        self._state_history = []
        self._state_frozen_history = []
        self._page_history = []
        self._conversion_record = []
        self.original_routes = []
        self.app = None
        self._custom_name = _custom_name

    def __repr__(self):
        if self._custom_name:
            return self._custom_name
        return f"Server({self.configuration!r})"

    def clear_routes(self):
        self.routes.clear()

    def dump_state(self):
        return json.dumps(dehydrate_json(self._state))

    def load_from_state(self, state, state_type):
        return rehydrate_json(json.loads(state), state_type)

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

    def reset(self):
        self._state = self.load_from_state(self._initial_state, self._initial_state_type)
        self._state_history.clear()
        self._state_frozen_history.clear()
        self._page_history.clear()
        self._conversion_record.clear()
        return self.routes['/']()

    def setup(self, initial_state=None):
        self._state = initial_state
        self._initial_state = self.dump_state()
        self._initial_state_type = type(initial_state)
        self.app = Bottle()

        # Setup error pages
        def handle_404(error):
            message = "<p>The requested page <code>{url}</code> was not found.</p>".format(url=request.url)
            # TODO: Only show if not the index
            message += "\n<p>You might want to return to the <a href='/'>index</a> page.</p>"
            original_error = f"{error.body}\n"
            if hasattr(error, 'traceback'):
                original_error += f"{error.traceback}\n"
            return TEMPLATE_404.format(title="404 Page not found", message=message,
                                       error=original_error,
                                       routes="\n".join(
                                           f"<li><code>{r!r}</code>: <code>{func}</code></li>" for r, func in
                                           self.original_routes))

        def handle_500(error):
            message = "<p>Sorry, the requested URL <code>{url}</code> caused an error.</p>".format(url=request.url)
            message += "\n<p>You might want to return to the <a href='/'>index</a> page.</p>"
            original_error = f"{error.body}\n"
            if hasattr(error, 'traceback'):
                original_error += f"{error.traceback}\n"
            return TEMPLATE_500.format(title="500 Internal Server Error",
                                       message=message,
                                       error=original_error,
                                       routes="\n".join(
                                           f"<li><code>{r!r}</code>: <code>{func}</code></li>" for r, func in
                                           self.original_routes))

        self.app.error(404)(handle_404)
        self.app.error(500)(handle_500)
        # Setup routes
        if not self.routes:
            raise ValueError("No routes have been defined.\nDid you remember the @route decorator?")
        self.app.route("/--reset", 'GET', self.reset)
        # If not skulpt, then allow them to test the deployment
        if not self.configuration.skulpt:
            self.app.route("/--test-deployment", 'GET', self.test_deployment)
        for url, func in self.routes.items():
            self.app.route(url, 'GET', func)
            self.app.route(url, "POST", func)
        if '/' not in self.routes:
            first_route = list(self.routes.values())[0]
            self.app.route('/', 'GET', first_route)
        self.handle_images()

    def run(self, **kwargs):
        final_args = asdict(self.configuration)
        # Update the configuration with the safe kwargs
        safe_keys = fields(ServerConfiguration)
        safe_kwargs = {key: value for key, value in kwargs.items() if key in safe_keys}
        updated_configuration = replace(self.configuration, **safe_kwargs)
        self.configuration = updated_configuration
        # Update the final args with the new configuration
        final_args.update(kwargs)
        self.app.run(**final_args)

    def prepare_args(self, original_function, args, kwargs):
        self._conversion_record.clear()
        args = list(args)
        kwargs = dict(**kwargs)
        button_pressed = ""
        params = get_params()
        if SUBMIT_BUTTON_KEY in params:
            button_pressed = json.loads(params.pop(SUBMIT_BUTTON_KEY))
        elif PREVIOUSLY_PRESSED_BUTTON in params:
            button_pressed = json.loads(params.pop(PREVIOUSLY_PRESSED_BUTTON))
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
        representation = [safe_repr(arg) for arg in args] + [
            f"{key}={safe_repr(value)}" if show_names.get(key, False) else safe_repr(value)
            for key, value in sorted(kwargs.items(), key=lambda item: expected_parameters.index(item[0]))]
        return args, kwargs, ", ".join(representation), button_pressed

    def handle_images(self):
        if self.configuration.deploy_image_path:
            self.app.route(f"/{self.configuration.deploy_image_path}/<path:path>", 'GET', self.serve_image)

    def serve_image(self, path):
        return static_file(path, root='./' + self.configuration.src_image_folder, mimetype='image/png')

    def try_special_conversions(self, value, target_type):
        if isinstance(value, bottle.FileUpload):
            if target_type == bytes:
                return target_type(value.file.read())
            elif target_type == str:
                try:
                    return value.file.read().decode('utf-8')
                except UnicodeDecodeError as e:
                    raise ValueError(f"Could not decode file {value.filename} as utf-8. Perhaps the file is not the type that you expected, or the parameter type is inappropriate?") from e
            elif target_type == dict:
                return {'filename': value.filename, 'content': value.file.read()}
            elif HAS_PILLOW and issubclass(target_type, PILImage.Image):
                try:
                    image = PILImage.open(value.file)
                    image.filename = value.filename
                    return image
                except Exception as e:
                    # TODO: Allow configuration for just setting this to None instead, if there is an error
                    raise ValueError(f"Could not open image file {value.filename} as a PIL.Image. Perhaps the file is not an image, or the parameter type is inappropriate?") from e
        return target_type(value)

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
                    target_type = expected_types[param]
                    converted_arg = self.try_special_conversions(val, target_type)
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
                additional_details = (f"  Arguments: {args!r}\n"
                                      f"  Keyword Arguments: {kwargs!r}\n"
                                      f"  Button Pressed: {button_pressed!r}\n"
                                      f"  Function Signature: {inspect.signature(original_function)}")
                return self.make_error_page("Error creating page", e, original_function, additional_details)
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
                content = page.render_content(self.dump_state(), self.configuration)
            except Exception as e:
                return self.make_error_page("Error rendering content", e, original_function)
            visiting_page.finish("Finished Page Load")
            if self.configuration.debug:
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
        content = f"<div class='btlw'>{content}</div>"
        style = self.configuration.style
        if style in INCLUDE_STYLES:
            scripts = "\n".join(INCLUDE_STYLES[style]['scripts'])
            styles = "\n".join(INCLUDE_STYLES[style]['styles'])
        else:
            raise ValueError(f"Unknown style {style}. Please choose from {', '.join(INCLUDE_STYLES.keys())}, or add a custom style tag with add_website_header.")
        if self.configuration.additional_header_content:
            header_content = "\n".join(self.configuration.additional_header_content)
        else:
            header_content = ""
        if self.configuration.additional_css_content:
            additional_css = "\n".join(self.configuration.additional_css_content)
            styles = f"{styles}\n<style>{additional_css}</style>"
        if self.configuration.skulpt:
            return TEMPLATE_200_WITHOUT_HEADER.format(
                header=header_content, styles=styles, scripts=scripts, content=content,
                title=json.dumps(self.configuration.title))
        else:
            return TEMPLATE_200.format(
                header=header_content, styles=styles, scripts=scripts, content=content,
                title=html.escape(self.configuration.title))


    def make_error_page(self, title, error, original_function, additional_details=""):
        tb = html.escape(traceback.format_exc())
        new_message = (f"""{title}.\n"""
                       f"""Error in {original_function.__name__}:\n"""
                       f"""{html.escape(str(error))}\n\n\n{tb}""")
        if additional_details:
            new_message += f"\n\n\nAdditional Details:\n{additional_details}"
        abort(500, new_message)

    def flash_warning(self, message):
        print(message)

    def make_debug_page(self):
        content = DebugInformation(self._page_history, self._state, self.routes, self._conversion_record,
                                   self.configuration)
        return content.generate()

    def test_deployment(self):
        # Bundle up the necessary files, including the source code
        student_main_file = seek_file_by_line("start_server")
        if student_main_file is None:
            return TEMPLATE_500.format(title="500 Internal Server Error",
                                       message="Could not find the student's main file.",
                                       error="Could not find the student's main file.",
                                       routes="")
        bundled_js, skipped, added = bundle_files_into_js(student_main_file, os.path.dirname(student_main_file))
        return TEMPLATE_SKULPT_DEPLOY.format(website_code=bundled_js)


MAIN_SERVER = Server(_custom_name="MAIN_SERVER")

def set_main_server(server: Server):
    """
    Sets the main server to the given server. This is useful for testing purposes.

    :param server: The server to set as the main server
    :return: None
    """
    global MAIN_SERVER
    MAIN_SERVER = server

def get_main_server() -> Server:
    """
    Gets the main server. This is useful for testing purposes.

    :return: The main server
    """
    return MAIN_SERVER

def get_all_routes(server: Optional[Server] = None):
    if server is None:
        server = get_main_server()
    return server.routes


def get_server_setting(key, default=None, server=MAIN_SERVER):
    """
    Gets a setting from the server's configuration. If the setting is not found, the default value is returned.

    :param key: The key to look up in the configuration
    :param default: The default value to return if the key is not found
    :param server: The server to look up the setting in (defaults to the ``MAIN_SERVER``)
    :return: The value of the setting, or the default value if not found
    """
    return getattr(server.configuration, key, default)


def start_server(initial_state=None, server: Server = MAIN_SERVER, skip=False, **kwargs):
    """
    Starts the server with the given initial state and configuration. If the server is set to skip, it will not start.
    Additional keyword arguments will be passed to the server's run method, and therefore to Bottle. This can be
    used to control things like the ``port``.

    :param initial_state: The initial state to start the server with
    :param server: The server to run on, defaulting to ``MAIN_SERVER``
    :param skip: If True, the server will not start; this is useful for running tests headlessly
    :param \**kwargs: Additional keyword arguments to pass to the server's run method. See below.
    :return: None

    :Keyword Arguments:
        * *port* (``int``) --
          The port to run the server on. Defaults to ``8080``
    """
    if server.configuration.skip or skip:
        logger.info("Skipping server setup and execution")
        return
    server.setup(initial_state)
    server.run(**kwargs)
