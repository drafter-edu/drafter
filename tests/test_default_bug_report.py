"""Tests for the default bug-report page (router/defaults/bug_report.py).

The --bug-report system route explains when a bug report is appropriate
(actual Drafter bugs or limitations, not homework help) and renders the
well-known download button that the client bridge wires to the debug
panel's bug-report bundle.
"""

from types import SimpleNamespace

from drafter.components import Header
from drafter.payloads.kinds.page import Page
from drafter.router.defaults.bug_report import (
    DownloadBugReportButton,
    default_bug_report,
)
from drafter.router.system_routes import _SYSTEM_ROUTES
from drafter.site.site import DRAFTER_TAG_IDS


def make_page():
    return default_bug_report("state", SimpleNamespace())


def page_headers(page):
    return [item.body for item in page.content if isinstance(item, Header)]


def page_text(page):
    return " ".join(repr(item) for item in page.content)


class TestDefaultBugReport:
    def test_registered_as_system_route(self):
        assert _SYSTEM_ROUTES["--bug-report"] is default_bug_report

    def test_returns_page_with_state(self):
        page = make_page()
        assert isinstance(page, Page)
        assert page.state == "state"

    def test_explains_when_reports_are_appropriate(self):
        headers = page_headers(make_page())
        assert "When a bug report is appropriate" in headers
        assert "When a bug report is NOT appropriate" in headers

        text = page_text(make_page())
        assert "limitation" in text
        assert "homework" in text

    def test_includes_download_button_with_well_known_id(self):
        page = make_page()
        buttons = [
            item for item in page.content if isinstance(item, DownloadBugReportButton)
        ]
        assert len(buttons) == 1
        assert buttons[0].get_id() == DRAFTER_TAG_IDS["BUG_REPORT_DOWNLOAD"]

    def test_offers_a_way_back_to_the_index(self):
        assert "index" in page_text(make_page())

    def test_rendered_button_is_not_a_submit_button(self):
        html = make_page().render("state", None)
        assert f'id="{DRAFTER_TAG_IDS["BUG_REPORT_DOWNLOAD"]}"' in html
        # type="button" keeps the click from submitting the site form.
        assert 'type="button"' in html
        assert "Download Bug Report" in html
