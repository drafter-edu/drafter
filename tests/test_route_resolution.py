"""Tests for how the Router resolves a requested URL to a registered route.

A requested URL matches its exact (normalized) registration first and only
then falls back to the cleaned, function-style name. System routes (the
`--` prefix, such as `--about`) match exactly and never through the cleaned
name, so a student route named `about` and the system `--about` route are
two separate pages.
"""

import pytest

from drafter.client_server.client_server import ClientServer
from drafter.data.errors import STATUS_NOT_FOUND, STATUS_OK
from drafter.data.request import Request
from drafter.payloads.kinds.page import Page
from drafter.router.routes import Router, is_system_url
from drafter.router.system_routes import _SYSTEM_ROUTES

DASHED_SYSTEM_ROUTES = [url for url in _SYSTEM_ROUTES if url.startswith("--")]
"""Every system route that carries the reserved `--` prefix."""


def bare_name(system_url: str) -> str:
    """The function name a student could plausibly pick: `--bug-report` -> `bugreport`."""
    return system_url.replace("-", "")


def make_started_server() -> ClientServer:
    server = ClientServer("test_route_resolution")
    server.do_configuration()
    server.do_start()
    return server


class TestIsSystemUrl:
    @pytest.mark.parametrize("url", ["--about", "/--about", " /--about/ ", "--reset"])
    def test_dashed_urls_are_system_urls(self, url):
        assert is_system_url(url)

    @pytest.mark.parametrize("url", ["about", "/about", "index", "", "a/--about"])
    def test_other_urls_are_not(self, url):
        assert not is_system_url(url)

    def test_every_dashed_system_route_is_recognized(self):
        assert DASHED_SYSTEM_ROUTES, "expected dashed system routes to exist"
        assert all(is_system_url(url) for url in DASHED_SYSTEM_ROUTES)


class TestRouterResolution:
    def test_student_route_does_not_answer_for_system_url(self):
        def about():
            return "student"

        router = Router()
        router.add_route("about", about)

        assert router.has_route("about")
        assert not router.has_route("--about")
        assert router.get_route("--about") is None

    @pytest.mark.parametrize("student_first", [True, False])
    def test_student_and_system_routes_coexist(self, student_first):
        def about():
            return "student"

        def system_about():
            return "system"

        router = Router()
        registrations = [("about", about), ("--about", system_about)]
        if not student_first:
            registrations.reverse()
        for url, func in registrations:
            router.add_route(url, func)

        assert router.get_route("about") is about
        assert router.get_route("/about") is about
        assert router.get_route("--about") is system_about
        assert router.get_route("/--about") is system_about

    def test_system_route_does_not_answer_for_bare_name(self):
        def system_about():
            return "system"

        router = Router()
        router.add_route("--about", system_about)

        assert not router.has_route("about")
        assert router.get_route("about") is None

    def test_exact_url_beats_cleaned_name(self):
        """`a/b` and `a_b` share the cleaned name `a_b` but are different URLs."""

        def nested():
            return "nested"

        def flat():
            return "flat"

        router = Router()
        router.add_route("a/b", nested)
        router.add_route("a_b", flat)

        assert router.get_route("a/b") is nested
        assert router.get_route("a_b") is flat

    def test_cleaned_name_fallback_still_finds_custom_urls(self):
        def my_page():
            return "page"

        router = Router()
        router.add_route("/my-page", my_page)

        assert router.has_route("mypage")
        assert router.get_route("mypage") is my_page

    def test_signature_lookup_agrees_with_route_lookup(self):
        """A URL that resolves to a route must also resolve to its signature."""

        def my_page(count: int):
            return count

        router = Router()
        router.add_route("/my-page", my_page)

        request = Request("submit", "mypage", {"count": "3"}, {})
        assert router.get_signature(request).function_name == "my_page"
        _args, kwargs, representation, _provenance = router.prepare_arguments(
            request, None, None, {}
        )
        assert kwargs == {"count": 3}
        assert representation == "my_page(3)"

    def test_unknown_url_has_no_signature(self):
        router = Router()
        with pytest.raises(ValueError, match="No signature found"):
            router.get_signature(Request("click", "missing", {}, {}))

    def test_clear_forgets_cleaned_names(self):
        def my_page():
            return "page"

        router = Router()
        router.add_route("/my-page", my_page)
        router.clear()

        assert not router.has_route("mypage")
        assert not router.has_route("/my-page")


class TestStudentRoutesNamedLikeSystemRoutes:
    """Regression: `@route def about(...)` used to shadow the `--about` page.

    The student route claimed the cleaned name `about`, so the system route
    was never registered; visiting `--about` then found the student function
    but no signature, failing with `request.argument_parsing_failed`.
    """

    @pytest.mark.parametrize("system_url", DASHED_SYSTEM_ROUTES)
    def test_system_route_is_still_registered(self, system_url):
        def student_route():
            return Page(None, ["Student page"])

        server = ClientServer("test_route_resolution")
        server.add_route(bare_name(system_url), student_route)
        server.do_configuration()
        server.do_start()

        assert server.router.get_route(system_url) is _SYSTEM_ROUTES[system_url]
        assert server.router.get_route(bare_name(system_url)) is student_route

    def test_about_and_system_about_are_separate_pages(self):
        def about(state):
            return Page(state, ["My very own about page"])

        server = ClientServer("test_route_resolution")
        server.add_route("about", about)
        server.do_configuration()
        server.do_start()

        system_response = server.do_visit(Request("click", "--about", {}, {}, ""))
        assert system_response.status_code == STATUS_OK
        assert "No site information has been set" in system_response.body
        assert "My very own about page" not in system_response.body

        student_response = server.do_visit(Request("click", "about", {}, {}, ""))
        assert student_response.status_code == STATUS_OK
        assert "My very own about page" in student_response.body

    def test_route_added_after_start_does_not_shadow_system_route(self):
        def about(state):
            return Page(state, ["My very own about page"])

        server = make_started_server()
        server.add_route("about", about)

        system_response = server.do_visit(Request("click", "--about", {}, {}, ""))
        assert system_response.status_code == STATUS_OK
        assert "My very own about page" not in system_response.body

    def test_student_error_route_does_not_render_error_pages(self):
        def error(state):
            return Page(state, ["My very own error page"])

        server = ClientServer("test_route_resolution")
        server.add_route("error", error)
        server.do_configuration()
        server.do_start()

        response = server.do_visit(Request("click", "nonexistent", {}, {}, ""))
        assert response.status_code == STATUS_NOT_FOUND
        assert "My very own error page" not in response.body
