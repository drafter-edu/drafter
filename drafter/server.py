import html
import os
import traceback
from dataclasses import dataclass, asdict, replace, field
from functools import wraps
from typing import Any
import json
import inspect

from drafter import friendly_urls, PageContent
from drafter.configuration import ServerConfiguration
from drafter.constants import RESTORABLE_STATE_KEY, SUBMIT_BUTTON_KEY, PREVIOUSLY_PRESSED_BUTTON
from drafter.debug import DebugInformation
from drafter.setup import Bottle, abort, request, static_file
from drafter.history import VisitedPage, rehydrate_json, dehydrate_json, ConversionRecord, UnchangedRecord, get_params, \
    remap_hidden_form_parameters
from drafter.page import Page
from drafter.files import TEMPLATE_200, TEMPLATE_404, TEMPLATE_500, INCLUDE_STYLES, TEMPLATE_200_WITHOUT_HEADER
from drafter.urls import remove_url_query_params

import logging
logger = logging.getLogger('drafter')


class Server:
    _page_history: list[tuple[VisitedPage, Any]]

    def __init__(self, **kwargs):
        self.routes = {}
        self._handle_route = {}
        self.configuration = ServerConfiguration(**kwargs)
        self._state = None
        self._initial_state = None
        self._state_history = []
        self._state_frozen_history = []
        self._page_history = []
        self._conversion_record = []
        self.original_routes = []
        self.app = None

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
        configuration = replace(self.configuration, **kwargs)
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
        if self.configuration.image_folder:
            self.app.route(f"/{self.configuration.image_folder}/<path:path>", 'GET', self.serve_image)

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


    def make_error_page(self, title, error, original_function):
        tb = traceback.format_exc()
        new_message = f"{title}.\nError in {original_function.__name__}:\n{error}\n\n\n{tb}"
        abort(500, new_message)

    def flash_warning(self, message):
        print(message)

    def make_debug_page(self):
        content = DebugInformation(self._page_history, self._state, self.routes, self._conversion_record)
        return content.generate()


MAIN_SERVER = Server()


def get_server_setting(key, default=None, server=MAIN_SERVER):
    return getattr(server.configuration, key, default)


def start_server(initial_state=None, server: Server = MAIN_SERVER, skip=False, **kwargs):
    if server.configuration.skip or skip:
        logger.info("Skipping server setup and execution")
        return
    server.setup(initial_state)
    server.run(**kwargs)
