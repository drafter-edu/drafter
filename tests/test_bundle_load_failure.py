"""Tests for the page's own check that Drafter's script loaded.

When `drafter.pyodide.js` fails to load, nothing of Drafter's can report
it: the error dialogs live in that same file. The page used to lift its
loading screen anyway, leaving a first page (drawn ahead of time) that
looked ready while every button did nothing. The scaffold now checks for
the script itself and says so in plain HTML.
"""

from pathlib import Path

from drafter.config.app_builder import AppBuilderConfiguration
from drafter.config.app_common import AppCommonConfiguration
from drafter.config.app_server import AppServerConfiguration
from drafter.config.bootstrap import BootstrapConfiguration
from drafter.config.client_server import ClientServerConfiguration
from drafter.config.system import SystemConfiguration
from drafter.scaffolding import templating
from drafter.site.site import DRAFTER_TAG_IDS

NOTICE_ID = "--drafter-script-missing-notice"


def render_index(tmp_path: Path, shared_runtime: bool = False) -> str:
    main = tmp_path / "main.py"
    main.write_text("print('hello')\n", encoding="utf-8")
    app_common = AppCommonConfiguration()
    app_common.prerender_initial_page = False
    app_builder = AppBuilderConfiguration()
    app_builder.shared_runtime = shared_runtime
    system = SystemConfiguration(
        bootstrap=BootstrapConfiguration(path=str(main)),
        client_server=ClientServerConfiguration(),
        app_server=AppServerConfiguration(),
        app_builder=app_builder,
        app_common=app_common,
    )
    return templating.render_index_html(
        system=system,
        modified_system={},
        inline_py=True,
        user_code="",
        python_url=None,
        dev_ws_url=None,
        assets_url="/__drafter_assets",
    )


def test_page_checks_for_the_script_before_using_it(tmp_path):
    html = render_index(tmp_path)

    check = html.index("if (!window.Drafter)")
    first_use = html.index("window.Drafter.setupPyodide(")
    assert check < first_use
    # The check ends the startup, so the first use is never reached.
    assert "return;" in html[check:first_use]


def test_notice_replaces_the_site_and_names_the_file(tmp_path):
    html = render_index(tmp_path)
    notice = html[html.index("if (!window.Drafter)") : html.index("// 1) Load Pyodide")]

    assert NOTICE_ID in notice
    assert "This site could not start" in notice
    assert f'getElementById("{DRAFTER_TAG_IDS["ROOT"]}").replaceChildren' in notice
    assert "js/drafter.pyodide.js" in notice


def test_shared_runtime_pages_try_the_parent_before_the_check(tmp_path):
    # An embedded page can run on its parent's copy of Drafter, so a
    # missing script of its own only matters once that has been ruled out.
    html = render_index(tmp_path, shared_runtime=True)

    assert html.index("parentHost.attach(") < html.index("if (!window.Drafter)")


class TestFirstPageWaitsForPython:
    """The first page is drawn ahead of time, then replaced.

    Text typed into it before Python had started was thrown away when the
    live page took its place, so the route got an empty string. The page
    cannot be used until the loading screen lifts.
    """

    def test_root_starts_out_inert(self, tmp_path):
        html = render_index(tmp_path)

        assert f'<div id="{DRAFTER_TAG_IDS["ROOT"]}" inert>' in html

    def test_inert_is_lifted_with_the_loading_screen(self, tmp_path):
        html = render_index(tmp_path)
        finishing = html[html.rindex("} finally {") :]

        lifted = finishing.index(
            f"getElementById(\"{DRAFTER_TAG_IDS['ROOT']}\")?.removeAttribute('inert')"
        )
        screen_removed = finishing.index("--drafter-initial-loading-white-screen")
        assert lifted < screen_removed

    def test_lifted_on_every_way_out_of_start_up(self, tmp_path):
        # One `finally` covers the normal start, a failed start, the
        # missing-script notice, and an embedded page that attached to
        # its parent's Python (each of those leaves through `return`).
        html = render_index(tmp_path, shared_runtime=True)
        start_up = html[html.index("(async () => {") :]

        assert start_up.count("} finally {") == 1
        assert start_up.index("removeAttribute('inert')") > start_up.index(
            "} finally {"
        )
