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
        page = default_error("state", make_error(), make_server())

        headers = page_headers(page)
        assert "Something Went Wrong" in headers
        assert "Technical Details" in headers

    def test_custom_title_replaces_default(self):
        page = default_error(
            "state",
            make_error(),
            make_server(error_page_title="Oh no, a glitch!"),
        )

        headers = page_headers(page)
        assert "Oh no, a glitch!" in headers
        assert "Something Went Wrong" not in headers

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
