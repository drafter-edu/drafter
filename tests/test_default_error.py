"""Tests for the default error page (router/defaults/error.py) customization.

The error page's heading, friendly message, and technical-details section
can be customized via the `error_page_title`, `error_page_message`, and
`error_page_show_details` configuration settings.
"""

from types import SimpleNamespace

from drafter.components import Header
from drafter.config.client_server import ClientServerConfiguration
from drafter.data.errors import ErrorDetails
from drafter.router.defaults.error import default_error


def make_server(**config_overrides):
    configuration = ClientServerConfiguration(**config_overrides)
    return SimpleNamespace(get_current_configuration=lambda: configuration)


def make_error():
    return ErrorDetails(
        id="request.route_execution_failed",
        category="runtime",
        message="division by zero",
        severity="error",
        details="ZeroDivisionError",
        traceback="Traceback (most recent call last):\n  ...",
    )


def page_headers(page):
    container = page.content[0]
    return [item.body for item in container.content if isinstance(item, Header)]


class TestErrorPageCustomization:
    def test_default_title_and_details(self):
        # With no friendly_title on the envelope, the title derives from
        # the category (runtime → "Error in Your Code") instead of the
        # generic "Something Went Wrong".
        page = default_error("state", make_error(), make_server())

        headers = page_headers(page)
        assert "Error in Your Code" in headers
        assert "Technical Details" in headers

    def test_custom_title_replaces_default(self):
        page = default_error(
            "state",
            make_error(),
            make_server(error_page_title="Oh no, a glitch!"),
        )

        headers = page_headers(page)
        assert "Oh no, a glitch!" in headers
        assert "Error in Your Code" not in headers

    def test_custom_message_replaces_summary(self):
        page = default_error(
            "state",
            make_error(),
            make_server(error_page_message="Please tell your teacher."),
        )

        container = page.content[0]
        texts = [repr(item) for item in container.content]
        assert any("Please tell your teacher." in text for text in texts)

    def test_details_can_be_hidden(self):
        page = default_error(
            "state",
            make_error(),
            make_server(error_page_show_details=False),
        )

        headers = page_headers(page)
        assert "Technical Details" not in headers
        # Navigation options remain available.
        texts = [repr(item) for item in page.content[0].content]
        assert any("Return to Index Page" in text for text in texts)


class TestErrorPageTitles:
    def test_title_from_envelope_friendly_title(self):
        error = ErrorDetails(
            id="request.route_execution_failed",
            category="runtime",
            message="name 'total' is not defined",
            friendly_title="Unknown Name",
        )
        assert "Unknown Name" in page_headers(
            default_error("state", error, make_server())
        )

    def test_argument_parsing_failed_gets_specific_title(self):
        error = ErrorDetails(
            id="request.argument_parsing_failed",
            category="request",
            message="could not bind",
        )
        headers = page_headers(default_error("state", error, make_server()))
        assert "Problem With the Route's Arguments" in headers
        assert "Something Went Wrong" not in headers


class TestStepRendering:
    def test_backticks_in_steps_become_inline_code(self):
        error = ErrorDetails(
            id="request.route_execution_failed",
            category="runtime",
            message="boom",
            friendly_steps=("Try the `in` operator before indexing.",),
        )
        page = default_error("state", error, make_server())
        text = repr(page.content[0])
        assert "InlineCode('in')" in text
        assert "`" not in text.replace("\\`", "")

    def test_plain_steps_stay_plain_strings(self):
        error = ErrorDetails(
            id="request.route_execution_failed",
            category="runtime",
            message="boom",
            friendly_steps=("Just read the message.",),
        )
        text = repr(default_error("state", error, make_server()).content[0])
        assert "Just read the message." in text


class TestTechnicalDetailsRendering:
    def make_error_with_data(self, **data):
        return ErrorDetails(
            id="request.route_execution_failed",
            category="runtime",
            message="division by zero",
            details="",
            data=data,
            traceback=None,
        )

    def page_text(self, page) -> str:
        return repr(page.content[0])

    def test_exact_route_call_renders_without_note(self):
        error = self.make_error_with_data(
            route_call="guess(pick=5)", route_call_exact=True
        )
        text = self.page_text(default_error("state", error, make_server()))
        assert "Route Call" in text
        assert "guess(pick=5)" in text
        assert "approximate" not in text

    def test_approximate_route_call_renders_with_note(self):
        error = self.make_error_with_data(
            route_call="guess(pick='abc')", route_call_exact=False
        )
        text = self.page_text(default_error("state", error, make_server()))
        assert "guess(pick='abc')" in text
        assert "approximate" in text

    def test_structured_data_renders_nested_not_repred(self):
        error = self.make_error_with_data(
            request={
                "url": "guess",
                "kwargs": {"pick": "5"},
                "raw_payload": [{"name": "pick", "source": "form_field"}],
            }
        )
        text = self.page_text(default_error("state", error, make_server()))
        # The row label comes from the data key, and nested keys/values
        # appear individually rather than inside one repr blob.
        assert "Request" in text
        assert "form_field" in text
        assert "{'url':" not in text

    def test_nested_data_is_collapsed_by_default(self):
        from drafter.components import Details

        def find_details(component):
            found = []
            if isinstance(component, Details):
                found.append(component)
            children = list(getattr(component, "content", []) or [])
            for row in getattr(component, "rows", []) or []:
                children.extend(row if isinstance(row, (list, tuple)) else [row])
            for child in children:
                if not isinstance(child, (str, bytes)):
                    found.extend(find_details(child))
            return found

        error = self.make_error_with_data(
            request={"url": "guess", "kwargs": {"pick": "5"}}
        )
        page = default_error("state", error, make_server())
        text = self.page_text(page)
        assert "Show details" in text
        collapsibles = find_details(page.content[0])
        assert collapsibles, "expected the request data to sit in a Details"
        assert all(not detail.open for detail in collapsibles)

    def test_empty_details_row_is_omitted(self):
        error = self.make_error_with_data()
        text = self.page_text(default_error("state", error, make_server()))
        assert "'Details'" not in text


class TestConfigurationRoundTrip:
    def test_new_fields_survive_copy(self):
        config = ClientServerConfiguration(
            button_spinners=True,
            error_page_title="Custom",
            error_page_message="Message",
            error_page_show_details=False,
        )
        copied = config.copy()
        assert copied.button_spinners is True
        assert copied.error_page_title == "Custom"
        assert copied.error_page_message == "Message"
        assert copied.error_page_show_details is False

    def test_new_fields_serialize_to_json(self):
        config = ClientServerConfiguration(button_spinners=True)
        data = config.to_json()
        assert data["button_spinners"] is True
        assert data["error_page_title"] == ""
        assert data["error_page_show_details"] is True

    def test_cli_flags_parse(self):
        parsed = ClientServerConfiguration.parse_args(
            {
                "button_spinners": True,
                "error_page_title": "Oops",
                "error_page_message": "Sorry!",
                "hide_error_details": True,
            }
        )
        assert parsed["button_spinners"] is True
        assert parsed["error_page_title"] == "Oops"
        assert parsed["error_page_message"] == "Sorry!"
        assert parsed["error_page_show_details"] is False
