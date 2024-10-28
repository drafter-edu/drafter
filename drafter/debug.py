from dataclasses import dataclass, is_dataclass
from typing import Any, Callable
import inspect
import html

from drafter.constants import RESTORABLE_STATE_KEY, PREVIOUSLY_PRESSED_BUTTON
from drafter.history import ConversionRecord, VisitedPage, format_page_content, make_value_expandable, safe_repr
from drafter.page import Page
from drafter.urls import merge_url_query_params
from drafter.testing import bakery, _bakery_tests, DIFF_WRAP_WIDTH, diff_tests
from drafter.components import Table

@dataclass
class DebugInformation:
    page_history: list[tuple[VisitedPage, Any]]
    state: Any
    routes: dict[str, Callable]
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
            return str(Table([[
                f"<code>{html.escape(type(state).__name__)}</code>",
                f"<code>{safe_repr(state)}</code>"
            ]]))

    # TODO: Dump the current server configuration

    def render_configuration(self):
        pass