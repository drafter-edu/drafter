from dataclasses import dataclass, is_dataclass
from typing import Any, Callable, List, Tuple, Dict
import inspect
import html

from drafter.constants import RESTORABLE_STATE_KEY, PREVIOUSLY_PRESSED_BUTTON
from drafter.history import (
    ConversionRecord,
    VisitedPage,
    format_page_content,
    make_value_expandable,
    safe_repr,
)
from drafter.payloads.page import Page
from drafter.urls import merge_url_query_params
from drafter.testing import bakery, _bakery_tests, DIFF_WRAP_WIDTH, diff_tests
from drafter.components.components import Table
from drafter.configuration import ServerConfiguration


@dataclass
class DebugInformation:
    """
    Holds debugging information related to the server, including page history, routing,
    state, conversion records, and configuration.

    This class is designed to generate detailed HTML debug information for students
    when debugging server applications. It provides utilities to render the current
    state of the server, the history of page loads, available routes, and test statuses.
    Additionally, it outlines server configuration details and deployment settings.

    :ivar page_history: List of tuples where each tuple contains a `VisitedPage` instance
        representing a visited page and its associated state.
    :type page_history: List[Tuple[VisitedPage, Any]]
    :ivar state: The current state of the application.
    :type state: Any
    :ivar routes: Dictionary of available routes mapped to their handler functions.
    :type routes: Dict[str, Callable]
    :ivar conversion_record: List of `ConversionRecord` instances that track state
        transitions and parameter changes.
    :type conversion_record: List[ConversionRecord]
    :ivar configuration: Server configuration holding deployment and runtime configuration details.
    :type configuration: ServerConfiguration
    """

    page_history: List[Tuple[VisitedPage, Any]]
    state: Any
    routes: Dict[str, Callable]
    conversion_record: List[ConversionRecord]
    configuration: ServerConfiguration

    INDENTATION_START_HTML = (
        "<div class='row'><div class='one column'></div><div class='eleven columns'>"
    )
    INDENTATION_END_HTML = "</div></div>"

    def generate(self):
        """
        Generates an HTML string containing debug information for the current system state. The generated
        debug information includes details about the current route, system state, available routes, page
        load history, test status, and test deployment. The HTML content is wrapped within a `<div>` element
        with the class `btlw-debug`.

        :return: An HTML string composed of debug information for the current system state.
        :rtype: str
        """
        parts = [
            "<div class='btlw-debug'>",
            "<h3>Debug Information</h3>",
            "<em>To hide this information, call <code>hide_debug_information()</code> in your code.</em><br>",
            *self.current_route(),
            *self.current_state(),
            *self.available_routes(),
            *self.page_load_history(),
            *self.test_status(),
            *self.test_deployment(),
            "</div>",
        ]
        return "\n".join(parts)

    def current_route(self):
        """
        Generates a sequence of HTML content describing the current routing state
        and associated parameter values.

        The function produces the last successfully visited page and its HTML
        representation, along with presenting a list of non-state parameters in
        HTML format. If no pages have been visited successfully or no non-state
        parameters exist, default messages in HTML format are generated instead.

        :return: A generator that yields HTML content representing the current
            routing state and its parameters.
        :rtype: Iterator[str]
        """
        # Current route
        if not self.page_history:
            yield "Currently no pages have been successfully visited."
        else:
            yield self.page_history[-1][0].as_html()
        yield f"<br>"
        non_state_parameters = [
            record for record in self.conversion_record if record.parameter != "state"
        ]
        if non_state_parameters:
            yield "<details open><summary><strong>Current parameter values:</strong></summary>"
            yield f"{self.INDENTATION_START_HTML}"
            yield f"<ul>"
            for record in self.conversion_record:
                if record.parameter != "state":
                    yield record.as_html()
            yield f"</ul>{self.INDENTATION_END_HTML}</details>"
        else:
            yield "<strong>No parameters were provided.</strong>"

    def current_state(self):
        """
        Generates HTML representation of the current state.

        This function yields an HTML block describing the current state
        of the object. It checks if the ``state`` attribute is not ``None``,
        and if so, it utilizes the method ``render_state`` to construct the
        appropriate HTML for the state data. If the attribute ``state`` is
        ``None``, it yields a placeholder HTML.

        :return: Yields string fragments of an HTML representation of the
            object's current state.
        :rtype: Iterator[str]

        """
        # Current State
        yield "<details open><summary><strong>Current State</strong></summary>"
        yield f"{self.INDENTATION_START_HTML}"
        if self.state is not None:
            yield self.render_state(self.state)
        else:
            yield "<code>None</code>"
        yield f"{self.INDENTATION_END_HTML}</details>"

    def available_routes(self):
        """
        Generate an HTML formatted list of all available routes and their corresponding functions.

        This method dynamically generates documentation for routes by examining the registered
        functions and their parameters in the `routes` dictionary. It formats each route as a list
        item with its corresponding callable function and parameters. Routes that have no parameters
        are formatted as clickable links pointing to the route path. The output is returned as
        HTML-rendered lines suitable for detailed documentation display.

        :returns: HTML-formatted strings representing available routes and their metadata.
        :rtype: Iterator[str]
        """
        # Routes
        yield f"<details open><summary><strong>Available Routes</strong></summary>"
        yield f"{self.INDENTATION_START_HTML}"
        yield f"<ul>"
        for original_route, function in self.routes.items():
            parameter_list = inspect.signature(function).parameters.keys()
            parameters = ", ".join(parameter_list)
            if original_route != "/":
                original_route += "/"
            route = f"<code>{original_route}</code>"
            call = f"{function.__name__}({parameters})"
            if len(parameter_list) == 1:
                call = f"<a href='{original_route}'>{call}</a>"
            yield f"<li>{route}: <code>{call}</code></li>"
        yield f"</ul>{self.INDENTATION_END_HTML}</details>"

    def page_load_history(self):
        """
        Generates HTML content listing the history of web page loads including related details, such as
        the button actions, function calls, URLs, and page content. Each step is presented in an
        expandable/collapsible structure for better visualization.

        :returns: A generator that yields strings representing segments of an HTML document formatted
            with the history details.
        :rtype: Iterator[str]
        """
        # Page History
        yield "<details open><summary><strong>Page Load History</strong></summary><ol>"
        all_visits = set()
        for page_history, old_state in reversed(self.page_history):
            button_pressed = (
                f"Clicked <code>{page_history.button_pressed}</code> &rarr; "
                if page_history.button_pressed
                else ""
            )
            url = merge_url_query_params(
                page_history.url,
                {
                    RESTORABLE_STATE_KEY: old_state,
                    PREVIOUSLY_PRESSED_BUTTON: page_history.button_pressed,
                },
            )
            yield f"<li>{button_pressed}{page_history.status}"  # <details><summary>
            yield f"{self.INDENTATION_START_HTML}"
            yield f"URL: <a href='{url}'><code>{page_history.url}/</code></a><br>"
            call = f"{page_history.function.__name__}({page_history.arguments})"
            yield f"Call: <code>{call}</code><br>"
            yield f"<details><summary>Page Content:</summary><pre style='width: fit-content' class='copyable'>"
            full_code = (
                f"assert_equal(\n {call},\n {page_history.original_page_content})"
            )
            all_visits.add(full_code)
            yield f"<code>{full_code}</code></pre></details>"
            yield f"{self.INDENTATION_END_HTML}"
            yield f"</li>"
        yield "</ol>"
        for part in self.copy_all_page_history(all_visits):
            yield part
        yield "</details>"

    def copy_all_page_history(self, all_visits):
        """
        Copies and formats the entire history of all page visits into a structured HTML
        representation, combining them within a collapsible details element for display.

        This function yields formatted HTML elements suitable for embedding in web pages
        or other HTML-based interfaces. The page history provided as input is processed
        and rendered into a human-readable format enclosed in a collapsible container.

        :param all_visits: The list of strings where each string represents individual
            page visit details to be combined and formatted for rendering.
        :type all_visits: list of str

        :return: Yields strings of HTML elements representing the formatted and combined
            page history.
        :rtype: Iterator[str]
        """
        yield "<details><summary><strong>Combined Page History</strong></summary>"
        yield f"{self.INDENTATION_START_HTML}"
        yield (
            "<pre style='width: fit-content' class='copyable'><code>"
            + "\n\n".join(all_visits)
            + "</code></pre>"
        )
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
                            given, given_normal_mode = format_page_content(
                                given, DIFF_WRAP_WIDTH
                            )
                            expected, expected_normal_mode = format_page_content(
                                expected, DIFF_WRAP_WIDTH
                            )
                            yield diff_tests(
                                given,
                                expected,
                                "Your function returned",
                                "But the test expected",
                            )
                yield "</ul>"
                yield f"{self.INDENTATION_END_HTML}"
                yield "</details>"
            else:
                yield "<div><strong>No Tests</strong></div>"

    def render_state(self, state):
        if is_dataclass(state):
            return str(Table(state))
        else:
            return str(
                Table(
                    [
                        [
                            f"<code>{html.escape(type(state).__name__)}</code>",
                            f"<code>{safe_repr(state)}</code>",
                        ]
                    ]
                )
            )

    def test_deployment(self):
        if self.configuration.skulpt:
            yield "<strong>Configuration</strong>"
            yield f"<p>Running on Skulpt.</p>"
        else:
            yield "<strong>Configuration</strong>"
            yield f"<div>Running on {self.configuration.backend}.</div>"
            yield f"""<details><summary>Configuration Details</summary><pre>
Host: {self.configuration.host}
Port: {self.configuration.port}
Reloader: {self.configuration.reloader}
Title: {self.configuration.title}
Framed: {self.configuration.framed}
Style: {self.configuration.style}
src_image_folder: {self.configuration.src_image_folder}
save_uploaded_files: {self.configuration.save_uploaded_files}
deploy_image_path: {self.configuration.deploy_image_path}
</pre></details>"""
            yield "<a class='button' target=_blank href='--test-deployment'>Try Deployment</a><br><small>Loads the website in a new tab using the deployment settings. Note that this does not make the site externally available; it is useful for testing your website before publishing it on a service like GitHub Pages.</small>"

    # TODO: Dump the current server configuration

    def render_configuration(self):
        pass
